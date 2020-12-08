import asyncio
import logging
import os

from aiohttp import web
from dotenv import load_dotenv
from tortoise import Tortoise

from api import handler_leaderboard
from midgard.value_filler import ValueFiller
from midgard.fetcher import run_fetcher
from midgard.models.transaction import BEPTransaction

PORT = 5000

logging.basicConfig(level=logging.INFO)


async def init_db(*_):
    host = os.environ.get('MYSQL_HOST', 'localhost')
    user = os.environ['MYSQL_USER']
    password = os.environ['MYSQL_PASSWORD']
    base = os.environ['MYSQL_DATABASE']

    await Tortoise.init(db_url=f"mysql://{user}:{password}@{host}/{base}", modules={
        "models": [
            "midgard.models.transaction",
        ]
    })
    await Tortoise.generate_schemas()


def run_api_server():
    app = web.Application(middlewares=[])
    app.add_routes([web.get('/api/v1/leaderboard', handler_leaderboard)])
    app.on_startup.append(init_db)
    app.on_startup.append(run_fetcher)

    web.run_app(app, port=PORT)


async def run_command():
    await init_db()

    command = sys.argv[1]
    if command == 'reset-rune-volumes':
        print('reset-rune-volumes command is executing...')
        await BEPTransaction.clear_rune_volume()
    elif command == 'calc-rune-volumes':
        print('calc-rune-volumes command is executing...')
        vf = ValueFiller()
        await vf.run()
    else:
        logging.error(f'unknown command {command}\n'
                      f'available commands are\n'
                      f'  reset-rune-volumes'
                      f'  calc-rune-volumes')


if __name__ == '__main__':
    load_dotenv('../../.env')

    import sys
    if len(sys.argv) >= 2:
        asyncio.run(run_command())
    else:
        run_api_server()
