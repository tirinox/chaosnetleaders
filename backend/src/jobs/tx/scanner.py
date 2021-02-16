import logging

import aiohttp

from models.tx import ThorTx




# v1 (chaosnet)
# https://chaosnet-midgard.bepswap.com/v1/txs?asset=USDT-6D8&offset=400&limit=50&type=swap,doubleSwap
#

# v2 (multinet)
# https://testnet.midgard.thorchain.info/v2/actions?limit=10&offset=100
# swap, addLiquidity, withdraw, donate, refund


class TxScanner:
    def __init__(self, midgard_url: str, session: aiohttp.ClientSession):
        self.midgard_url = midgard_url
        self.session = session

    async def get_transaction_list(self, offset, limit):
        url = self.midgard_url.format(offset=offset, limit=limit)
        logging.info(f'getting {url}...')
        async with self.session.get(url) as resp:
            json = await resp.json()
            count = int(json.get('count', 0))
            models = []
            txs = json.get('txs')
            for i, tx in enumerate(txs, start=1):
                tx_model = ThorTx.from_json(tx)
                if tx_model is not None:
                    models.append(tx_model)

            return models, count, len(txs) > 0

    # async def calculate_rune_volume(self):
    #     if self.type == self.TYPE_SWAP:
    #         # simple
    #         return self.input_amount if self.input_asset == RUNE_SYMBOL_NATIVE else self.output_amount
    #     else:
    #         # double
    #         input_price, input_date = await self.get_best_rune_price(self.input_asset, self.date)
    #         output_price, output_date = await self.get_best_rune_price(self.output_asset, self.date)
    #
    #         if input_price and output_price:
    #             input_later = input_date > output_date
    #             price = input_price if input_later else output_price
    #             amount = self.input_amount if input_later else self.output_amount
    #         elif input_price:
    #             price = input_price
    #             amount = self.input_amount
    #         elif output_price:
    #             price = output_price
    #             amount = self.output_amount
    #         else:
    #             return None
    #         return amount * price
    #
    # async def fill_tx_volume_and_usd_prices(self, ppc: 'PoolPriceCache', fetcher: PoolPriceFetcher):
    #     _, self.output_usd_price = await ppc.get_historical_price(fetcher, self.output_asset, self.block_height)
    #     dollar_per_rune, self.input_usd_price = await ppc.get_historical_price(fetcher, self.input_asset,
    #                                                                            self.block_height)
    #
    #     self.rune_volume = self.input_amount * self.input_usd_price / dollar_per_rune
    #     return self
