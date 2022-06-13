from pathlib import Path
from typing import Optional


def get_cwd(file: Optional[str] = None) -> Path:
    return Path(file or __file__).parent
