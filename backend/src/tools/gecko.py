import asyncio

import aiohttp
import datetime

from helpers.coingecko import cg_get_historical_rune_price


async def main():
    t_early = 1598617260
    async with aiohttp.ClientSession() as session:
        result = await cg_get_historical_rune_price(t_early, session)
        print(f'Rune price @ {datetime.datetime.fromtimestamp(t_early)} is ${result:0.3f}.')


if __name__ == "__main__":
    asyncio.run(main())
