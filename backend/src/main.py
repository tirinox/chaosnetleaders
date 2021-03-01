import logging

from aiohttp import web
from dotenv import load_dotenv

from api import handler_leaderboard
# from _old.fetcher import run_fetcher
from helpers.db import DB

PORT = 5000

logging.basicConfig(level=logging.INFO)


async def init_db(*_):
    db = DB()
    await db.start()
    return db


def run_api_server():
    app = web.Application(middlewares=[])
    app.add_routes([web.get('/api/v1/leaderboard', handler_leaderboard)])
    app.on_startup.append(init_db)

    # run bg tasks
    # app.on_startup.append(run_fetcher)

    web.run_app(app, port=PORT)


# async def run_command():
#     await init_db()
#
#     command = sys.argv[1]
#     if command == 'reset-rune-volumes':
#         print('reset-rune-volumes command is executing...')
#         await BEPTransaction.clear_rune_volume()
#     elif command == 'calc-rune-volumes':
#         print('calc-rune-volumes command is executing...')
#         vf = ValueFiller()
#         await vf.run()
#     else:
#         logging.error(f'unknown command {command}\n'
#                       f'available commands are\n'
#                       f'  reset-rune-volumes'
#                       f'  calc-rune-volumes')


if __name__ == '__main__':
    load_dotenv('../../.env')

    run_api_server()

    # import sys
    # if len(sys.argv) >= 2:
    #     asyncio.run(run_command())
    # else:
    #     run_api_server()
