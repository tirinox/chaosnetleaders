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

    def __str__(self):
        return f"{self.type} @ {datetime.datetime.fromtimestamp(float(self.date))}(#{self.id}: " \
               f"{self.amount1} {self.asset1} -> {self.amount2} {self.asset2})"

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
    async def get_items_with_no_prices(cls, start=0, limit=10):
        # fixme
        return await cls.filter(output_usd_price_lte=1e-10, input_usd_price_lte=1e-10).limit(limit).offset(start).all()

    @classmethod
    async def last_date(cls):
        try:
            max_date = await cls.annotate(max_date=Max('date')).values('max_date')
            max_date = int(max_date[0]['max_date'])
            return max_date
        except (LookupError, ValueError, TypeError):
            return 0

    @classmethod
    def without_volume(cls):
        return cls.filter(rune_volume=None)

    @classmethod
    async def n_without_volume(cls) -> int:
        r = await cls.annotate(n=Count('id')).filter(rune_volume=None).values('n')
        return int(r[0]['n'])

    @classmethod
    async def random_tx_without_volume(cls):
        n = await cls.n_without_volume()
        if n == 0:
            return None, 0
        i = randint(0, n - 1)
        tx = await cls.without_volume().offset(i).limit(1).first()
        return tx, n

    @property
    def is_double(self):
        return self.type == self.TYPE_DOUBLE_SWAP

    @classmethod
    def all_by_date(cls, asc=True):
        return cls.all().order_by('date' if asc else '-date')

    @classmethod
    async def clear(cls):
        await cls.all().delete()

    @classmethod
    async def clear_rune_volume(cls):
        await cls.all().update(rune_volume=None)

    @classmethod
    async def all_for_address(cls, input_address):
        return await cls.filter(input_address=input_address)
