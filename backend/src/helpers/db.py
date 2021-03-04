import os

from tortoise import Tortoise


class DB:
    @property
    def connect_url(self):
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        user = os.environ.get('POSTGRES_USER', 'thor')
        password = os.environ['POSTGRES_PASSWORD']
        base = os.environ.get('POSTGRES_DB', 'thorchain')
        port = os.environ.get('POSTGRES_PORT', '54320')
        db_type = 'postgres'

        connect_string = f'{db_type}://{user}:{password}@{host}:{port}/{base}'
        return connect_string

    async def start(self):
        await Tortoise.init(db_url=self.connect_url, modules={
            "models": [
                "models.tx",
            ]
        })
        await Tortoise.generate_schemas()
