from aiohttp import web

from helpers.utils import error_guard

BOARD_LIMIT = 100
MAX_TS = 2_147_483_647


#
# COMP_START_TIMESTAMP = 1599739200  # 12pm UTC, Thursday 10th September 2020
# COMP_END_TIMESTAMP = 1602158400  # 12pm UTC, Thursday 8th October 2020
#
#
# @error_guard
# async def handler_leaderboard(request):
#     start_timestamp = int(request.rel_url.query.get('since') or COMP_START_TIMESTAMP)
#     final_timestamp = int(request.rel_url.query.get('to') or COMP_END_TIMESTAMP)
#
#     currency = request.rel_url.query.get('currency')
#     if currency not in ('rune', 'usd'):
#         currency = 'rune'
#
#     if final_timestamp <= 0:
#         final_timestamp = MAX_TS
#
#     limit = int(request.rel_url.query.get('limit') or BOARD_LIMIT)
#     offset = int(request.rel_url.query.get('offset') or 0)
#
#     limit = min(limit, BOARD_LIMIT)
#
#     lb = await leaderboard(start_timestamp, final_timestamp, offset, limit, currency)
#     tv = await total_volume(from_date=start_timestamp, to_date=final_timestamp, currency=currency)
#     pt = await total_items_in_leaderboard(from_date=start_timestamp, to_date=final_timestamp)
#
#     return web.json_response({
#         'leaderboard': lb,
#         'since': start_timestamp,
#         'to': final_timestamp,
#         'limit': limit,
#         'chaosnet_volume': tv,
#         'participants': pt,
#         'offset': offset,
#         'currency': currency,
#     })

@error_guard
async def handler_leaderboard(request):
    start_timestamp = int(request.rel_url.query.get('since') or 0)
    final_timestamp = int(request.rel_url.query.get('to') or 0)

    currency = request.rel_url.query.get('currency')
    if currency not in ('rune', 'usd'):
        currency = 'rune'

    if final_timestamp <= 0:
        final_timestamp = MAX_TS

    limit = int(request.rel_url.query.get('limit') or BOARD_LIMIT)
    offset = int(request.rel_url.query.get('offset') or 0)

    limit = min(limit, BOARD_LIMIT)

    return web.json_response({
        'todo': 'work in progress'
    })
