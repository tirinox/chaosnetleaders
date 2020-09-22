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

    # r = await BEPTransaction.filter(date__gte=START_TIMESTAMP).group_by('input_address')
    # print(r)

    la = LeaderAggregator()

    txs = await BEPTransaction.all()

    for tx in txs:
        await la.add_transaction(tx)

    await la.save_all()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
