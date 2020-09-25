import logging
import os

from aiohttp import web
from dotenv import load_dotenv
from tortoise import Tortoise

from midgard.aggregator import leaderboard
from midgard.fetcher import run_fetcher

logging.basicConfig(level=logging.INFO)

START_TIMESTAMP = 1599739200  # 12pm UTC, Thursday 10th September 2020
BOARD_LIMIT = 100
PORT = 5000


async def handler_leaderboard(request):
    timestamp = int(request.rel_url.query.get('since') or START_TIMESTAMP)
    limit = int(request.rel_url.query.get('limit') or BOARD_LIMIT)

    lb = await leaderboard(timestamp, limit)
    return web.json_response({
        'leaderboard': lb,
        'since': timestamp,
        'limit': limit
    })


async def init_db(*_):
    host = os.environ.get('MYSQL_HOST', 'localhost')
    user = os.environ['MYSQL_USER']
    password = os.environ['MYSQL_PASSWORD']
    base = os.environ['MYSQL_DATABASE']

    await Tortoise.init(db_url=f"mysql://{user}:{password}@{host}/{base}", modules={
        "models": [
            "midgard.models.transaction",
        ]
    })
    await Tortoise.generate_schemas()


if __name__ == '__main__':
    load_dotenv('../../.env')

    app = web.Application(middlewares=[])
    app.add_routes([web.get('/api/v1/leaderboard', handler_leaderboard)])
    app.on_startup.append(init_db)
    app.on_startup.append(run_fetcher)

    web.run_app(app, port=PORT)
