from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO

from .import_result import ImportResult
from .source_context import SourceContext


class BaseConnector(ABC):
    @abstractmethod
    def can_handle(self, file: BinaryIO, context: SourceContext) -> bool:
        raise NotImplementedError

    @abstractmethod
    def parse(self, file: BinaryIO, context: SourceContext) -> ImportResult:
        raise NotImplementedError
