import asyncio
import datetime
import logging
import time
from copy import copy
from dataclasses import dataclass
from typing import List

import names
import tqdm
from aiothornode.connector import ThorConnector, ThorEnvironment, TEST_NET_ENVIRONMENT_MULTI_1, \
    CHAOS_NET_BNB_ENVIRONMENT
from tenacity import retry, stop_after_attempt, RetryError

from helpers.coingecko import CoinGeckoPriceProvider
from helpers.coins import STABLE_COINS
from helpers.constants import NetworkIdents
from helpers.utils import weighted_mean, progressbar
from models.poolcache import ThorPoolModel
from models.tx import ThorTx


def get_thor_env_by_network_id(network_id) -> ThorEnvironment:
    if network_id == NetworkIdents.TESTNET_MULTICHAIN:
        return copy(TEST_NET_ENVIRONMENT_MULTI_1)
    elif network_id == NetworkIdents.CHAOSNET_BEP2CHAIN:
        return copy(CHAOS_NET_BNB_ENVIRONMENT)
    else:
        # todo: add multi-chain chaosnet
        raise KeyError('unsupported network ID!')


@dataclass
class ValueFiller:
    thor_connector: ThorConnector
    network_id: str
    retries: int = 3
    error_proof: bool = False
    iteration_delay: float = 1.0  # sec
    max_fails_of_tx: int = 4
    dry_run: bool = False
    concurrent_jobs: int = 4
    _progress_counter: int = 0
    progress_every_n_iter: int = 50
    _last_time: float = 0.0

    logger = logging.getLogger('ValueFiller')

    @staticmethod
    def calculate_usd_per_rune(pools: List[ThorPoolModel]):
        rates, depths = [], []
        for pool in pools:
            if pool.pool in STABLE_COINS:
                rates.append(pool.assets_per_rune)
                depths.append(int(pool.balance_rune))
        if sum(depths) <= 0.0:
            return None
        return weighted_mean(rates, depths)

    async def fill_one_tx(self, tx: ThorTx, name):
        pools = await ThorPoolModel.find_pools(self.network_id, tx.block_height)
        if not pools:
            try:
                pools = await self.request_pools_and_cache_them(tx.block_height)
            except RetryError:
                pass

        if pools:
            try:
                usd_per_rune = self.calculate_usd_per_rune(pools)
                if not usd_per_rune:
                    cg_price_provider = CoinGeckoPriceProvider(self.thor_connector.session)
                    usd_per_rune = await cg_price_provider.get_historical_rune_price(tx.date)
            except:
                self.logger.exception(f'"{name}" usd/rune price error')
                usd_per_rune = None

            if not usd_per_rune:
                self.logger.error(f'"{name}" no rune price for block #{tx.block_height}')
                tx.increase_fail_count()
            else:
                pool_map = {pool.pool: pool for pool in pools}
                tx.fill_volumes(pool_map, usd_per_rune)
        else:
            self.logger.error(f'"{name}" no pools were loaded for block #{tx.block_height}')
            tx.increase_fail_count()

        if not self.dry_run:
            await tx.save()

    @retry(stop=stop_after_attempt(3))
    async def request_pools_and_cache_them(self, block_height):
        pool_info = await self.thor_connector.query_pools(block_height)
        results = []
        for pool in pool_info:
            pool_model = ThorPoolModel.from_thor_pool(pool, self.network_id, block_height)
            await pool_model.save()
            results.append(pool_model)
        return results

    async def get_unfilled_tx_batch(self, n):
        tx_batch = await ThorTx.select_not_processed_transactions(self.network_id,
                                                                  start=0,
                                                                  limit=n,
                                                                  max_fails=self.max_fails_of_tx,
                                                                  new_first=False)
        return tx_batch

    async def get_one_unfilled(self, shift=0):
        tx_batch = await ThorTx.select_not_processed_transactions(self.network_id,
                                                                  start=shift,
                                                                  limit=1,
                                                                  max_fails=self.max_fails_of_tx,
                                                                  new_first=False)
        return tx_batch[0] if tx_batch else None

    async def run_one_job(self, txs: List[ThorTx]):
        name = names.get_full_name()
        self.logger.info(f'Job "{name}" has got {len(txs)} to fill.')
        for i, tx in enumerate(txs, start=1):
            await self.fill_one_tx(tx, name)
            self.logger.info(f'Job "{name}" progress: {i}/{len(txs)}.')

    async def print_progress(self):
        self._progress_counter += 1
        if self._progress_counter >= self.progress_every_n_iter:
            self._progress_counter = 0

            n_done, total, percent = await self.get_progress()

            dt = time.monotonic() - self._last_time
            time_per_tx = dt / self.progress_every_n_iter
            time_estimation = time_per_tx * (total - n_done)
            tdelta = datetime.timedelta(seconds=time_estimation)

            pb = progressbar(n_done, total, symbol_width=30)

            self.logger.info(f'{pb}: {n_done} / {total} ({percent:.3f}%) {tdelta}')
            self._last_time = time.monotonic()

    async def run_job(self, shift=0):
        name = names.get_full_name()
        self.logger.info(f'"{name}" job started with shift = {shift}.')
        while True:
            try:
                tx = await self.get_one_unfilled(shift)
                if tx:
                    await self.fill_one_tx(tx, name)
                else:
                    await asyncio.sleep(1.0)
                await self.print_progress()
            except Exception:
                self.logger.exception(f'"{name}" job iteration failed.')

    async def run_concurrent_jobs(self):
        jobs = [self.run_job(shift) for shift in range(self.concurrent_jobs)]
        await asyncio.gather(*jobs)

    async def get_progress(self):
        total = await ThorTx.count_of_transactions_for_network(self.network_id)
        n_to_go = await ThorTx.count_without_volume(self.network_id, self.max_fails_of_tx)

        total = max(1, total)
        n_done = total - n_to_go
        percent = 100 * n_done / total
        return n_done, total, percent

