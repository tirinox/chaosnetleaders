import asyncio
import logging
from typing import Optional

import aiohttp
from aiohttp import web, ClientTimeout
from aiothornode.connector import ThorConnector, ThorEnvironment, \
    CHAOS_NET_BNB_ENVIRONMENT, TEST_NET_ENVIRONMENT_MULTI_1
from dotenv import load_dotenv

from api import API
from helpers.db import DB
from jobs.tx.parser import TxParserV1, TxParserV2
from jobs.tx.scanner import MidgardURLGenV1, NetworkIdents, MidgardURLGenV2, TxScanner
from jobs.tx.storage import TxStorage
from jobs.vauefill import ValueFiller


logging.basicConfig(level=logging.INFO)


class App:
    def __init__(self) -> None:
        self.db = DB()
        self.tx_storage = TxStorage()
        self.api = API(self.tx_storage)
        self.api_port = 5000  # todo: config
        self.version = 1
        self.midgard_time_out = 5.0
        self.thor_time_out = 5.0
        self.scanner: Optional[TxScanner] = None
        self.thor_env = TEST_NET_ENVIRONMENT_MULTI_1
        self.thor: Optional[ThorConnector] = None

    async def init_db(self, _):
        await self.db.start()

    async def scanner_job(self):
        version = 1
        start = 0

        url_gen = MidgardURLGenV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN) if version == 1 \
            else MidgardURLGenV2(network_id=NetworkIdents.TESTNET_MULTICHAIN)
        parser = TxParserV1(url_gen.network_id) if version == 1 else TxParserV2(url_gen.network_id)

        timeout = ClientTimeout(total=self.midgard_time_out)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.scanner = TxScanner(url_gen, session, parser, delegate=self.tx_storage)
            await self.scanner.run_scan(start=start)

    async def run_scanner(self, _):
        timeout = ClientTimeout(total=self.thor_time_out)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.thor = ThorConnector(self.thor_env, session)
            asyncio.create_task(self.scanner_job())

    async def fill_job(self):
        ...

    async def run_fill_job(self, _):
        asyncio.create_task(self.fill_job())

    def run_server(self):
        app = web.Application(middlewares=[])

        routes = {
            '/api/v1/leaderboard': self.api.handler_leaderboard,
            '/api/v1/progress': self.api.handler_sync_progress
        }

        for route, handler in routes.items():
            app.add_routes([web.get(route, handler)])

        # run bg tasks
        app.on_startup.append(self.init_db)
        app.on_startup.append(self.run_scanner)
        app.on_startup.append(self.run_fill_job)

        web.run_app(app, port=self.api_port)


if __name__ == '__main__':
    load_dotenv('../../.env')
    App().run_server()

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

# import sys
# if len(sys.argv) >= 2:
#     asyncio.run(run_command())
# else:
#     run_api_server()
