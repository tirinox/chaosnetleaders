import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List

from aiothornode.connector import ThorConnector, ThorEnvironment, TEST_NET_ENVIRONMENT_MULTI_1, \
    CHAOS_NET_BNB_ENVIRONMENT, ThorPool

from helpers.coins import STABLE_COINS
from helpers.constants import NetworkIdents
from helpers.utils import weighted_mean
from models.tx import ThorTx


def get_thor_env_by_network_id(network_id) -> ThorEnvironment:
    if network_id == NetworkIdents.TESTNET_MULTICHAIN:
        return TEST_NET_ENVIRONMENT_MULTI_1
    elif network_id == NetworkIdents.CHAOSNET_BEP2CHAIN:
        return CHAOS_NET_BNB_ENVIRONMENT
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

    logger = logging.getLogger('ValueFiller')

    @staticmethod
    def calculate_usd_per_rune(pools: List[ThorPool]):
        rates, depths = [], []
        for pool in pools:
            if pool.asset in STABLE_COINS:
                rates.append(pool.assets_per_rune)
                depths.append(pool.balance_rune_int)
        if sum(depths) <= 0.0:
            return None
        return weighted_mean(rates, depths)

    async def _fill_tx_list_from_pool_map(self, tx_list: List[ThorTx], pools: List[ThorPool], block_height):
        pool_map = {pool.asset: pool for pool in pools}

        usd_per_rune = self.calculate_usd_per_rune(pools)
        self.logger.info(f'Block: #{block_height}, rune price: ${usd_per_rune:.4f}')
        #
        # return
        #
        # for tx in tx_list:
        #     if tx.number_of_fails >= self.max_fails_of_tx:
        #         continue
        #
        #     pool = pool_map[tx.none_rune_asset]
        #     if not pool:
        #         tx.increase_fail_count()
        #         self.logger.warning(f'no pool info for tx {tx}!')
        #     else:
        #         tx.fill_volumes(pool, usd_per_rune)
        #
        #     await tx.save()
        #
        #     # fixme: debug
        #     print(f'{tx} => {tx.rune_volume} Rune, {tx.usd_volume} $, ProcessFlags = {tx.process_flags}')

    async def _job_iterate(self):
        tx_batch = await ThorTx.select_not_processed_transactions(self.network_id,
                                                                  start=0,
                                                                  limit=self.batch_size,
                                                                  max_fails=3, new_first=False)

        block_to_tx_map = defaultdict(list)
        for tx in tx_batch:
            block_to_tx_map[tx.block_height].append(tx)

        self.logger.info(f'this batch has {len(tx_batch)} tx to fill; {len(block_to_tx_map)} different blocks')

        for block_height, tx_list in block_to_tx_map.items():
            pool_info = await self.thor_connector.query_pools(block_height)
            pool_info = pool_info or []
            await self._fill_tx_list_from_pool_map(tx_list, pool_info, block_height)

    async def run_job(self):
        while True:
            try:
                await self._job_iterate()
                await asyncio.sleep(self.iteration_delay)
            except:
                self.logger.exception('job iteration failed')
                if not self.error_proof:
                    raise
