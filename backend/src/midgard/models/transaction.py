import datetime
import logging
from hashlib import sha256
from random import randint

from tortoise import fields, exceptions
from tortoise.functions import Max, Count

from midgard.models.base import IdModel
from midgard.pool_price import PoolPriceCache


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
    input_usd_price = fields.FloatField(default=0.0)

    output_address = fields.CharField(255, index=True)
    output_asset = fields.CharField(50, index=True)
    output_amount = fields.FloatField()
    output_usd_price = fields.FloatField(default=0.0)

    rune_volume = fields.FloatField(default=None, null=True)
    block_height = fields.IntField(default=0, null=True)

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
    def from_json(cls, tx):
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

                    hasher = sha256()
                    hasher.update(in_data['txID'].encode('ascii'))
                    hasher.update(out_data['txID'].encode('ascii'))
                    tx_hash = hasher.hexdigest()

                    return cls(type=t,
                               date=int(tx['date']),
                               pool=tx['pool'],
                               input_address=in_data['address'],
                               input_asset=in_coin['asset'],
                               input_amount=in_amount,
                               input_usd_price=-1.0,
                               output_address=out_data['address'],
                               output_asset=out_coin['asset'],
                               output_amount=out_amount,
                               output_usd_price=-1.0,
                               hash=tx_hash,
                               block_height=int(tx['height']))
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
        except exceptions.IntegrityError:
            return False

    def _get_price_rune(self):
        if self.input_asset == self.RUNE_SYMBOL:
            return self.input_amount / self.output_amount
        elif self.output_asset == self.RUNE_SYMBOL:
            return self.output_amount / self.input_amount

    @classmethod
    async def get_items_with_no_prices(cls, start=0, limit=10):
        return await cls.filter(output_usd_price_lte=1e-10, input_usd_price_lte=1e-10).limit(limit).offset(start).all()

    @classmethod
    async def get_best_rune_price(cls, pool, date):
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

    @classmethod
    async def n_without_volume(cls) -> int:
        r = await cls.annotate(n=Count('id')).filter(rune_volume=None).values('n')
        return int(r[0]['n'])

    @classmethod
    async def random_tx_without_volume(cls):
        n = await cls.n_without_volume()
        if n == 0:
            return None
        i = randint(0, n - 1)
        tx = await cls.without_volume().offset(i).limit(1).first()
        return tx

    @property
    def is_double(self):
        return self.type == self.TYPE_DOUBLE_SWAP

    async def fill_tx_volume_and_usd_prices(self, ppc: 'PoolPriceCache'):
        _, self.output_usd_price = await ppc.get_historical_price(self.output_asset, self.block_height)
        dollar_per_rune, self.input_usd_price = await ppc.get_historical_price(self.input_asset, self.block_height)
        volume = self.input_amount * self.input_usd_price / dollar_per_rune
        self.rune_volume = volume
        return self

    @classmethod
    async def clear(cls):
        await cls.all().delete()

    @classmethod
    async def clear_rune_volume(cls):
        await BEPTransaction.all().update(rune_volume=None)

    @classmethod
    async def all_for_address(cls, input_address):
        return await cls.filter(input_address=input_address)
