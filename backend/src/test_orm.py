import asyncio
import os

from dotenv import load_dotenv
from tortoise import Tortoise

from midgard.fetcher import run_fetcher


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

    # await get_more_transactions()
    # await fill_rune_volumes()

    await run_fetcher()

    while True:
        await asyncio.sleep(5.0)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
