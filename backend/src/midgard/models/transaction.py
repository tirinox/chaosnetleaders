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

    block_height = fields.IntField(default=0, null=True)
    input_usd_price = fields.FloatField(default=0.0)
    output_usd_price = fields.FloatField(default=0.0)

    hash = fields.CharField(255, unique=True)

    def __str__(self):
        return f"{self.type} @ {datetime.datetime.fromtimestamp(self.date)}(#{self.id}: {self.input_amount} {self.input_asset} -> {self.output_amount} {self.output_asset})"

    def __repr__(self) -> str:
        return super().__str__()

    @property
    def simple_json(self):
        return {
            'in': {
                'coin': self.input_asset,
                'amount': self.input_amount,
                'usd': self.input_usd_price
            },
            'out': {
                'coin': self.output_asset,
                'amount': self.output_amount,
                'usd': self.output_usd_price
            },
            'address:': self.input_address,
            'height': self.block_height,
            'date': self.date,
            'pool': self.pool,
            'type': self.type,
        }

    @property
    def other_asset(self):
        return self.input_asset if self.output_address == self.RUNE_SYMBOL else self.output_address

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
                               order_of_come=order_of_come,
                               block_height=int(tx['height']),
                               input_usd_price=0.0,
                               output_usd_price=0.0
                               )
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
            return False

    def _get_price_rune(self):
        if self.input_asset == self.RUNE_SYMBOL:
            return self.input_amount / self.output_amount
        elif self.output_asset == self.RUNE_SYMBOL:
            return self.output_amount / self.input_amount

    @classmethod
    async def get_best_rune_price(cls, pool, date):
        # forwards
        # transaction1 = await cls.filter(date__gte=date, pool=pool, type=cls.TYPE_SWAP).order_by("date").first()

        transaction_before = await cls.filter(date__lte=date, pool=pool, type=cls.TYPE_SWAP).order_by("-date").first()

        if transaction_before:
            price = transaction_before._get_price_rune()
            return price, transaction_before.date
        else:
            return None, None

    async def calculate_rune_volume(self):
        if self.type == self.TYPE_SWAP:
            # simple
            return self.input_amount if self.input_asset == self.RUNE_SYMBOL else self.output_amount
        else:
            # double
            input_price, input_date = await self.get_best_rune_price(self.input_asset, self.date)
            output_price, output_date = await self.get_best_rune_price(self.output_asset, self.date)

            # print(f'{self.input_asset}: input_price = {input_price}, date = {input_date}')
            # print(f'{self.output_asset}: output_price = {output_price}, date = {output_date}')

            if input_price and output_price:
                input_later = input_date > output_date
                price = input_price if input_later else output_price
                amount = self.input_amount if input_later else self.output_amount
            elif input_price:
                price = input_price
                amount = self.input_amount
            elif output_price:
                price = output_price
                amount = self.output_amount
            else:
                return None
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
    def without_volume(cls):
        return cls.filter(rune_volume=None)

    @property
    def is_double(self):
        return self.type == self.TYPE_DOUBLE_SWAP

    async def fill_rune_volume(self):
        volume = await self.calculate_rune_volume()
        if volume:
            self.rune_volume = volume
        else:
            logging.warning(f"failed to calc rune volume for {self}; no data")
            self.rune_volume = 0
        await self.save()

    @classmethod
    async def clear(cls):
        await cls.all().delete()

    @classmethod
    async def clear_rune_volume(cls):
        await BEPTransaction.all().update(rune_volume=None)

    @classmethod
    async def all_for_address(cls, input_address):
        return await cls.filter(input_address=input_address)
