import datetime
import random
from typing import Dict, Optional, Iterable

from aiothornode.types import ThorPool
from tortoise import fields, exceptions, Model, BaseDBAsyncClient
from tortoise.functions import Max, Count

from helpers.coins import is_rune
from models.poolcache import ThorPoolModel


class ThorTxType:
    OLD_TYPE_STAKE = 'stake'  # deprecated (only for v1 parsing)

    TYPE_ADD_LIQUIDITY = 'addLiquidity'

    TYPE_SWAP = 'swap'
    OLD_TYPE_DOUBLE_SWAP = 'doubleSwap'  # deprecated (only for v1 parsing)

    TYPE_WITHDRAW = 'withdraw'
    OLD_TYPE_UNSTAKE = 'unstake'  # deprecated (only for v1 parsing)

    OLD_TYPE_ADD = 'add'
    TYPE_DONATE = 'donate'

    TYPE_REFUND = 'refund'
    TYPE_SWITCH = 'switch'


class ThorTx(Model):
    id = fields.BigIntField(pk=True)
    block_height = fields.BigIntField(default=0, null=True)
    hash = fields.CharField(255, unique=True)

    network = fields.CharField(80, default='testnet', index=True)

    type = fields.CharField(20)
    date = fields.BigIntField(index=True)

    user_address = fields.CharField(255, index=True)

    asset1 = fields.CharField(128, index=True, null=True)
    amount1 = fields.FloatField()
    usd_price1 = fields.FloatField(default=0.0)

    asset2 = fields.CharField(128, index=True, null=True)
    amount2 = fields.FloatField()
    usd_price2 = fields.FloatField(default=0.0)

    rune_volume = fields.FloatField(default=None, null=True)
    usd_volume = fields.FloatField(default=None, null=True)

    fee = fields.FloatField(default=0.0)
    slip = fields.FloatField(default=0.0)
    liq_units = fields.FloatField(default=0.0)
    process_flags = fields.IntField(default=0, index=True)

    def __str__(self):
        return f"{self.type}(@{datetime.datetime.fromtimestamp(float(self.date))}, {self.user_address}: " \
               f"{self.amount1} {self.asset1 or 'Rune'} -> {self.amount2} {self.asset2 or 'Rune'})"

    def __repr__(self) -> str:
        return self.__str__()

    @property
    def none_rune_asset(self):
        return self.asset1 if not self.asset2 else self.asset2

    @property
    def number_of_fails(self):
        return 0 if self.process_flags < 0 else abs(self.process_flags)

    async def save_unique(self):
        try:
            old = await self.filter(hash=self.hash)
            if not old:
                await self.save()
                return True
            else:
                return False
        except exceptions.IntegrityError:
            return False

    @classmethod
    async def select_not_processed_transactions(cls, network_id, start=0, limit=10, max_fails=3, new_first=True):
        order = '-block_height' if new_first else 'block_height'
        return await cls.filter(
            network=network_id,
            process_flags__lte=0,
            process_flags__gt=-max_fails).order_by(order).limit(limit).offset(start)

    @classmethod
    async def select_random_unfilled_tx(cls, network_id, max_fails=3):
        n = await cls.count_without_volume(network_id, max_fails)
        random_shift = random.randint(0, n - 1) if n > 0 else 0
        txs = await cls.select_not_processed_transactions(network_id, random_shift, 1, max_fails)
        return txs[0] if txs else None

    def increase_fail_count(self):
        self.process_flags -= 1

    def set_processed(self):
        self.process_flags = 1

    @staticmethod
    def _usd_price_and_volume(asset, amount, pools: Dict[str, ThorPoolModel], usd_per_rune: float):
        if asset is None or is_rune(asset):
            return usd_per_rune, amount * usd_per_rune, amount
        else:
            pool = pools.get(asset, None)
            if not pool or int(pool.balance_rune) == 0 or int(pool.balance_asset) == 0:
                return None, 0.0, 0.0
            usd_price = usd_per_rune if asset is None else pool.runes_per_asset * usd_per_rune
            usd_volume = usd_price * amount
            rune_volume = usd_volume / usd_per_rune
            return usd_price, usd_volume, rune_volume

    def fill_volumes(self, pools: Dict[str, ThorPoolModel], usd_per_rune: float):
        # # fdixme: debug!
        # print(self.type)
        # if self.type == ThorTxType.TYPE_SWITCH:
        #     print('boo!')

        if not usd_per_rune:
            return self.increase_fail_count()

        self.usd_price1, usd_volume1, rune_volume1 = self._usd_price_and_volume(self.asset1, self.amount1, pools,
                                                                                usd_per_rune)
        self.usd_price2, usd_volume2, rune_volume2 = self._usd_price_and_volume(self.asset2, self.amount2, pools,
                                                                                usd_per_rune)

        if self.asset1 and not self.usd_price1:
            return self.increase_fail_count()

        if self.asset2 and not self.usd_price2:
            return self.increase_fail_count()

        if self.type in (ThorTxType.TYPE_SWAP, ThorTxType.TYPE_REFUND, ThorTxType.TYPE_SWITCH):
            # 1. swap, refund, switch: volume = input asset
            self.rune_volume = rune_volume1
            self.usd_volume = usd_volume1
        else:
            # 2. donate, withdraw, addLiquidity = sum of input and output
            self.rune_volume = rune_volume1 + rune_volume2
            self.usd_volume = usd_volume1 + usd_volume2

        self.set_processed()

    async def _pre_save(self, using_db: Optional[BaseDBAsyncClient] = None,
                        update_fields: Optional[Iterable[str]] = None) -> None:
        self.usd_price1 = self.usd_price1 or 0.0
        self.usd_price2 = self.usd_price2 or 0.0
        return await super()._pre_save(using_db, update_fields)

    @classmethod
    async def last_date(cls):
        try:
            max_date = await cls.annotate(max_date=Max('date')).values('max_date')
            max_date = int(max_date[0]['max_date'])
            return max_date
        except (LookupError, ValueError, TypeError):
            return 0

    @classmethod
    def select_by_network(cls, network_id: str):
        return cls.filter(network=network_id)

    @classmethod
    async def count_of_transactions_for_network(cls, network_id: str):
        result = await cls.all().annotate(n=Count("id")).filter(network=network_id).values('n')
        return result[0]['n']

    @classmethod
    async def count_without_volume(cls, network_id: str, max_fails) -> int:
        r = await cls.annotate(n=Count('id')).filter(network=network_id,
                                                     process_flags__lte=0,
                                                     process_flags__gt=-max_fails,
                                                     ).values('n')
        return int(r[0]['n'])

    @classmethod
    def all_by_date(cls, asc=True):
        return cls.all().order_by('date' if asc else '-date')

    @classmethod
    async def clear(cls):
        await cls.all().delete()

    @classmethod
    async def clear_rune_volume(cls, network):
        await cls.filter(network=network).all().update(rune_volume=None, usd_volume=None, process_flags=0)

    @classmethod
    async def all_for_address(cls, user_address):
        return await cls.filter(user_address=user_address)

    @classmethod
    async def total_distinct_users_count(cls, network_id, from_date=0, to_date=0):
        r = await cls \
            .annotate(total_addresses=Count('user_address', distinct=True)) \
            .filter(date__gte=from_date) \
            .filter(date__lte=to_date) \
            .filter(network=network_id) \
            .values('total_addresses')
        return r[0]['total_addresses']
