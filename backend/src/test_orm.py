import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from tortoise import Tortoise

from midgard.aggregator import fill_rune_volumes
from utils import schedule_task_periodically

logging.basicConfig(level=logging.INFO)


async def period_delay_test():
    print(f'start {time.time()}')

    async def foo():
        print(f'foo! {time.time()}')

    schedule_task_periodically(5, foo, 3)

    await asyncio.sleep(30)


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

    await fill_rune_volumes()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
