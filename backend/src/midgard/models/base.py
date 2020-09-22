from tortoise import fields, Model


class IdModel(Model):
    id = fields.IntField(pk=True)

    class Meta:
        abstract = True
