import asyncio
import logging

from dotenv import load_dotenv

from helpers.db import DB
from models.transaction import ThorTransaction

logging.basicConfig(level=logging.INFO)


async def amain():
    db = DB()
    await db.start()



if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
