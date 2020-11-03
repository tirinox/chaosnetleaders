from tortoise import fields

from midgard.models.base import IdModel


class BlockPrice(IdModel):
    pool = fields.CharField(32, index=True)
    block_height = fields.IntField(index=True, default=0)
    price = fields.FloatField(default=0.0)

    def __repr__(self):
        return f"BlockPrice(pool={self.pool}, block_height={self.block_height}, price={self.price}"

    def __str__(self) -> str:
        return super().__repr__()

    @classmethod
    async def get(cls, pool, block_height):
        return await cls.filter(pool=pool, block_height=block_height).first()
