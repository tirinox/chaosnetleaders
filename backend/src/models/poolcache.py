from aiothornode.types import ThorPool
from tortoise import fields, Model


class ThorPoolModel(Model):
    id = fields.BigIntField(pk=True)
    block_height = fields.BigIntField(index=True)
    network = fields.CharField(80, default='testnet', index=True)
    pool = fields.CharField(128, index=True)

    balance_asset = fields.DecimalField(30, 0)
    balance_rune = fields.DecimalField(30, 0)
    pool_units = fields.DecimalField(30, 0)
    status = fields.CharField(32, index=True)

    def __str__(self) -> str:
        return f'ThorPoolModel(#{self.block_height}, ' \
               f'{int(self.balance_asset) / 1e8} {self.pool} vs {int(self.balance_rune) / 1e8} R, ' \
               f'{self.status})'

    @classmethod
    def from_thor_pool(cls, p: ThorPool, network_id, block_height):
        return ThorPoolModel(
            block_height=block_height,
            network=network_id,
            pool=p.asset,
            balance_asset=p.balance_asset_int,
            balance_rune=p.balance_rune_int,
            pool_units=p.pool_units_int,
            status=p.status
        )

    @classmethod
    async def find_one(cls, network_id: str, block_height: int, pool: str):
        return await cls.filter(network=network_id, block_height=block_height, pool=pool).first()

    @classmethod
    async def find_pools(cls, network_id: str, block_height: int):
        return await cls.filter(network=network_id, block_height=block_height)

    @property
    def assets_per_rune(self):
        return int(self.balance_asset) / int(self.balance_rune)

    @property
    def runes_per_asset(self):
        return int(self.balance_rune) / int(self.balance_asset)
