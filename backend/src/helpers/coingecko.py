from aiohttp import ClientSession

COIN_GECKO_PRICE_HISTORY = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range?" \
                           "vs_currency=usd&from={t_from}&to={t_to}"

COIN_GECKO_RUNE_SYMBOL = 'thorchain'
COIN_GECKO_TIME_RANGE_SEC = 3600  # experimentally chosen


async def cg_get_historical_rune_price(timestamp: int, session: ClientSession):
    url = COIN_GECKO_PRICE_HISTORY.format(coin=COIN_GECKO_RUNE_SYMBOL,
                                          t_from=timestamp - COIN_GECKO_TIME_RANGE_SEC,
                                          t_to=timestamp + COIN_GECKO_TIME_RANGE_SEC)
    async with session.get(url) as resp:
        response_json = await resp.json()
        prices = response_json.get('prices', [])
        if prices:
            return float(prices[0][1])
        else:
            return 0.0
