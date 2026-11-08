import re
import unicodedata

def str_display_width(s: str) -> int:
    """Compute visual terminal cell width (ignoring ANSI codes & handling CJK characters)."""
    visible = re.sub(r"\033\[[0-9;]*[a-zA-Z~]", "", s)
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in visible)

def pad_display(s: str, target_width: int) -> str:
    """Pad string with spaces to reach visual target width in terminal cells."""
    current_width = str_display_width(s)
    return s + " " * max(0, target_width - current_width)
