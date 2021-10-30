import logging
import random
from dataclasses import dataclass
from typing import Optional

from jobs.tx.parser import TxParseResult
from jobs.tx.scanner import ITxDelegate, TxScanner
from models.tx import ThorTx


@dataclass
class TxStorage(ITxDelegate):
    full_scan: bool = False
    last_page_counter: int = 0
    overscan_pages: int = 10
    logger = logging.getLogger('TxStorage')
    jump_down_flag: bool = False
    last_tx_result: Optional[TxParseResult] = None

    async def on_scan_start(self, scanner: TxScanner):
        self.last_page_counter = 0
        self.jump_down_flag = False

    async def on_transactions(self, tx_results: TxParseResult, scanner: TxScanner) -> bool:
        new_count = 0
        for tx in tx_results.txs:
            if await tx.save_unique():
                new_count += 1

        # save last results for statistics
        if not self.last_tx_result or tx_results.total_count:
            self.last_tx_result = tx_results

        n_local, n_remote, percent = await self.get_scan_progress()
        if n_remote:
            self.logger.info(f'Scan progress: {percent:.2f} % ({n_local} / {n_remote}) and '
                             f'{new_count} TXS added this iteration')

        if not self.full_scan:
            if new_count == 0:  # all tx are already in out DB
                self.last_page_counter += 1
                if self.last_page_counter > self.overscan_pages:
                    # overscan has failed => try jump to a random location and scan there
                    if not self.jump_down_flag:
                        jump_location = random.randint(0, self.last_tx_result.total_count)
                        self.logger.warning(f'jumping to {jump_location} offset to discover any new tx')
                        scanner.rewind(jump_location)
                        self.last_page_counter = 0
                        self.jump_down_flag = True
                    else:
                        return False  # STOP SCANNING
                self.logger.info(f'over scan: {self.last_page_counter} pages')
            else:
                self.last_page_counter = 0  # reset if found new tx

        return True

    async def get_scan_progress(self):
        n_local = await ThorTx.count_of_transactions_for_network(self.last_tx_result.network_id)
        n_remote = self.last_tx_result.total_count
        percent = 100 * n_local / n_remote if n_remote else 0.0
        return n_local, n_remote, percent


@dataclass
class TxStorageMock(ITxDelegate):
    full_scan: bool = False
    logger = logging.getLogger('TxStorageMock')

    async def on_scan_start(self, scanner: TxScanner):
        ...

    async def on_transactions(self, tx_results: TxParseResult, scanner: TxScanner) -> bool:
        return True

    async def get_scan_progress(self):
        n_local = 0
        n_remote = 1
        percent = 0
        return n_local, n_remote, percent
