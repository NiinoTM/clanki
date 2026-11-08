import html
import json
import re
import sys
from typing import Any, Optional
import unicodedata
import requests

ANKI_URL = "http://127.0.0.1:8765"


def anki(action: str, suppress_error: bool = False, **params: Any) -> Optional[Any]:
  payload = {"action": action, "version": 6, "params": params}
  try:
    response = requests.post(ANKI_URL, json=payload, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
      if not suppress_error:
        print(f"\n⚠️  AnkiConnect error on '{action}': {data['error']}", file=sys.stderr)
      return None
    return data.get("result")
  except requests.exceptions.ConnectionError:
    if not suppress_error:
      print(
          "\n❌ Could not connect to AnkiConnect at 127.0.0.1:8765."
          "\nEnsure the Anki desktop application is open and AnkiConnect is installed.",
          file=sys.stderr,
      )
    return None
  except requests.exceptions.RequestException as err:
    if not suppress_error:
      print(f"\n❌ Network error: {err}", file=sys.stderr)
    return None


# ANSI Terminal Formatting Palette
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


def str_display_width(s: str) -> int:
  # Compute visual terminal cell width (ignoring ANSI codes & handling CJK characters like 汉语)
  visible = re.sub(r"\033\[[0-9;]*m", "", s)
  return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in visible)


def pad_display(s: str, target_width: int) -> str:
  current_width = str_display_width(s)
  return s + " " * max(0, target_width - current_width)


def get_deck_stats(deck_names: list[str]) -> dict[str, dict[str, int]]:
  stats: dict[str, dict[str, int]] = {
      d: {"new": 0, "learn": 0, "due": 0, "total": 0} for d in deck_names
  }

  # Attempt 1: Native getDeckStats (fastest when Anki is on the Deck Browser screen)
  raw = anki("getDeckStats", suppress_error=True, decks=deck_names)
  if isinstance(raw, dict) and raw:
    for _, info in raw.items():
      if isinstance(info, dict) and "name" in info:
        stats[info["name"]] = {
            "new": int(info.get("new_count", 0)),
            "learn": int(info.get("learn_count", 0)),
            "due": int(info.get("review_count", 0)),
            "total": int(info.get("total_in_deck", 0)),
        }
    return stats

  # Attempt 2: Resilient batch search query fallback via 'multi'
  # Collects new, learn, due, and total card counts to detect empty ghost decks
  actions = []
  for d in deck_names:
    safe_name = d.replace('"', '\\"')
    actions.append({"action": "findCards", "params": {"query": f'deck:"{safe_name}" is:new'}})
    actions.append({"action": "findCards", "params": {"query": f'deck:"{safe_name}" is:learn'}})
    actions.append({"action": "findCards", "params": {"query": f'deck:"{safe_name}" is:due -is:new -is:learn'}})
    actions.append({"action": "findCards", "params": {"query": f'deck:"{safe_name}"'}})

  results = anki("multi", suppress_error=True, actions=actions)
  if isinstance(results, list) and len(results) == len(deck_names) * 4:
    for i, d in enumerate(deck_names):
      new_cards = results[i * 4]
      learn_cards = results[i * 4 + 1]
      due_cards = results[i * 4 + 2]
      total_cards = results[i * 4 + 3]
      stats[d] = {
          "new": len(new_cards) if isinstance(new_cards, list) else 0,
          "learn": len(learn_cards) if isinstance(learn_cards, list) else 0,
          "due": len(due_cards) if isinstance(due_cards, list) else 0,
          "total": len(total_cards) if isinstance(total_cards, list) else 0,
      }

  return stats


