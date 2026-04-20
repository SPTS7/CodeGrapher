from dataclasses import dataclass
from typing import List, Optional

class CodeAnalysisError(Exception):
    pass

@dataclass
class FunctionInfo:
    name: str
    calls: List[str]
    source_code: str
    file_path: str
    complexity: int = 0
    summary: str = "No AI summary generated."
    line_number: int = 0
    is_async: bool = False
    is_method: bool = False
    docstring: Optional[str] = None
    signature: str = ""
