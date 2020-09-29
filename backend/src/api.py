from aiohttp import web

from midgard.aggregator import leaderboard, total_volume, total_items_in_leaderboard
from utils import error_guard

START_TIMESTAMP = 1599739200  # 12pm UTC, Thursday 10th September 2020
BOARD_LIMIT = 100


@error_guard
async def handler_leaderboard(request):
    timestamp = int(request.rel_url.query.get('since') or START_TIMESTAMP)
    limit = int(request.rel_url.query.get('limit') or BOARD_LIMIT)
    offset = int(request.rel_url.query.get('offset') or 0)

    limit = min(limit, BOARD_LIMIT)

    lb = await leaderboard(timestamp, offset, limit)
    tv = await total_volume(from_date=timestamp)
    pt = await total_items_in_leaderboard(from_date=timestamp)

    return web.json_response({
        'leaderboard': lb,
        'since': timestamp,
        'limit': limit,
        'chaosnet_volume': tv,
        'participants': pt,
        'offset': offset
    })
