from tortoise.functions import Sum, Max

from midgard.models.transaction import BEPTransaction

import logging


BATCH = 100


async def fill_rune_volumes():
    number = 0
    while True:
        txs = await BEPTransaction.without_volume().limit(100)
        if not txs:
            break

        for tx in txs:
            await tx.fill_rune_volume()
            # print(f'{tx} : rune volume = {tx.rune_volume}')

        number += len(txs)

    logging.info(f"fill_rune_volumes = {number} items filled")
    return number


async def leaderboard(from_date=0, limit=10):
    # select input_address, sum(rune_volume) as total_volume
    # from beptransaction
    # where date > 1599739200
    # group by input_address order by total_volume desc;
    results = await BEPTransaction\
        .annotate(total_volume=Sum('rune_volume'), date=Max('date'))\
        .filter(date__gte=from_date)\
        .group_by('input_address')\
        .order_by('-total_volume') \
        .limit(limit)\
        .values('total_volume', 'input_address', 'date')

    return results


async def total_volume(from_date=0):
    try:
        result = await BEPTransaction.annotate(v=Sum('rune_volume'))\
            .filter(date__gte=from_date)\
            .values('v')
        return float(result[0]['v'])
    except (TypeError, LookupError):
        return 0


async def dbg_print_leaderboard():
    results = await leaderboard(0)
    for place, result in enumerate(results, start=1):
        print(f"#{place}: {result}")
