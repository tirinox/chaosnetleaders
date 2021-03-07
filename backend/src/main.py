import asyncio
import logging
from typing import Optional

import aiohttp
from aiohttp import web, ClientTimeout
from aiothornode.connector import ThorConnector

from api import API
from helpers.config import Config
from helpers.datetime import parse_timespan_to_seconds
from helpers.db import DB
from helpers.utils import schedule_task_periodically
from jobs.tx.parser import get_parser_by_network_id
from jobs.tx.scanner import NetworkIdents, TxScanner, get_url_gen_by_network_id
from jobs.tx.storage import TxStorage
from jobs.vauefill import ValueFiller, get_thor_env_by_network_id

logging.basicConfig(level=logging.INFO)


class App:
    def __init__(self) -> None:
        self.cfg = Config()
        self.db = DB()
        self.tx_storage = TxStorage()

        self.network_id = self.cfg.as_str('thorchain.network_id', NetworkIdents.TESTNET_MULTICHAIN)
        logging.info(f'Starting Chaosnetleaders backend for network {self.network_id!r}')

        self.scanner: Optional[TxScanner] = None
        self.thor: Optional[ThorConnector] = None
        self.value_filler: Optional[ValueFiller] = None

    async def init_db(self, _):
        await self.db.start()

    async def scanner_job(self, retries, batch_size, sleep_before_retry):
        url_gen = get_url_gen_by_network_id(self.network_id)
        parser = get_parser_by_network_id(self.network_id)
        midgard_time_out = self.cfg.as_float('thorchain.midgard.timeout', 7.1)
        timeout = ClientTimeout(total=midgard_time_out)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            self.scanner = TxScanner(url_gen, session, parser, delegate=self.tx_storage,
                                     retries=retries, sleep_before_retry=sleep_before_retry)
            await self.scanner.run_scan(start=0, batch_size=batch_size)

    async def run_scanner(self, _):
        cfg = self.cfg.get('thorchain.scanner.tx')
        period = parse_timespan_to_seconds(cfg.as_str('period', '66s'))
        assert period >= 0.0
        retries = cfg.as_int('retries', 5)
        batch_size = cfg.as_int('batch', 49)
        overscan = self.tx_storage.overscan_pages = cfg.as_int('over_scan_pages', 9)
        delay = parse_timespan_to_seconds(cfg.as_str('start_delay', '2s'))
        sleep_before_retry = parse_timespan_to_seconds(cfg.as_str('sleep_before_retry', '2s'))
        logging.info(f'starting scanner with {period=} sec, {retries=}, {batch_size=}, {delay=} sec, {overscan=} pages')
        schedule_task_periodically(period, self.scanner_job, delay, retries, batch_size, sleep_before_retry)

    async def fill_job(self):
        cfg = self.cfg.get('thorchain')
        thor_time_out = cfg.as_float('thornode.timeout', 4.2)
        timeout = ClientTimeout(total=thor_time_out)
        retires = cfg.as_int('value_filler.retries', 3)
        batch = cfg.as_int('value_filler.batch', 100)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            thor_env = get_thor_env_by_network_id(self.network_id)
            thor_env.consensus_min = 1
            thor_env.consensus_total = 1
            self.thor = ThorConnector(thor_env, session)
            self.value_filler = ValueFiller(self.thor, self.network_id, batch, retires)
            await self.value_filler.run_concurrent_jobs()

    async def run_fill_job(self, _):
        asyncio.create_task(self.fill_job())

    def run_server(self):
        app = web.Application(middlewares=[])

        api = API(self.tx_storage)

        routes = {
            '/api/v1/leaderboard': api.handler_leaderboard,
            '/api/v1/progress': api.handler_sync_progress
        }

        for route, handler in routes.items():
            app.add_routes([web.get(route, handler)])

        # run bg tasks
        app.on_startup.append(self.init_db)
        app.on_startup.append(self.run_scanner)  # fixme: uncomment
        app.on_startup.append(self.run_fill_job)

        api_port = int(self.cfg.get('api.port', 5000))
        web.run_app(app, port=api_port)


if __name__ == '__main__':
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
