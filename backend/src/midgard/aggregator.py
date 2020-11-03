import asyncio

import aiohttp
from tortoise.functions import Sum, Max, Count

from midgard.models.transaction import BEPTransaction

import logging

from midgard.pool_price import PoolPriceCache, PoolPriceFetcher

FILL_VOLUME_BATCH = 100

pool_price_cache = PoolPriceCache()


async def fill_rune_volumes():
    number = 0
    async with aiohttp.ClientSession() as session:
        fetcher = PoolPriceFetcher(session)

        while True:
            try:
                tx = await BEPTransaction.random_tx_without_volume()
                if not tx:
                    break
                await tx.fill_tx_volume_and_usd_prices(pool_price_cache, fetcher)
                await tx.save()

                number += 1
                logging.info(f'filled usd data for {tx}. n = {number} filled this session')
            except:
                logging.exception('fill_rune_volumes error, I will sleep for a little while')
                await asyncio.sleep(3.0)

    logging.info(f"fill_rune_volumes = {number} items filled")
    return number


async def total_items_in_leaderboard(from_date=0, to_date=0):
    r = await BEPTransaction \
        .annotate(total_addresses=Count('input_address', distinct=True)) \
        .filter(date__gte=from_date) \
        .filter(date__lte=to_date) \
        .values('total_addresses')
    return r[0]['total_addresses']


async def leaderboard(from_date=0, to_date=0, offset=0, limit=10):
    results = await BEPTransaction \
        .annotate(total_volume=Sum('rune_volume'), n=Count('id')) \
        .filter(date__gte=from_date) \
        .filter(date__lte=to_date) \
        .group_by('input_address') \
        .order_by('-total_volume') \
        .offset(offset) \
        .limit(limit) \
        .values('total_volume', 'input_address', 'date', 'n')

    last_dates = await BEPTransaction \
        .annotate(last_date=Max('date')) \
        .filter(date__gte=from_date) \
        .group_by('input_address') \
        .values('input_address', 'last_date')
    last_dates_cache = {e['input_address']: e['last_date'] for e in last_dates}

    for item in results:
        item['date'] = last_dates_cache.get(item['input_address'], item['date'])

    return results


async def total_volume(from_date=0, to_date=0):
    try:
        result = await BEPTransaction.annotate(v=Sum('rune_volume')) \
            .filter(date__gte=from_date) \
            .filter(date__lte=to_date) \
            .values('v')
        return float(result[0]['v'])
    except (TypeError, LookupError):
        return 0


async def dbg_print_leaderboard():
    results = await leaderboard(0)
    for place, result in enumerate(results, start=1):
        print(f"#{place}: {result}")
