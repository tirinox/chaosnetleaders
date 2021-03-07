from dataclasses import dataclass
from typing import Optional

from aiohttp import web

from helpers.utils import error_guard
from jobs.tx.storage import TxStorage
from leaderboard import leaderboard, total_volume
from models.tx import ThorTx

BOARD_LIMIT = 100
MAX_TS = 2_147_483_647


@dataclass
class API:
    network_id: str
    tx_storage: Optional[TxStorage] = None

    @error_guard
    async def handler_leaderboard(self, request):
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

        lb = await leaderboard(self.network_id, start_timestamp, final_timestamp, offset, limit, currency)
        tv = await total_volume(self.network_id, from_date=start_timestamp, to_date=final_timestamp, currency=currency)
        pt = await ThorTx.total_distinct_users_count(self.network_id,
                                                     from_date=start_timestamp,
                                                     to_date=final_timestamp)

        return web.json_response({
            'leaderboard': lb,
            'since': start_timestamp,
            'to': final_timestamp,
            'limit': limit,
            'chaosnet_volume': tv,
            'participants': pt,
            'offset': offset,
            'currency': currency,
        })

    @error_guard
    async def handler_sync_progress(self, request):
        progress, n_local, n_remote = await self.tx_storage.scan_progress()
        return web.json_response({
            'progress': 100 * progress,
            'local_tx_count': n_local,
            'remote_tx_count': n_remote
        })
