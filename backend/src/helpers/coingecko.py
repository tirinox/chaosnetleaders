from aiohttp import ClientSession

from helpers.datetime import HOUR, TemporalCache

COIN_GECKO_PRICE_HISTORY = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart/range?" \
                           "vs_currency=usd&from={t_from}&to={t_to}"

COIN_GECKO_RUNE_SYMBOL = 'thorchain'
COIN_GECKO_TIME_RANGE_SEC = 2400  # experimentally chosen


class CoinGeckoPriceProvider:
    def __init__(self, session: ClientSession, cache_precision=HOUR):
        self.session = session
        self.cache = TemporalCache(cache_precision)

    async def _get_historical_rune_price(self, timestamp: int):
        url = COIN_GECKO_PRICE_HISTORY.format(coin=COIN_GECKO_RUNE_SYMBOL,
                                              t_from=timestamp - COIN_GECKO_TIME_RANGE_SEC,
                                              t_to=timestamp + COIN_GECKO_TIME_RANGE_SEC)
        async with self.session.get(url) as resp:
            response_json = await resp.json()
            prices = response_json.get('prices', [])
            if prices:
                return float(prices[0][1])
            else:
                return 0.0

    async def get_historical_rune_price(self, timestamp: int, cached=True):
        old_value = self.cache[timestamp] if cached else None
        if old_value:
            return old_value
        else:
            value = await self._get_historical_rune_price(timestamp)
            self.cache[timestamp] = value
            return value
