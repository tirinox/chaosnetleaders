import asyncio
import json
import logging
import os
from typing import List

import aiohttp
import datetime

from aiothornode.connector import ThorConnector

from helpers.coingecko import CoinGeckoPriceProvider
from helpers.config import Config
from helpers.constants import NetworkIdents
from helpers.datetime import MINUTE
from helpers.db import DB
from jobs.tx.parser import get_parser_by_network_id
from jobs.value_filler import get_thor_env_by_network_id, ValueFiller
from models.poolcache import ThorPoolModel
from models.tx import ThorTx

logging.basicConfig(level=logging.INFO)


def example_tx_gen(name):
    with open(os.path.join('./test/tx_examples', name), 'r') as f:
        return json.load(f)


async def my_test_get_gecko_price(t_early=1598617260):
    async with aiohttp.ClientSession() as session:
        cg = CoinGeckoPriceProvider(session)
        result = await cg.get_historical_rune_price(t_early)
        print(f'Rune price @ {datetime.datetime.fromtimestamp(t_early)} is ${result:0.3f}.')

        cg.session = None  # make sure it won't try to use HTTP again
        result2 = await cg.get_historical_rune_price(t_early)
        print(f'Rune price cached? is ${result2:0.3f}.')
        result55 = await cg.get_historical_rune_price(t_early + 10 * MINUTE)
        assert result55 == result2


def load_early_tx(network_id) -> List[ThorTx]:
    parser = get_parser_by_network_id(network_id)
    result = parser.parse_tx_response(example_tx_gen('v1_first_ever_txs.json'))
    return result.txs


async def my_test_test_early_tx_fill():
    network_id = NetworkIdents.CHAOSNET_BEP2CHAIN
    async with aiohttp.ClientSession() as session:
        thor_env = get_thor_env_by_network_id(network_id)
        thor_env.set_consensus(1, 1)
        thor = ThorConnector(thor_env, session)
        value_filler = ValueFiller(thor, network_id, dry_run=False, concurrent_jobs=2, batch_size=20)

        txs = load_early_tx(network_id)

        await value_filler.run_concurrent_jobs()

        # await value_filler.request_pools_and_cache_them(example_tx.block_height)
        # await value_filler.request_pools_and_cache_them(200060)

        # pool = await ThorPoolModel.find_one(network_id, 200060, 'BNB.BUSD-BD1')
        # print(pool)
        #
        # pools = await ThorPoolModel.find_pools(network_id, 200060)
        # print(len(pools))


async def main():
    Config()
    await DB().start()

    await my_test_test_early_tx_fill()
    # await my_test_get_gecko_price()


if __name__ == "__main__":
    asyncio.run(main())
