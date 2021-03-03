import asyncio
import logging
import time
import random

import aiohttp
from dotenv import load_dotenv

from helpers.db import DB
from helpers.deps import Dependencies
from jobs.tx.parser import TxParserV1, TxParserV2, TxParseResult
from jobs.tx.scanner import TxScanner, MidgardURLGenV1, MidgardURLGenV2, ITxDelegate, NetworkIdents
from jobs.tx.storage import TxStorage
from models.tx import ThorTx, ThorTxType

logging.basicConfig(level=logging.INFO)


async def add_test_tx():
    tx = ThorTx(
        type=ThorTxType.TYPE_ADD,
        date=time.time(),
        hash='0xrandomtxhsh24433',
        block_height=43223232,
        user_address='0x3404808182083',
        asset1='BNB.BNB',
        amount1=100,
        usd_price1=123.0,
        asset2='BTC.BTC',
        amount2=0.2232,
        usd_price2=46421.023,
        fee=0.1,
        slip=0.01,
    )
    await tx.save_unique()


class TxStorageRandomFail(TxStorage):
    async def on_transactions(self, tx_results: TxParseResult) -> bool:
        if random.uniform(0, 1) > 0.5:
            self.logger.error('simalating error')
            raise ValueError('lol fail!')
        return await super().on_transactions(tx_results)


class TxDelegateDummy(ITxDelegate):
    def __init__(self) -> None:
        self.n = 200

    def on_transactions(self, tx_results: TxParseResult) -> bool:
        self.n -= tx_results.tx_count

        for tx in tx_results.txs:
            tx: ThorTx
            print(tx.hash)

        return self.n > 0


async def my_test_scan(deps, version=1, start=0, full_scan=False):
    url_gen = MidgardURLGenV1(network_id=NetworkIdents.CHAOSNET_BEP2CHAIN) if version == 1 \
        else MidgardURLGenV2(network_id=NetworkIdents.TESTNET_MULTICHAIN)
    parser = TxParserV1(url_gen.network_id) if version == 1 else TxParserV2(url_gen.network_id)
    async with aiohttp.ClientSession() as session:
        # storage = TxStorageRandomFail(deps)
        storage = TxStorage(deps)
        storage.full_scan = full_scan
        scanner = TxScanner(url_gen, session, parser, delegate=storage)
        await scanner.run_scan(start=start)


async def my_test_progress():
    n = await ThorTx.count_of_transactions_for_network(NetworkIdents.TESTNET_MULTICHAIN)
    print(f'TESTNET_MULTICHAIN: {n=}')
    n = await ThorTx.count_of_transactions_for_network(NetworkIdents.CHAOSNET_BEP2CHAIN)
    print(f'CHAOSNET_BEP2CHAIN: {n=}')


async def main():
    deps = Dependencies(db=DB())
    await deps.db.start()
#    await add_test_tx()
    await my_test_scan(deps, version=2, start=0, full_scan=False)
    # await my_test_progress()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
