from dataclasses import dataclass
from typing import Optional

from helpers.db import DB


@dataclass
class Dependencies:
    db: Optional[DB] = None
    api: Optional['API'] = None
    last_tx_result: Optional['TxParseResult'] = None
    tx_storage: Optional['TxStorage'] = None
    tx_scanner: Optional['TxScanner'] = None
