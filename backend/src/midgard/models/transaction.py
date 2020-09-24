import logging
import datetime

from tortoise import fields, exceptions
from tortoise.functions import Max

from midgard.models.base import IdModel


class BEPTransaction(IdModel):
    RUNE_SYMBOL = 'BNB.RUNE-B1A'
    DIVIDER = 100_000_000.0

    TYPE_SWAP = 'swap'
    TYPE_DOUBLE_SWAP = 'doubleSwap'

    type = fields.CharField(20)
    date = fields.IntField(index=True)
    pool = fields.CharField(50, index=True)

    input_address = fields.CharField(255, index=True)
    input_asset = fields.CharField(50, index=True)
    input_amount = fields.FloatField()
    output_address = fields.CharField(255, index=True)
    output_asset = fields.CharField(50, index=True)
    output_amount = fields.FloatField()
    order_of_come = fields.IntField()
    rune_volume = fields.FloatField(default=None, null=True)

    hash = fields.CharField(255, unique=True)

    def __str__(self):
        return f"{self.type} @ {datetime.datetime.fromtimestamp(self.date)}(#{self.id}: {self.input_amount} {self.input_asset} -> {self.output_amount} {self.output_asset})"

    @classmethod
    def from_json(cls, tx, order_of_come=0):
        try:
            t = tx['type']
            s = tx['status']
            if s == 'Success':
                if t in (cls.TYPE_DOUBLE_SWAP, cls.TYPE_SWAP):
                    in_data, out_data = tx['in'], tx['out'][0]

                    in_coin = in_data['coins'][0]
                    out_coin = out_data['coins'][0]
                    in_amount = int(in_coin['amount']) / cls.DIVIDER
                    out_amount = int(out_coin['amount']) / cls.DIVIDER

                    tx_hash = f"{in_data['txID']}_{out_data['txID']}"

                    return cls(type=t,
                               date=int(tx['date']),
                               pool=tx['pool'],
                               input_address=in_data['address'],
                               input_asset=in_coin['asset'],
                               input_amount=in_amount,
                               output_address=out_data['address'],
                               output_asset=out_coin['asset'],
                               output_amount=out_amount,
                               hash=tx_hash,
                               order_of_come=order_of_come)
        except (LookupError, ValueError) as e:
            logging.error(f"failed to parse transaction JSON; exeption: {e}")
            return None

    async def save_unique(self):
        try:
            old = await self.filter(hash=self.hash)
            if not old:
                await self.save()
                return True
            else:
                return False
        except exceptions.IntegrityError as e:
            print(e)
            return False

    def get_price_rune(self):
        if self.input_asset == self.RUNE_SYMBOL:
            return self.input_amount / self.output_amount
        elif self.output_asset == self.RUNE_SYMBOL:
            return self.output_amount / self.input_amount

    @classmethod
    async def get_best_rune_price(cls, pool, date):
        transaction1 = await cls.filter(date__gte=date, pool=pool, type=cls.TYPE_SWAP).order_by("date").first()
        transaction2 = await cls.filter(date__lte=date, pool=pool, type=cls.TYPE_SWAP).order_by("-date").first()

        prices = [tx.get_price_rune() for tx in (transaction1, transaction2) if tx is not None]
        if prices:
            avg_price = sum(prices) / len(prices)
            return avg_price

    async def calculate_rune_volume(self):
        if self.type == self.TYPE_SWAP:
            # simple
            return self.input_amount if self.input_asset == self.RUNE_SYMBOL else self.output_amount
        else:
            # double
            price = await self.get_best_rune_price(self.input_asset, self.date)
            amount = self.input_amount
            if price is None:
                price = await self.get_best_rune_price(self.output_asset, self.date)
                amount = self.output_amount

            if price is not None:
                return amount * price

    @classmethod
    async def last_date(cls):
        try:
            max_date = await cls.annotate(max_date=Max('date')).values('max_date')
            max_date = int(max_date[0]['max_date'])
            return max_date
        except (LookupError, ValueError, TypeError):
            return 0

    @classmethod
    def filter_from_date(cls, min_date):
        # todo: filter by last TX hash if the dates are same!
        return cls.filter(date__gt=min_date).order_by('date')

    @classmethod
    def without_volume(cls):
        return cls.filter(rune_volume=None)

    async def fill_rune_volume(self):
        volume = await self.calculate_rune_volume()
        if volume:
            self.rune_volume = volume
            await self.save()

    @classmethod
    async def clear(cls):
        await cls.all().delete()
