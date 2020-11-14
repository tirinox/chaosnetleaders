import asyncio
import logging
import os
import time

from dotenv import load_dotenv
from tortoise import Tortoise
from tortoise.functions import Sum, Count

from midgard.aggregator import fill_rune_volumes, leaderboard_raw, total_volume
from midgard.models.transaction import BEPTransaction
from utils import schedule_task_periodically

logging.basicConfig(level=logging.INFO)


async def period_delay_test():
    print(f'start {time.time()}')

    async def foo():
        print(f'foo! {time.time()}')

    schedule_task_periodically(5, foo, 3)

    await asyncio.sleep(30)


async def get_sql_lb():
    r = await leaderboard_raw(from_date=1604401655, to_date=1654401655, offset=0, limit=100, currency='usd')
    print(*r, sep='\n')


async def get_tot_vol():
    r = BEPTransaction.annotate(v=Sum('rune_volume')) \
        .filter(date__gte=1604401655) \
        .filter(date__lte=1654401655) \
        .values('v').sql()
    print(r)
    r = await total_volume(1604401655, 1654401655, 'rune')
    print(r)


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

    # await fill_rune_volumes()

    # await get_sql_lb()
    await get_tot_vol()


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
