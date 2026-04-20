from abc import ABC, abstractmethod
from typing import Dict, List, Any
from pathlib import Path

class BaseParser(ABC):
    def __init__(self, source_code: str, file_path: Path):
        self.source_code = source_code
        self.source_bytes = source_code.encode('utf-8')
        self.file_path = file_path
        self.functions: Dict[str, Any] = {}

    @abstractmethod
    def parse(self) -> Dict[str, Any]:
        """Parses the source code and returns a dictionary of function information."""
        pass
