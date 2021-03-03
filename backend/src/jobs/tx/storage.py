import logging
from dataclasses import dataclass
from typing import Optional

from helpers.deps import Dependencies
from jobs.tx.parser import TxParseResult
from jobs.tx.scanner import ITxDelegate
from models.tx import ThorTx


@dataclass
class TxStorage(ITxDelegate):
    deps: Dependencies
    full_scan: bool = False
    last_page_counter: int = 0
    overscan_pages: int = 2
    logger = logging.getLogger('TxStorage')
    last_result: Optional[TxParseResult] = None

    async def on_scan_start(self):
        self.last_page_counter = 0

    async def on_transactions(self, tx_results: TxParseResult) -> bool:
        any_new_tx = False
        for tx in tx_results.txs:
            if await tx.save_unique():
                any_new_tx = True

        if not self.last_result or tx_results.total_count:
            self.last_result = tx_results

        if not self.full_scan:
            if not any_new_tx:
                self.last_page_counter += 1
                if self.last_page_counter > self.overscan_pages:
                    return False
                self.logger.info(f'over scan: {self.last_page_counter} pages')
            else:
                self.last_page_counter = 0  # reset if found new tx

        progress, n_local, n_remote = await self.scan_progress()
        if n_remote:
            self.logger.info(f'Scan progress: {(progress * 100):.2f} % ({n_local} / {n_remote})')

        return True

    async def scan_progress(self):
        n_local = await ThorTx.count_of_transactions_for_network(self.last_result.network_id)
        n_remote = self.last_result.total_count
        ratio = n_local / n_remote if n_remote else 0.0
        return ratio, n_local, n_remote
