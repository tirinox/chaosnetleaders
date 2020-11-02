import asyncio
import logging
import os

from dotenv import load_dotenv
from tortoise import Tortoise
import time

from tortoise.functions import Sum, Count

from api import COMP_START_TIMESTAMP, COMP_END_TIMESTAMP
from midgard.aggregator import total_volume, leaderboard, total_items_in_leaderboard
from midgard.fetcher import run_fetcher, get_more_transactions_periodically
from midgard.models.transaction import BEPTransaction
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

    # tr = await BEPTransaction.filter(id=732).first()
    # print(f"tr = {tr}")
    # brpr = await BEPTransaction.get_best_rune_price(tr.pool, tr.date)
    # print(f"best rune price {tr.pool} @ {tr.date} => {brpr}")
    # print(await tr.calculate_rune_volume())

    # print(await total_items_in_leaderboard(from_date=1600959386))

    # print(await BEPTransaction.all_for_address('bnb1k5ypfc7azkkt8v792ucgldlfrlh0att5733lxc'))

    # await run_fetcher()
    # await period_delay_test()
    # await get_more_transactions_periodically()
    # await fill_rune_volumes()

    # await BEPTransaction.clear_rune_volume()
    #
    # lb = await leaderboard(from_date=1600959386)
    # print(lb)

    from_date = COMP_START_TIMESTAMP
    to_date = COMP_END_TIMESTAMP
    limit, offset = 0, 0

    r = BEPTransaction \
        .annotate(total_volume=Sum('rune_volume'), n=Count('id')) \
        .filter(date__gte=from_date) \
        .filter(date__lte=to_date) \
        .group_by('input_address') \
        .order_by('-total_volume') \
        .offset(offset) \
        .limit(limit) \
        .values('total_volume', 'input_address', 'date', 'n').sql()
    print(r)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
