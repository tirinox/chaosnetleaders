import asyncio
import json
import os
from typing import List

import aiohttp
import datetime

from aiothornode.connector import ThorConnector

from helpers.coingecko import CoinGeckoPriceProvider
from helpers.constants import NetworkIdents
from helpers.datetime import MINUTE
from jobs.tx.parser import get_parser_by_network_id
from jobs.vauefill import get_thor_env_by_network_id, ValueFiller
from models.tx import ThorTx


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
        value_filler = ValueFiller(thor, network_id, 5, 3)

        txs = load_early_tx(network_id)
        example_tx = txs[3]

        print(f'Example tx = {example_tx}')
        pools = await thor.query_pools(example_tx.block_height)
        print(pools)

        rune_price = value_filler.calculate_usd_per_rune(pools)
        print(f'{rune_price=}')
        cg = CoinGeckoPriceProvider(session)
        if rune_price is None:
            print('No usd pool at that moment, requesting gecko')
            rune_price = await cg.get_historical_rune_price(example_tx.date)

        print(f'{rune_price=}')




async def main():
    await my_test_test_early_tx_fill()
    # await my_test_get_gecko_price()


if __name__ == "__main__":
    asyncio.run(main())
