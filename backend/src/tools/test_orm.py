import asyncio
import logging
import time

from dotenv import load_dotenv

from helpers.db import DB
from models.tx import ThorTx

logging.basicConfig(level=logging.INFO)


async def add_test_tx():
    tx = ThorTx(type=ThorTx.TYPE_DONATE,
                pool1='BTC.BTC',
                pool2='BNB.BNB',
                date=time.time(),
                input_address='0x3404808182083',
                input_asset='BNB.BNB',
                input_amount=100,
                input_usd_price=123.0,
                output_address='0x434859574',
                output_asset='BTC.BTC',
                output_amount=0.2232,
                output_usd_price=46421.023,
                fee=0.1,
                slip=0.01,
                hash='0xrandomtxhsh24433',
                block_height=43223232
                )
    await tx.save_unique()


async def main():
    db = DB()
    await db.start()
    await add_test_tx()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