def select_deck() -> Optional[str]:
  # 1. Allow passing deck name directly or displaying help
  if len(sys.argv) > 1:
    arg = " ".join(sys.argv[1:]).strip()
    if arg in ["-h", "--help", "help"]:
      print(f"\n{BOLD}{C_CYAN}clanki{RESET} - Minimalist Terminal Reviewer for Anki\n")
      print(f"{BOLD}Usage:{RESET}")
      print(f"  ank                 Interactive deck selection and study session")
      print(f"  ank <deck_name>     Directly launch review for <deck_name>")
      print(f"  ank -h, --help      Display this help menu\n")
      return None
    return arg

  # Subdecks hidden by default per user preference
  show_subdecks = False

  # Navigate Anki back to the main deck browser so the scheduler unlocks tree stats
  anki("guiDeckBrowser", suppress_error=True)

  while True:
    decks = anki("deckNames")
    if not decks:
      print(f"\n{C_RED}❌ No decks found or failed to query Anki.{RESET}")
      return None

    stats = get_deck_stats(decks)

    # Filter out empty orphan/ghost decks (0 total cards and no children with cards)
    has_any_total = any(st.get("total", 0) > 0 for st in stats.values())
    if has_any_total:
      valid_decks = [
          d for d in decks
          if stats.get(d, {}).get("total", 0) > 0
          or any(child.startswith(d + "::") and stats.get(child, {}).get("total", 0) > 0 for child in decks)
      ]
    else:
      valid_decks = decks
    valid_decks = sorted(valid_decks)

    # Build hierarchical tree list
    display_items: list[tuple[str, str, int]] = []
    for name in valid_decks:
      parts = name.split("::")
      depth = len(parts) - 1
      short_name = parts[-1]

      # If subdecks are hidden, skip non-root decks
      if depth > 0 and not show_subdecks:
        continue

      display_items.append((name, short_name, depth))

    # Header with column labels matching Anki Desktop (New, Learn, Due)
    print(f"\n{BOLD}{C_MAGENTA}╔{'═' * 66}╗")
    header_title = pad_display(" 📚 DECKS", 39)
    header_counts = (
        f"{BOLD}{C_BLUE}{'New':>7}{RESET}  "
        f"{BOLD}{C_RED}{'Learn':>7}{RESET}  "
        f"{BOLD}{C_GREEN}{'Due':>7}{RESET}"
    )
    print(f"║ {header_title}{header_counts} {C_MAGENTA}║")
    print(f"╚{'═' * 66}╝{RESET}")

    selectable_map: dict[int, str] = {}
    current_idx = 1

    for full_name, short_name, depth in display_items:
      selectable_map[current_idx] = full_name
      st = stats.get(full_name, {"new": 0, "learn": 0, "due": 0})

      # Format tree indentation & branch connectors with bold deck names
      if depth == 0:
        has_children = any(d.startswith(full_name + "::") for d in valid_decks)
        icon = "📁 " if has_children else "📄 "
        if not show_subdecks and has_children:
          child_count = sum(1 for d in valid_decks if d.startswith(full_name + "::"))
          name_display = f"{icon}{BOLD}{short_name}{RESET} {DIM}(+{child_count} subdecks){RESET}"
        else:
          name_display = f"{icon}{BOLD}{short_name}{RESET}"
        prefix = f" {BOLD}{C_CYAN}[{current_idx:2d}]{RESET} {name_display}"
      else:
        parent_prefix = full_name.rsplit("::", 1)[0]
        siblings = [
            d for d in valid_decks
            if d.startswith(parent_prefix + "::") and len(d.split("::")) - 1 == depth
        ]
        is_last = (full_name == siblings[-1]) if siblings else True
        branch = "└─ " if is_last else "├─ "
        indent = "    " * depth
        prefix = f"{indent}{C_DIM}{branch}{RESET}{BOLD}{C_CYAN}[{current_idx:2d}]{RESET} {BOLD}{short_name}{RESET}"

      # Format counts: non-zero numbers are highlighted; zeroes are dimmed
      new_val = st["new"]
      learn_val = st["learn"]
      due_val = st["due"]

      new_str = f"{BOLD}{C_BLUE}{new_val:>7d}{RESET}" if new_val > 0 else f"{DIM}{'0':>7}{RESET}"
      learn_str = f"{BOLD}{C_RED}{learn_val:>7d}{RESET}" if learn_val > 0 else f"{DIM}{'0':>7}{RESET}"
      due_str = f"{BOLD}{C_GREEN}{due_val:>7d}{RESET}" if due_val > 0 else f"{DIM}{'0':>7}{RESET}"

      left_col = pad_display(prefix, 38)
      print(f"{left_col}{new_str}  {learn_str}  {due_str}")
      current_idx += 1

    sub_status = f"{C_GREEN}Shown{RESET}" if show_subdecks else f"{C_YELLOW}Hidden{RESET}"
    print(f"{C_MAGENTA}{'─' * 66}{RESET}")
    print(f" {BOLD}[s]{RESET} Toggle Subdecks ({sub_status})   {BOLD}[r]{RESET} Refresh   {BOLD}[q]{RESET} Quit")
    print(f"{C_MAGENTA}{'─' * 66}{RESET}")

    choice = input(f"\n{BOLD}Select deck number or action:{RESET} ").strip().lower()
    if choice in ["q", "quit", "exit"]:
      return None
    if choice in ["s", "sub", "toggle"]:
      show_subdecks = not show_subdecks
      continue
    if choice in ["r", "refresh"]:
      continue
    if choice.isdigit():
      num = int(choice)
      if num in selectable_map:
        return selectable_map[num]
    print(f"{C_RED}Invalid input. Enter 1-{len(selectable_map)}, 's', 'r', or 'q'.{RESET}")


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
