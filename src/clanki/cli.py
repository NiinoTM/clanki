from pathlib import Path
import sys

# Ensure src/ is on sys.path even if cli.py is executed directly from subdirectories
_src_dir = str(Path(__file__).resolve().parent.parent)
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from clanki.app import AppSession
from clanki.ui.theme import BOLD, C_CYAN, RESET

def main() -> None:
    initial_deck = None
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:]).strip()
        if arg in ["-h", "--help", "help"]:
            print(f"\n{BOLD}{C_CYAN}clanki{RESET} - Minimalist Terminal Reviewer for Anki\n")
            print(f"{BOLD}Usage:{RESET}")
            print("  ank                 Interactive deck selection and study session")
            print("  ank <deck_name>     Directly launch review for <deck_name>")
            print("  ank -h, --help      Display this help menu\n")
            return
        initial_deck = arg

    session = AppSession()
    session.run(initial_deck)

if __name__ == "__main__":
    main()
