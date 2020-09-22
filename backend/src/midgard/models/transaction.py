import logging

from tortoise import fields, exceptions

from midgard.models.base import IdModel


class BEPTransaction(IdModel):
    DIVIDER = 100_000.0

    type = fields.CharField(20)
    date = fields.IntField(index=True)
    pool = fields.CharField(50, index=True)

    input_address = fields.CharField(255, index=True)
    input_asset = fields.CharField(50, index=True)
    input_amount = fields.FloatField()
    output_address = fields.CharField(255, index=True)
    output_asset = fields.CharField(50, index=True)
    output_amount = fields.FloatField()

    hash = fields.CharField(255, unique=True)

    def __str__(self):
        return f"{self.type}({self.input_amount} {self.input_asset} -> {self.output_amount} {self.output_asset})"

    @classmethod
    def from_json(cls, tx):
        try:
            t = tx['type']
            s = tx['status']
            if s == 'Success':
                if t in ('swap', 'doubleSwap'):
                    in_data, out_data = tx['in'], tx['out'][0]

                    in_coin = in_data['coins'][0]
                    out_coin = out_data['coins'][0]
                    in_amount = int(in_coin['amount']) / cls.DIVIDER
                    out_amount = int(out_coin['amount']) / cls.DIVIDER

                    tx_hash = f"{in_data['txID']}_{out_data['txID']}"

                    return cls(type="swap",
                               date=int(tx['date']),
                               pool=tx['pool'],
                               input_address=in_data['address'],
                               input_asset=in_coin['asset'],
                               input_amount=in_amount,
                               output_address=out_data['address'],
                               output_asset=out_coin['asset'],
                               output_amount=out_amount,
                               hash=tx_hash)
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
