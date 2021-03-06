import asyncio
import logging
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from datetime import datetime
from typing import List

from aiothornode.connector import ThorConnector, ThorEnvironment, TEST_NET_ENVIRONMENT_MULTI_1, \
    CHAOS_NET_BNB_ENVIRONMENT, ThorPool
from tenacity import retry, stop_after_attempt, RetryError

from helpers.coingecko import CoinGeckoPriceProvider
from helpers.coins import STABLE_COINS
from helpers.constants import NetworkIdents
from helpers.utils import weighted_mean
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
    batch_size: int = 1000
    retries: int = 3
    error_proof: bool = False
    iteration_delay: float = 1.0  # sec
    max_fails_of_tx: int = 4
    dry_run: bool = False

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

    async def fill_one_tx(self, tx: ThorTx):
        if not tx:
            self.logger.error('no tx to fill')
            return

        pools = await ThorPoolModel.find_pools(self.network_id, tx.block_height)
        if not pools:
            try:
                pools = await self.request_pools_and_cache_them(tx.block_height)
            except RetryError:
                pass

        if pools:
            usd_per_rune = self.calculate_usd_per_rune(pools)

            if not usd_per_rune:
                cg_price_provider = CoinGeckoPriceProvider(self.thor_connector.session)
                usd_per_rune = await cg_price_provider.get_historical_rune_price(tx.date)

            if not usd_per_rune:
                self.logger.error(f'no rune price for block #{tx.block_height}')
                tx.increase_fail_count()
            else:
                pool_map = {pool.pool: pool for pool in pools}
                tx.fill_volumes(pool_map, usd_per_rune)
        else:
            self.logger.error(f'no pools were loaded for block #{tx.block_height}')
            tx.increase_fail_count()

        if not self.dry_run:
            await tx.save()

    async def get_unfilled_tx_batch(self):
        tx_batch = await ThorTx.select_not_processed_transactions(self.network_id,
                                                                  start=0,
                                                                  limit=self.batch_size,
                                                                  max_fails=3, new_first=False)
        return tx_batch

    async def process_tx_batch(self, tx_batch: List[ThorTx]):
        block_to_tx_map = defaultdict(list)
        min_ts, max_ts = datetime.now().timestamp(), 0
        for tx in tx_batch:
            min_ts = min(min_ts, tx.date)
            max_ts = max(max_ts, tx.date)
            block_to_tx_map[tx.block_height].append(tx)

        self.logger.info(f'This batch has {len(tx_batch)} tx to fill; '
                         f'from {datetime.fromtimestamp(min_ts)} to {datetime.fromtimestamp(max_ts)}; '
                         f'{len(block_to_tx_map)} different blocks.')

    @retry(stop=stop_after_attempt(3))
    async def request_pools_and_cache_them(self, block_height):
        pool_info = await self.thor_connector.query_pools(block_height)
        results = []
        for pool in pool_info:
            pool_model = ThorPoolModel.from_thor_pool(pool, self.network_id, block_height)
            await pool_model.save()
            results.append(pool_model)
        return results

    async def run_job(self):
        while True:
            try:
                txs = await self.get_unfilled_tx_batch()
                await self.process_tx_batch(txs)
                await asyncio.sleep(self.iteration_delay)
            except:
                self.logger.exception('job iteration failed')
                if not self.error_proof:
                    raise
