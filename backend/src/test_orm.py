import asyncio
from dotenv import load_dotenv
import os
import logging

from tortoise import Tortoise, fields, run_async
from tortoise.functions import Sum, Count

from midgard.fetcher import fetch_all_absent_transactions
from midgard.models.transaction import BEPTransaction
from midgard.aggregator import LeaderAggregator

START_TIMESTAMP = 1599739200  # 12pm UTC, Thursday 10th September 2020


logging.basicConfig(level=logging.INFO)


async def amain():
    host = 'localhost'
    user = os.environ['MYSQL_USER']
    password = os.environ['MYSQL_PASSWORD']
    base = os.environ['MYSQL_DATABASE']

    await Tortoise.init(db_url=f"mysql://{user}:{password}@{host}/{base}", modules={
        "models": [
            "midgard.models.transaction",
            "midgard.models.leader",
        ]
    })
    await Tortoise.generate_schemas()

    # await fetch_all_absent_transactions()


    # la = LeaderAggregator()
    #
    # txs = await BEPTransaction.all()
    #
    # for tx in txs:
    #     await la.add_transaction(tx)
    #
    # await la.save_all()

    p = await BEPTransaction.get_best_rune_price('BNB.BUSD-BD1', 1600799725)
    p = 1.0 / p
    print(p)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
