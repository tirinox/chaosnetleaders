import datetime
from random import randint

from tortoise import fields, exceptions, Model
from tortoise.functions import Max, Count


class ThorTxType:
    TYPE_STAKE = 'stake'  # deprecated (only for v1 parsing)
    TYPE_ADD = 'add'
    TYPE_ADD_LIQUIDITY = 'addLiquidity'

    TYPE_SWAP = 'swap'
    TYPE_DOUBLE_SWAP = 'doubleSwap'  # deprecated (only for v1 parsing)

    TYPE_WITHDRAW = 'withdraw'
    TYPE_UNSTAKE = 'unstake'  # deprecated (only for v1 parsing)

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
    async def select_not_processed_transactions(cls, network_id, start=0, limit=10):
        return await cls.filter(network=network_id, process_flags__lte=0) \
            .order_by('-block_height') \
            .limit(limit).offset(start)

    def increase_fail_count(self):
        self.process_flags -= 1

    def set_processed(self):
        self.process_flags = 1

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
