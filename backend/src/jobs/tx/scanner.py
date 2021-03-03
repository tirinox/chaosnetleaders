import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import aiohttp

from jobs.tx.parser import TxParserBase, TxParseResult
from models.tx import ThorTx


class NetworkIdents:
    TESTNET_MULTICHAIN = 'testnet-multi'
    CHAOSNET_MULTICHAIN = 'chaosnet-multi'
    CHAOSNET_BEP2CHAIN = 'chaosnet-bep2'


class MidgardURLGenBase(ABC):
    def __init__(self, network_id):
        self.network_id = network_id

    @abstractmethod
    def url_for_tx(self, offset=0, count=50) -> str:
        ...


class MidgardURLGenV1(MidgardURLGenBase):
    def __init__(self, network_id=NetworkIdents.CHAOSNET_BEP2CHAIN):
        super().__init__(network_id)

    def url_for_tx(self, offset=0, count=50) -> str:
        return f'https://chaosnet-midgard.bepswap.com/v1/txs?offset={offset}&limit={count}'


class MidgardURLGenV2(MidgardURLGenBase):
    def __init__(self, network_id=NetworkIdents.TESTNET_MULTICHAIN):
        super().__init__(network_id)

    def url_for_tx(self, offset=0, count=50) -> str:
        return f'https://testnet.midgard.thorchain.info/v2/actions?offset={offset}&limit={count}'


class ITxDelegate(ABC):
    @abstractmethod
    async def on_transactions(self, tx_results: TxParseResult) -> bool:
        """
        :param tx_results:
        :return: True if you want to continue scanning otherwise False
        """
        ...

    @abstractmethod
    async def on_scan_start(self):
        ...


@dataclass
class TxScanner:
    midgard_url_gen: MidgardURLGenBase
    session: aiohttp.ClientSession
    parser: TxParserBase
    delegate: Optional[ITxDelegate] = None
    logger = logging.getLogger('TxScanner')
    retries: int = 3
    working: bool = False
    sleep_before_retry: float = 3.0

    async def request_transaction_list(self, offset=0, limit=50):
        url = self.midgard_url_gen.url_for_tx(offset, limit)
        self.logger.info(f'GET {url}...')
        async with self.session.get(url) as resp:
            response_json = await resp.json()
            return self.parser.parse_tx_response(response_json)

    async def run_scan(self, start=0, batch_size=50):
        assert self.delegate

        if self.working:
            self.logger.warning("I'm still working")
            return
        self.working = True

        offset = start
        current_retry = 0
        total_tx_got = 0

        await self.delegate.on_scan_start()

        while True:
            try:
                tx_results = await self.request_transaction_list(offset, batch_size)

                if not tx_results.tx_count_unfiltered:
                    self.logger.warning(f'no more TX, retry once after {self.sleep_before_retry:.1f} sec...')
                    await asyncio.sleep(self.sleep_before_retry)
                    tx_results = await self.request_transaction_list(offset, batch_size)

                if not tx_results.tx_count_unfiltered:
                    self.logger.warning(f'scan stop. reason: no more tx; total tx = {total_tx_got}')
                    break

                total_tx_got += tx_results.tx_count

                to_continue = await self.delegate.on_transactions(tx_results)
                if not to_continue:
                    self.logger.info(f'scan stop. reason: delegate insists to stop; total tx = {total_tx_got}')
                    break

            except Exception as e:
                self.logger.exception(f'exception has been raised while tx scanning: {e!r}. '
                                      f'retry after {self.sleep_before_retry:.1f} sec...')
                current_retry += 1
                if current_retry > self.retries:
                    self.logger.error(f'retry limit reached; stopping scan! total tx = {total_tx_got}')
                    break
                await asyncio.sleep(self.sleep_before_retry)
            else:
                current_retry = 0
                offset += batch_size

        self.logger.info('finished')
        self.working = False

# --------- old stuff ---------

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
