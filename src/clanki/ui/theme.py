# ANSI Terminal Formatting Palette & Style Tokens

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
C_DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Foreground Colors
C_BLACK = "\033[30m"
C_RED = "\033[91m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_BLUE = "\033[94m"
C_MAGENTA = "\033[95m"
C_CYAN = "\033[96m"
C_WHITE = "\033[97m"

# Background Badges
BG_CYAN = "\033[46m"
BG_GREEN = "\033[42m"
BG_MAGENTA = "\033[45m"

# Style Resets
OFF_BOLD = "\033[22;39m"
OFF_ITALIC = "\033[23;39m"
OFF_UNDERLINE = "\033[24m"

# Terminal Screen Buffer & Cursor Controls
ALT_SCREEN_ENTER = "\033[?1049h"
ALT_SCREEN_EXIT = "\033[?1049l"
CURSOR_HOME = "\033[H"
CLEAR_FROM_HOME = "\033[J"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"
