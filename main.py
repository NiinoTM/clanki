import html
import json
import re
import sys
from typing import Any, Optional
import requests

ANKI_URL = "http://127.0.0.1:8765"


def anki(action: str, **params: Any) -> Optional[Any]:
  payload = {"action": action, "version": 6, "params": params}
  try:
    response = requests.post(ANKI_URL, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
      print(f"\n⚠️  AnkiConnect error on '{action}': {data['error']}", file=sys.stderr)
      return None
    return data.get("result")
  except requests.exceptions.ConnectionError:
    print(
        "\n❌ Could not connect to AnkiConnect at 127.0.0.1:8765."
        "\nEnsure the Anki desktop application is open and AnkiConnect is installed.",
        file=sys.stderr,
    )
    return None
  except requests.exceptions.RequestException as err:
    print(f"\n❌ Network error: {err}", file=sys.stderr)
    return None


# ANSI Terminal Formatting Palette
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
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

# Style resets for specific attributes without wiping all styles
OFF_BOLD = "\033[22;39m"
OFF_ITALIC = "\033[23;39m"
OFF_UNDERLINE = "\033[24m"


def clean_html(raw_html: str) -> str:
  # 1. Remove JavaScript and CSS completely
  clean = re.sub(
      r"<(script|style).*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE
  )

  # 2. Convert structural HTML tags to newlines & bullet points
  clean = re.sub(r"<(br|p|div|h[1-6])[^>]*>", "\n", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</(p|div|h[1-6])>", "\n", clean, flags=re.IGNORECASE)
  clean = re.sub(r"<li[^>]*>", "\n  • ", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</li>", "", clean, flags=re.IGNORECASE)

  # 3. Map vanilla HTML styling tags to ANSI sequences
  # <b> / <strong> -> Bold Gold/Yellow
  clean = re.sub(r"<(b|strong)[^>]*>", f"{BOLD}{C_YELLOW}", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</(b|strong)>", OFF_BOLD, clean, flags=re.IGNORECASE)

  # <i> / <em> -> Italic Cyan
  clean = re.sub(r"<(i|em)[^>]*>", f"{ITALIC}{C_CYAN}", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</(i|em)>", OFF_ITALIC, clean, flags=re.IGNORECASE)

  # <u> / <ins> -> Underline
  clean = re.sub(r"<(u|ins)[^>]*>", UNDERLINE, clean, flags=re.IGNORECASE)
  clean = re.sub(r"</(u|ins)>", OFF_UNDERLINE, clean, flags=re.IGNORECASE)

  # <code> -> Bold Green
  clean = re.sub(r"<code[^>]*>", f"{BOLD}{C_GREEN}", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</code>", OFF_BOLD, clean, flags=re.IGNORECASE)

  # <mark> -> Reverse Video / Highlight
  clean = re.sub(r"<mark[^>]*>", f"\033[7;33m", clean, flags=re.IGNORECASE)
  clean = re.sub(r"</mark>", "\033[27;39m", clean, flags=re.IGNORECASE)

  # 4. Strip any remaining unsupported HTML tags
  clean = re.sub(r"<[^>]+>", "", clean)

  # 5. Decode HTML entities (&lt;, &gt;, &amp;, &quot;, &#39;, etc.)
  clean = html.unescape(clean)

  # 6. Normalize spacing while preserving paragraph gaps
  clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", clean)
  return clean.strip() + RESET


def select_deck() -> Optional[str]:
  # 1. Allow passing deck name directly via CLI: python3 main.py "My Deck"
  if len(sys.argv) > 1:
    return " ".join(sys.argv[1:]).strip()

  # 2. Query Anki for all available decks
  decks = anki("deckNames")
  if not decks:
    return None

  decks = sorted(decks)
  print(f"\n{BOLD}{C_MAGENTA}╔{'═' * 52}╗")
  print(f"║ 📚 AVAILABLE DECKS{' ' * 33}║")
  print(f"╚{'═' * 52}╝{RESET}")
  for idx, name in enumerate(decks, start=1):
    print(f"  {BOLD}{C_CYAN}[{idx:2d}]{RESET} {name}")
  print(f"  {DIM}[ q] Quit{RESET}")
  print(f"{C_MAGENTA}{'─' * 54}{RESET}")

  while True:
    choice = input(f"\n{BOLD}Select deck number:{RESET} ").strip().lower()
    if choice in ["q", "quit", "exit"]:
      return None
    if choice.isdigit():
      num = int(choice)
      if 1 <= num <= len(decks):
        return decks[num - 1]
    print(f"{C_RED}Invalid choice. Enter 1-{len(decks)} or 'q'.{RESET}")


def review_deck(deck_name: str) -> None:
  # Programmatically instruct Anki to open and review this deck
  result = anki("guiDeckReview", name=deck_name)
  if result is False:
    print(f"\n{C_RED}⚠️  Could not launch review session for '{deck_name}'.{RESET}")
    return

  print(f"\n{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}")

  while True:
    card = anki("guiCurrentCard")
    if not card:
      print(f"\n{BOLD}{C_GREEN}🎉 All due cards finished in '{deck_name}'!{RESET}")
      break

    # Question Banner (Cyan)
    clean_q = clean_html(card["question"])
    # Eliminate question repetition: Anki's default template embeds {{FrontSide}} in card["answer"]
    raw_answer = card["answer"]
    split_parts = re.split(
        r"<hr\s*id=[\"']?answer[\"']?[^>]*>", raw_answer, flags=re.IGNORECASE
    )
    if len(split_parts) > 1:
      clean_a = clean_html(split_parts[1])
    else:
      clean_a = clean_html(raw_answer)
      if clean_a.startswith(clean_q):
        clean_a = clean_a[len(clean_q):].lstrip()
    # Question Header (Filled Badge + Clean Solid Rule)
    print(f"\n{BG_CYAN}{C_BLACK}{BOLD} ❓ QUESTION {RESET}")
    print(f"{C_CYAN}{'─' * 62}{RESET}")
    print(clean_q)
    print(f"{C_CYAN}{'─' * 62}{RESET}")

    prompt = f"\n{DIM}[Press ENTER to reveal answer, or 'q' to quit]{RESET}: "
    user_input = input(prompt).strip().lower()
    if user_input in ["q", "quit", "exit"]:
      print(f"\n{C_YELLOW}Review session closed.{RESET}")
      break

    # Flip the card in Anki's state machine before grading
    anki("guiShowAnswer")

    # Answer Header (Filled Badge + Clean Solid Rule)
    print(f"\n{BG_GREEN}{C_BLACK}{BOLD} 💡 ANSWER {RESET}")
    print(f"{C_GREEN}{'─' * 62}{RESET}")
    print(clean_a)
    print(f"{C_GREEN}{'─' * 62}{RESET}")

    rating_prompt = (
        f"\n{BOLD}Rating:{RESET} "
        f"{C_RED}[1] Again{RESET}  "
        f"{C_YELLOW}[2] Hard{RESET}  "
        f"{C_GREEN}[3] Good{RESET}  "
        f"{C_CYAN}[4] Easy{RESET}  "
        f"{DIM}[q: Quit]{RESET}: "
    )
    ease = input(rating_prompt).strip().lower()
    if ease in ["1", "2", "3", "4"]:
      anki("guiAnswerCard", ease=int(ease))
    elif ease in ["q", "quit", "exit"]:
      print(f"\n{C_YELLOW}Review session closed.{RESET}")
      break
    else:
      print(f"{C_DIM}Invalid input, skipping grading...{RESET}")


def main():
  deck = select_deck()
  if deck:
    review_deck(deck)


if __name__ == "__main__":
  main()
