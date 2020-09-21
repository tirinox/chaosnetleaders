from tortoise import Tortoise, fields, run_async, Model


class Trasnaction(Model):
    id = fields.IntField(pk=True)
    name = fields.TextField()
    datetime = fields.DatetimeField(null=True)

    def __str__(self):
        return self.name
