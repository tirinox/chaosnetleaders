from dataclasses import dataclass
from typing import Optional

from helpers.db import DB

@dataclass
class Dependencies:
    db: Optional[DB] = None
