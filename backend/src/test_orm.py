import asyncio
import logging
import os

from dotenv import load_dotenv
from tortoise import Tortoise

from midgard.aggregator import total_volume, leaderboard
from midgard.fetcher import run_fetcher, get_more_transactions_periodically
from midgard.models.transaction import BEPTransaction

logging.basicConfig(level=logging.INFO)


async def amain():
    host = 'localhost'
    user = os.environ['MYSQL_USER']
    password = os.environ['MYSQL_PASSWORD']
    base = os.environ['MYSQL_DATABASE']

    await Tortoise.init(db_url=f"mysql://{user}:{password}@{host}/{base}", modules={
        "models": [
            "midgard.models.transaction",
        ]
    })
    await Tortoise.generate_schemas()

    await get_more_transactions_periodically()
    # await fill_rune_volumes()

    # await BEPTransaction.clear_rune_volume()
    #
    # lb = await leaderboard(from_date=1600959386)
    # print(lb)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
