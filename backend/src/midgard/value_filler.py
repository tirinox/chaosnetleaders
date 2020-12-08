import asyncio
import logging

import aiohttp
import names

from midgard.models.transaction import BEPTransaction
from midgard.pool_price import PoolPriceCache, PoolPriceFetcher
from utils import schedule_task_periodically, progressbar


class ValueFiller:
    FILL_VOLUME_BATCH = 100
    DONT_FILL_RUNE_PRICE_BEFORE = 1598788800  # Sunday, 30-Aug-20 12:00:00 UTC in RFC 2822

    def __init__(self, n_workers=4):
        self.n_workers = n_workers
        self.tx_black_list = {}
        self.pool_price_cache = PoolPriceCache()
        self.total_number = None
        self.processed_number = 0
        self.fetcher = PoolPriceFetcher()

    async def run(self, interval=20, blocking=True):
        _, self.total_number = await BEPTransaction.random_tx_without_volume()

        async with aiohttp.ClientSession() as session:
            self.fetcher.session = session
            await self.fetcher.load_nodes_ip()
            tasks = []
            for i in range(self.n_workers):
                if interval > 0:
                    t = schedule_task_periodically(interval, self._worker)
                else:
                    t = asyncio.create_task(self._worker())
                tasks.append(t)

            if blocking:
                await asyncio.gather(*tasks)

    async def _give_up_tx(self, tx: BEPTransaction, logger):
        logger.warning(f'give up on tx: {tx}')
        tx.rune_volume = 0
        tx.output_usd_price = 0.01
        tx.input_usd_price = 0.01
        await tx.save()

    def _blacklist_tx(self, tx: BEPTransaction):
        if tx is not None:
            n = self.tx_black_list[tx.hash] = self.tx_black_list.get(tx.hash, 0) + 1
            return n

    def _times_blacklisted(self, tx: BEPTransaction):
        if tx is not None:
            return self.tx_black_list.get(tx.hash, 0)
        else:
            return 0

    async def _worker(self):
        name = f"Value Filler Worker {names.get_full_name()}"
        logger = logging.getLogger(name)

        tx = None
        while True:
            try:
                tx, n = await BEPTransaction.random_tx_without_volume()
                if not tx or n == 0:
                    logger.info('no more TX to fill, worker quits.')
                    break

                if tx.date <= self.DONT_FILL_RUNE_PRICE_BEFORE or self._times_blacklisted(tx) >= 3:
                    await self._give_up_tx(tx, logger)
                    continue

                await tx.fill_tx_volume_and_usd_prices(self.pool_price_cache, self.fetcher)
                await tx.save()

                self.processed_number += 1
                logger.info(
                    f'filled usd data for #{tx.id} ({tx.rune_volume:.1f} R). '
                    f'{self.processed_number}/{self.total_number}, '
                    f'{progressbar(self.processed_number, self.total_number, 20)}'
                )
            except Exception:
                logger.exception(f'error, I will sleep for a little while {tx.hash if tx else ""} ({tx})',
                                 exc_info=False)
                self._blacklist_tx(tx)
                await asyncio.sleep(3.0)
