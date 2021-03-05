import datetime
from typing import Dict

from aiothornode.types import ThorPool
from tortoise import fields, exceptions, Model
from tortoise.functions import Max, Count


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


class ThorTx(Model):
    DIVIDER = 100_000_000.0

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

    def increase_fail_count(self):
        self.process_flags -= 1

    def set_processed(self):
        self.process_flags = 1

    @staticmethod
    def _usd_price_and_volume(asset, amount, pools: Dict[str, ThorPool], usd_per_rune: float):
        pool = pools.get(asset, None)
        usd_price = usd_per_rune if asset is None else pool.runes_per_asset * usd_per_rune
        usd_volume = usd_price * amount
        rune_volume = usd_volume / usd_per_rune
        return usd_price, usd_volume, rune_volume

    def fill_volumes(self, pools: Dict[str, ThorPool], usd_per_rune: float):
        self.usd_price1, usd_volume1, rune_volume1 = self._usd_price_and_volume(self.asset1, self.amount1, pools,
                                                                                usd_per_rune)
        self.usd_price2, usd_volume2, rune_volume2 = self._usd_price_and_volume(self.asset2, self.amount2, pools,
                                                                                usd_per_rune)

        if self.type in (ThorTxType.TYPE_SWAP, ThorTxType.TYPE_REFUND):
            # 1. swap, refund: volume = input asset
            self.rune_volume = rune_volume1
            self.usd_volume = usd_volume1
        else:
            # 2. donate, withdraw, addLiquidity = sum of input and output
            self.rune_volume = rune_volume1 + rune_volume2
            self.usd_volume = usd_volume1 + usd_volume2

        # self.set_processed()  # todo!

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
    async def count_without_volume(cls, network_id: str) -> int:
        r = await cls.annotate(n=Count('id')).filter(network=network_id, process_flags__lte=0).values('n')
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
