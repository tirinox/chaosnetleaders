import asyncio
from dotenv import load_dotenv
import os
import logging

from tortoise import Tortoise, fields, run_async
from tortoise.functions import Sum, Count

from midgard.fetcher import foo_test
from midgard.models.transaction import BEPTransaction


logging.basicConfig(level=logging.INFO)


async def amain():
    host = 'localhost'
    user = os.environ['MYSQL_USER']
    password = os.environ['MYSQL_PASSWORD']
    base = os.environ['MYSQL_DATABASE']

    await Tortoise.init(db_url=f"mysql://{user}:{password}@{host}/{base}", modules={
        "models": [
            "midgard.models.transaction"
        ]
    })
    await Tortoise.generate_schemas()

    await foo_test()

    # ret = (await BEPTransaction.annotate())




if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
