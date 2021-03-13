import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

import aiohttp

from helpers.constants import NetworkIdents
from jobs.tx.parser import TxParserBase, TxParseResult


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


def get_url_gen_by_network_id(network_id) -> MidgardURLGenBase:
    if network_id == NetworkIdents.TESTNET_MULTICHAIN:
        return MidgardURLGenV2(network_id)
    elif network_id == NetworkIdents.CHAOSNET_BEP2CHAIN:
        return MidgardURLGenV1(network_id)
    else:
        raise KeyError('unsupported network ID!')


class ITxDelegate(ABC):
    @abstractmethod
    async def on_transactions(self, tx_results: TxParseResult, scanner: 'TxScanner') -> bool:
        """
        :param scanner: TxScanner object
        :param tx_results:
        :return: True if you want to continue scanning otherwise False
        """
        ...

    @abstractmethod
    async def on_scan_start(self, scanner: 'TxScanner'):
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
    stop_flag: bool = False
    offset: int = 0
    batch_size: int = 50

    async def request_transaction_list(self, offset=0, limit=50):
        url = self.midgard_url_gen.url_for_tx(offset, limit)
        self.logger.info(f'GET {url}...')
        async with self.session.get(url) as resp:
            response_json = await resp.json()
            return self.parser.parse_tx_response(response_json)

    def stop_scan(self):
        self.working = False

    def rewind(self, to_offset):
        self.offset = to_offset

    async def run_scan(self, start=0, batch_size=50):
        assert self.delegate
        assert 0 < batch_size <= 50
        assert start >= 0
        self.batch_size = batch_size if batch_size else self.batch_size

        if self.working:
            self.logger.warning("I'm still working")
            return
        self.working = True
        self.offset = start

        current_retry = 0
        total_tx_got = 0

        await self.delegate.on_scan_start(self)

        while self.working:
            try:
                tx_results = await self.request_transaction_list(self.offset, batch_size)

                if not tx_results.tx_count_unfiltered:
                    self.logger.warning(f'no more TX, retry once after {self.sleep_before_retry:.1f} sec...')
                    await asyncio.sleep(self.sleep_before_retry)
                    tx_results = await self.request_transaction_list(self.offset, batch_size)

                if not tx_results.tx_count_unfiltered:
                    self.logger.warning(f'scan stop. reason: no more tx; total tx = {total_tx_got}')
                    break

                total_tx_got += tx_results.tx_count

                to_continue = await self.delegate.on_transactions(tx_results, self)
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
                self.offset += self.batch_size

        self.logger.info('finished')
        self.working = False
