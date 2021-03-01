import asyncio
import logging
import time

from dotenv import load_dotenv

from helpers.db import DB
from models.tx import ThorTx, ThorTxType

logging.basicConfig(level=logging.INFO)


async def add_test_tx():
    tx = ThorTx(type=ThorTxType.TYPE_ADD,
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


async def main():
    db = DB()
    await db.start()
    await add_test_tx()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
