"""ingestion/sources/base.py

TradeSource interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator


class TradeSource(ABC):
    @abstractmethod
    def iter_records(self) -> Iterator[Dict[str, Any]]:
        """Yield raw records (dict) that can be normalized into Trade."""
