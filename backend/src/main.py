import asyncio
import logging

import aiohttp
from aiohttp import web, ClientTimeout
from dotenv import load_dotenv

from api import API
# from _old.fetcher import run_fetcher
from helpers.db import DB
from helpers.deps import Dependencies
from jobs.tx.parser import TxParserV1, TxParserV2
from jobs.tx.scanner import MidgardURLGenV1, NetworkIdents, MidgardURLGenV2, TxScanner
from jobs.tx.storage import TxStorage

PORT = 5000

logging.basicConfig(level=logging.INFO)


async def init_db(app):
    deps = app['deps']
    await deps.db.start()


async def scanner_job(deps: Dependencies):
    version = 1
    timeout = 5.0
    start = 0

    deps.tx_storage = TxStorage(deps)
    url_gen = MidgardURLGenV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN) if version == 1 \
        else MidgardURLGenV2(network_id=NetworkIdents.TESTNET_MULTICHAIN)
    parser = TxParserV1(url_gen.network_id) if version == 1 else TxParserV2(url_gen.network_id)

    timeout = ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        deps.scanner = TxScanner(url_gen, session, parser, delegate=deps.tx_storage)
        await deps.scanner.run_scan(start=start)


async def run_scanner(app):
    deps: Dependencies = app['deps']
    asyncio.create_task(scanner_job(deps))


def run_api_server(deps: Dependencies):
    deps.api = API(deps)
    app = web.Application(middlewares=[])
    app.add_routes([web.get('/api/v1/leaderboard', deps.api.handler_leaderboard)])
    app.add_routes([web.get('/api/v1/progress', deps.api.handler_sync_progress)])
    app.on_startup.append(init_db)
    app['deps'] = deps

    # run bg tasks
    app.on_startup.append(run_scanner)

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
