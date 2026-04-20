from pathlib import Path
from typing import Optional, Type
from codegrapher.parsers.base import BaseParser
from codegrapher.parsers.python import PythonParser
from codegrapher.parsers.javascript import JSParser

def get_parser(file_path: Path) -> Optional[Type[BaseParser]]:
    """Returns the appropriate parser class based on the file extension."""
    ext = file_path.suffix.lower()
    if ext == '.py':
        return PythonParser
    elif ext in ['.js', '.jsx', '.ts', '.tsx']:
        return JSParser
    return None

def is_supported_file(file_path: Path) -> bool:
    return get_parser(file_path) is not None
