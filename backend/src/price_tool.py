import asyncio
import logging

from dotenv import load_dotenv

from main import init_db
from midgard.value_filler import ValueFiller

logging.basicConfig(level=logging.INFO)


async def main():
    await init_db()

    await ValueFiller(n_workers=8).run(blocking=True)


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(main())
