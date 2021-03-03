import logging
from dataclasses import dataclass

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

    async def on_scan_start(self):
        self.last_page_counter = 0

    async def on_transactions(self, tx_results: TxParseResult) -> bool:
        any_new_tx = False
        for tx in tx_results.txs:
            if await tx.save_unique():
                any_new_tx = True

        if not self.full_scan:
            if not any_new_tx:
                self.last_page_counter += 1
                if self.last_page_counter > self.overscan_pages:
                    return False
                self.logger.info(f'over scan: {self.last_page_counter} pages')
            else:
                self.last_page_counter = 0  # reset if found new tx

        return True
