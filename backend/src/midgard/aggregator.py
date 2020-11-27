import asyncio
import logging

import aiohttp
import names
from tortoise import Tortoise
from tortoise.functions import Max, Count

from midgard.models.transaction import BEPTransaction
from midgard.pool_price import PoolPriceCache, PoolPriceFetcher

FILL_VOLUME_BATCH = 100

DONT_FILL_RUNE_PRICE_BEFORE = 1598788800  # Sunday, 30-Aug-20 12:00:00 UTC in RFC 2822

pool_price_cache = PoolPriceCache()


async def fill_rune_volumes():
    number = 0
    name = names.get_full_name()
    logger = logging.getLogger(name)
    async with aiohttp.ClientSession() as session:
        fetcher = PoolPriceFetcher(session)

        n_passed = 0
        n_passed_limit = 100
        while True:
            try:
                tx, n = await BEPTransaction.random_tx_without_volume()
                if not tx:
                    break

                if tx.date < DONT_FILL_RUNE_PRICE_BEFORE:
                    n_passed += 1
                    if n_passed < n_passed_limit and n >= 2:
                        continue
                    else:
                        break

                await tx.fill_tx_volume_and_usd_prices(pool_price_cache, fetcher)
                await tx.save()

                number += 1
                logger.info(f'filled usd data for {tx.id} ({tx.rune_volume:.1f} R). {number}/{n}')
            except Exception as e:
                logger.exception(f'fill_rune_volumes error, I will sleep for a little while {tx.hash} ({tx})',
                                 exc_info=False)
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


async def leaderboard_raw(from_date=0, to_date=0, offset=0, limit=10, currency='rune'):
    if currency == 'rune':
        sum_variable = "`rune_volume`"
        usd_filled_condition = ''
    else:
        sum_variable = "`input_amount` * `input_usd_price`"
        usd_filled_condition = ' AND `input_usd_price` > 0 '

    q = (f"SELECT "
         f"`input_address` `input_address`,"
         f"SUM({sum_variable}) `total_volume`, MAX(`date`) as `date`,"
         f"COUNT(`id`) `n` "
         f"FROM `beptransaction` "
         f"WHERE `date` >= {int(from_date)} AND `date` <= {int(to_date)} {usd_filled_condition} "
         f"GROUP BY `input_address` "
         f"ORDER BY SUM({sum_variable}) "
         f"DESC LIMIT {int(limit)} OFFSET {int(offset)}")

    conn = Tortoise.get_connection("default")
    return await conn.execute_query_dict(q)


async def leaderboard(from_date=0, to_date=0, offset=0, limit=10, currency='rune'):
    results = await leaderboard_raw(from_date, to_date, offset, limit, currency)

    last_dates = await BEPTransaction \
        .annotate(last_date=Max('date')) \
        .filter(date__gte=from_date) \
        .group_by('input_address') \
        .values('input_address', 'last_date')
    last_dates_cache = {e['input_address']: e['last_date'] for e in last_dates}

    for item in results:
        item['date'] = last_dates_cache.get(item['input_address'], item['date'])

    return results


async def total_volume(from_date=0, to_date=0, currency='rune'):
    try:
        if currency == 'rune':
            sum_variable = "`rune_volume`"
            usd_filled_condition = ''
        else:
            sum_variable = "`input_amount` * `input_usd_price`"
            usd_filled_condition = ' AND `input_usd_price` > 0 '

        sql = (f"SELECT SUM({sum_variable}) `v` FROM `beptransaction` "
               f"WHERE `date` >= {int(from_date)} AND `date` <= {int(to_date)} {usd_filled_condition}")

        conn = Tortoise.get_connection("default")
        result = await conn.execute_query_dict(sql)

        return float(result[0]['v'])
    except (TypeError, LookupError):
        return 0


async def dbg_print_leaderboard():
    results = await leaderboard(0)
    for place, result in enumerate(results, start=1):
        print(f"#{place}: {result}")
