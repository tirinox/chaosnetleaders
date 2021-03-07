from tortoise import Tortoise
from tortoise.functions import Max

from helpers.constants import NetworkIdents
from models.tx import ThorTx, ThorTxType


async def leaderboard_raw(network_id, from_date=0, to_date=0, offset=0, limit=10, currency='rune'):
    if currency == 'rune':
        sum_variable = "rune_volume"
    else:
        sum_variable = "usd_volume"

    end_date_cond = f' AND date <= {int(to_date)} ' if to_date else ''

    q = (f"SELECT "
         f" user_address,"
         f" SUM({sum_variable}) total_volume, MAX(date) as date, "
         f" COUNT(id) n "
         f" FROM thortx "
         f" WHERE network = '{network_id}' "
         f" AND type = '{ThorTxType.TYPE_SWAP}' "
         f' AND date >= {int(from_date)} {end_date_cond}'
         f" GROUP BY user_address "
         f" ORDER BY SUM({sum_variable}) "
         f" DESC LIMIT {int(limit)} OFFSET {int(offset)}")

    conn = Tortoise.get_connection("default")
    return await conn.execute_query_dict(q)


async def leaderboard(network_id, from_date=0, to_date=0, offset=0, limit=10, currency='rune'):
    results = await leaderboard_raw(network_id, from_date, to_date, offset, limit, currency)

    last_dates = await ThorTx \
        .annotate(last_date=Max('date')) \
        .filter(network=network_id, type=ThorTxType.TYPE_SWAP, date__gte=from_date) \
        .group_by('user_address') \
        .values('user_address', 'last_date')
    last_dates_cache = {e['user_address']: e['last_date'] for e in last_dates}

    for item in results:
        item['date'] = last_dates_cache.get(item['user_address'], item['date'])

    return results


async def total_volume(network_id, from_date=0, to_date=0, currency='rune'):
    try:
        if currency == 'rune':
            sum_variable = "rune_volume"
        else:
            sum_variable = "usd_volume"

        sql = (f"SELECT SUM({sum_variable}) v FROM thortx "
               f"WHERE network = '{network_id}' AND type = '{ThorTxType.TYPE_SWAP}' AND "
               f"date >= {int(from_date)} ")
        if to_date:
            sql += f" AND date <= {int(to_date)} "

        conn = Tortoise.get_connection("default")
        result = await conn.execute_query_dict(sql)

        return float(result[0]['v'])
    except (TypeError, LookupError):
        return 0


async def dbg_print_leaderboard():
    results = await leaderboard(NetworkIdents.CHAOSNET_BEP2CHAIN)
    for place, result in enumerate(results, start=1):
        print(f"#{place}: {result}")
