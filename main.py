"""Backward-compatibility shim for clanki.
Original monolithic main.py has been moved to archive/main.py.
"""
from pathlib import Path
import sys

# Ensure src/ is accessible if invoked directly as `python main.py`
src_dir = str(Path(__file__).resolve().parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from clanki.cli import main

if __name__ == "__main__":
    main()
