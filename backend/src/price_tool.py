import asyncio
import json
import logging

import aiohttp
from dotenv import load_dotenv

from api import COMP_START_TIMESTAMP, COMP_END_TIMESTAMP
from midgard.fetcher import Fetcher, URL_SWAP_GEN, get_more_transactions_periodically
from midgard.models.transaction import BEPTransaction

logging.basicConfig(level=logging.INFO)


class TXCache:
    CACHE_FILE = '../../data/tx_cache.json'

    def __init__(self, tx_handler: callable):
        self.tx_cache = {}
        self.batch = 50
        self.counter = 0
        self.file_name = self.CACHE_FILE
        self.logger = logging.getLogger('TXCache')
        self.tx_handler = tx_handler
        self.load()

    async def try_to_save(self, forced=False):
        self.counter += 1
        if self.counter >= 10 or forced:
            await asyncio.get_event_loop().run_in_executor(None, self.save)
            self.counter = 0

    def save(self):
        with open(self.file_name, 'w') as f:
            json.dump(self.tx_cache, f, indent=4)

    def load(self):
        try:
            with open(self.file_name, 'r') as f:
                self.tx_cache = json.load(f)
                print(f'loaded tx_cache ({len(self.tx_cache)} items)')
        except FileNotFoundError:
            pass

    @staticmethod
    def filter_by_competition(tx: BEPTransaction):
        return COMP_START_TIMESTAMP <= tx.date <= COMP_END_TIMESTAMP

    async def run(self):
        async with aiohttp.ClientSession() as session:
            f = Fetcher(URL_SWAP_GEN, session)
            start = 0
            while True:
                try:
                    txs, total, go_on = await f.get_transaction_list(start, self.batch)
                    if not go_on:
                        self.logger.info("no more tx!")
                        break
                    simple_txs = []
                    for tx in txs:
                        simple_data = self.tx_cache[tx.hash] = tx.simple_json
                        simple_txs.append(simple_data)
                    asyncio.create_task(self.tx_handler(simple_txs))
                    await self.try_to_save()
                    self.logger.info(f'added tx = {len(txs)}; cache size = {len(self.tx_cache)}; total = {total}')
                except Exception:
                    self.logger.exception("run")
                    continue
                start += self.batch

            await self.try_to_save(forced=True)


async def main():
    await get_more_transactions_periodically(full_scan=True)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
