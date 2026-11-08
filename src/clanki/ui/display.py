import re
import unicodedata
from clanki.ui.theme import BOLD, C_CYAN, C_GREEN, DIM, RESET

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
