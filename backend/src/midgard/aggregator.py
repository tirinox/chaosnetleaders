from tortoise import Tortoise
from tortoise.functions import Max, Count

from models.transaction import BEPTransaction


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
