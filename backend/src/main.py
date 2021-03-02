import logging

from aiohttp import web
from dotenv import load_dotenv

from api import handler_leaderboard
# from _old.fetcher import run_fetcher
from helpers.db import DB
from helpers.deps import Dependencies

PORT = 5000

logging.basicConfig(level=logging.INFO)


async def init_db(app):
    deps = app['deps']
    await deps.db.start()


def run_api_server(deps):
    app = web.Application(middlewares=[])
    app.add_routes([web.get('/api/v1/leaderboard', handler_leaderboard)])
    app.on_startup.append(init_db)
    app['deps'] = deps

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

    deps = Dependencies(db=DB())

    run_api_server(deps)

    # import sys
    # if len(sys.argv) >= 2:
    #     asyncio.run(run_command())
    # else:
    #     run_api_server()
