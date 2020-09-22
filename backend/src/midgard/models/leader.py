from tortoise import fields

from midgard.models.base import IdModel


class BEPLeader(IdModel):
    address = fields.CharField(255, index=True)
    asset = fields.CharField(50, index=True)
    amount = fields.FloatField()
    date = fields.IntField(index=True)
    last_tx_id = fields.IntField(index=True)
    order_of_come = fields.IntField()

    def __str__(self):
        return f"BEPLeader({self.address} has {self.amount} {self.asset})"

