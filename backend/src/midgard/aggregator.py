from tortoise.functions import Sum, Max, Count

from midgard.models.transaction import BEPTransaction

import logging


FILL_VOLUME_BATCH = 100


async def fill_rune_volumes():
    number = 0
    while True:
        txs = await BEPTransaction.without_volume().limit(FILL_VOLUME_BATCH)
        if not txs:
            break

        for tx in txs:
            await tx.fill_rune_volume()
            # print(f'{tx} : rune volume = {tx.rune_volume}')

        number += len(txs)

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
    # SELECT `input_address` `input_address`,`date` `date`,SUM(`rune_volume`) `total_volume`,COUNT(`id`) `n`
    # FROM `beptransaction`
    # WHERE `date`>=1599739200 AND `date`<=1602158400
    # GROUP BY `input_address`
    # ORDER BY SUM(`rune_volume`) DESC

    results = await BEPTransaction\
        .annotate(total_volume=Sum('rune_volume'), n=Count('id'))\
        .filter(date__gte=from_date)\
        .filter(date__lte=to_date) \
        .group_by('input_address') \
        .order_by('-total_volume') \
        .offset(offset)\
        .limit(limit)\
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
        result = await BEPTransaction.annotate(v=Sum('rune_volume'))\
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
