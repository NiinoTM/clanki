import atexit
import re
import sys
from typing import Any
import unicodedata
from clanki.ui.theme import (
    ALT_SCREEN_ENTER,
    ALT_SCREEN_EXIT,
    BOLD,
    CLEAR_FROM_HOME,
    CURSOR_HIDE,
    CURSOR_HOME,
    CURSOR_SHOW,
    C_CYAN,
    C_GREEN,
    DIM,
    RESET,
)

def clear_screen() -> None:
    """Home cursor to row 1, col 1 and clear screen below while suppressing flicker."""
    sys.stdout.write(f"{CURSOR_HIDE}{CURSOR_HOME}{CLEAR_FROM_HOME}")
    sys.stdout.flush()

class TerminalScreen:
    """Context manager to run the UI inside the alternate screen buffer with guaranteed restoration."""

    _active = False

    def __enter__(self) -> "TerminalScreen":
        self.resume()
        atexit.register(self._cleanup)
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._cleanup()

    @classmethod
    def resume(cls) -> None:
        """Switch into alternate screen buffer and home cursor."""
        sys.stdout.write(f"{ALT_SCREEN_ENTER}{CURSOR_HOME}{CLEAR_FROM_HOME}")
        sys.stdout.flush()
        cls._active = True

    @classmethod
    def suspend(cls) -> None:
        """Temporarily drop out of alternate buffer to allow external CLI tools to run."""
        sys.stdout.write(f"{CURSOR_SHOW}{ALT_SCREEN_EXIT}")
        sys.stdout.flush()
        cls._active = False

    def _cleanup(self) -> None:
        self.suspend()

def render_progress(percent: int, message: str, bar_width: int = 24) -> str:
    """Format an apt-style progress bar string with percentage and status message."""
    clamped = max(0, min(100, percent))
    filled = int(bar_width * (clamped / 100))
    empty = bar_width - filled
    bar = f"{C_GREEN}{'#' * filled}{RESET}{DIM}{'.' * empty}{RESET}"
    return f"\r{BOLD}Progress:{RESET} [{BOLD}{C_CYAN}{clamped:>3d}%{RESET}] [{bar}] {message}\033[K"

def str_display_width(s: str) -> int:
    """Compute visual terminal cell width (ignoring ANSI codes & handling CJK characters)."""
    visible = re.sub(r"\033\[[0-9;]*[a-zA-Z~]", "", s)
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in visible)

def pad_display(s: str, target_width: int) -> str:
    """Pad string with spaces to reach visual target width in terminal cells."""
    current_width = str_display_width(s)
    return s + " " * max(0, target_width - current_width)
