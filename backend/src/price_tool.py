import asyncio
import logging

from dotenv import load_dotenv

from main import init_db
from midgard.aggregator import fill_rune_volumes
from midgard.fetcher import get_more_transactions_periodically, FILL_INTERVAL
from utils import schedule_task_periodically

logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()

    n_fillers = 2
    for i in range(n_fillers):
        schedule_task_periodically(FILL_INTERVAL, fill_rune_volumes)

    start = 0
    await get_more_transactions_periodically(full_scan=True, start=start)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
