import os

from gino import Gino

db = Gino()


class DB:
    @property
    def connect_url(self):
        host = os.environ.get('POSTGRES_HOST', 'localhost')
        user = os.environ.get('POSTGRES_USER', 'thor')
        password = os.environ['POSTGRES_PASSWORD']
        base = os.environ.get('POSTGRES_DB', 'thorchain')
        port = os.environ.get('POSTGRES_PORT', '54320')

        connect_string = f'postgresql://{user}:{password}@{host}:{port}/{base}'
        return connect_string

    async def start(self):
        await db.set_bind(self.connect_url)
        await db.gino.create_all()
