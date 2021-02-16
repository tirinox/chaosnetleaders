import os
import time

from tortoise import Tortoise

from models.tx import ThorTx


class DB:
    @property
    def connect_url(self):
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        user = os.environ.get('POSTGRES_USER', 'thor')
        password = os.environ['POSTGRES_PASSWORD']
        base = os.environ.get('POSTGRES_DB', 'thorchain')
        port = os.environ.get('POSTGRES_PORT', '54320')

        connect_string = f'postgres://{user}:{password}@{host}:{port}/{base}'
        return connect_string

    async def start(self):
        await Tortoise.init(db_url=self.connect_url, modules={
            "models": [
                "models.tx",
            ]
        })
        await Tortoise.generate_schemas()
