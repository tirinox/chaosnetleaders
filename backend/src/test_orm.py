import asyncio
from dotenv import load_dotenv
import os

from tortoise import Tortoise, fields, run_async
from midgard.models.transaction import Trasnaction


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

    event = await Trasnaction.create(name="34309091ab38031")
    # await Trasnaction.filter(id=event.id).update(name="Updated name")

    print(await Trasnaction.filter(name="34309091ab38031").first())


if __name__ == '__main__':
    load_dotenv('../../.env')
    asyncio.run(amain())
