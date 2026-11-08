#!/usr/bin/env python3
"""Automated migration script to transition clanki from a monolithic file
into a modular, layered, world-class architecture.
"""

from pathlib import Path
import shutil
import sys

BASE_DIR = Path(__file__).resolve().parent

# --- File Contents Map ---

FILES = {
    "pyproject.toml": """[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "clanki"
version = "0.2.0"
description = "Minimalist Terminal Reviewer for Anki"
readme = "README.md"
requires-python = ">=3.9"
dependencies = [
    "requests>=2.28.0",
]

[project.scripts]
ank = "clanki.cli:main"
clanki = "clanki.cli:main"
""",

    "src/clanki/__init__.py": """\"\"\"clanki - Minimalist Terminal Reviewer for Anki.\"\"\"

__version__ = "0.2.0"
""",

    "src/clanki/__main__.py": """from clanki.cli import main

if __name__ == "__main__":
    main()
""",

    "src/clanki/ui/theme.py": """# ANSI Terminal Formatting Palette & Style Tokens

RESET = "\\033[0m"
BOLD = "\\033[1m"
DIM = "\\033[2m"
C_DIM = "\\033[2m"
ITALIC = "\\033[3m"
UNDERLINE = "\\033[4m"

# Foreground Colors
C_BLACK = "\\033[30m"
C_RED = "\\033[91m"
C_GREEN = "\\033[92m"
C_YELLOW = "\\033[93m"
C_BLUE = "\\033[94m"
C_MAGENTA = "\\033[95m"
C_CYAN = "\\033[96m"
C_WHITE = "\\033[97m"

# Background Badges
BG_CYAN = "\\033[46m"
BG_GREEN = "\\033[42m"
BG_MAGENTA = "\\033[45m"

# Style Resets
OFF_BOLD = "\\033[22;39m"
OFF_ITALIC = "\\033[23;39m"
OFF_UNDERLINE = "\\033[24m"
""",

    "src/clanki/ui/display.py": """import re
import unicodedata

def str_display_width(s: str) -> int:
    \"\"\"Compute visual terminal cell width (ignoring ANSI codes & handling CJK characters).\"\"\"
    visible = re.sub(r"\\033\\[[0-9;]*[a-zA-Z~]", "", s)
    return sum(2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1 for ch in visible)

def pad_display(s: str, target_width: int) -> str:
    \"\"\"Pad string with spaces to reach visual target width in terminal cells.\"\"\"
    current_width = str_display_width(s)
    return s + " " * max(0, target_width - current_width)
""",

    "src/clanki/ui/html.py": """import html
import re
from clanki.ui.theme import (
    BOLD, C_CYAN, C_GREEN, C_YELLOW, OFF_BOLD, OFF_ITALIC, OFF_UNDERLINE, RESET, UNDERLINE
)

def clean_html(raw_html: str) -> str:
    \"\"\"Convert card HTML markup into formatted ANSI terminal text.\"\"\"
    # 1. Remove JavaScript and CSS completely
    clean = re.sub(r"<(script|style).*?</\\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)

    # 2. Convert structural HTML tags to newlines & bullet points
    clean = re.sub(r"<(br|p|div|h[1-6])[^>]*>", "\\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</(p|div|h[1-6])>", "\\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<li[^>]*>", "\\n  • ", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</li>", "", clean, flags=re.IGNORECASE)

    # 3. Map vanilla HTML styling tags to ANSI sequences
    clean = re.sub(r"<(b|strong)[^>]*>", f"{BOLD}{C_YELLOW}", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</(b|strong)>", OFF_BOLD, clean, flags=re.IGNORECASE)

    clean = re.sub(r"<(i|em)[^>]*>", f"{ITALIC}{C_CYAN}", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</(i|em)>", OFF_ITALIC, clean, flags=re.IGNORECASE)

    clean = re.sub(r"<(u|ins)[^>]*>", UNDERLINE, clean, flags=re.IGNORECASE)
    clean = re.sub(r"</(u|ins)>", OFF_UNDERLINE, clean, flags=re.IGNORECASE)

    clean = re.sub(r"<code[^>]*>", f"{BOLD}{C_GREEN}", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</code>", OFF_BOLD, clean, flags=re.IGNORECASE)

    clean = re.sub(r"<mark[^>]*>", "\\033[7;33m", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</mark>", "\\033[27;39m", clean, flags=re.IGNORECASE)

    # 4. Strip any remaining unsupported HTML tags
    clean = re.sub(r"<[^>]+>", "", clean)

    # 5. Decode HTML entities (&lt;, &gt;, &amp;, &quot;, &#39;, etc.)
    clean = html.unescape(clean)

    # 6. Normalize spacing while preserving paragraph gaps
    clean = re.sub(r"\\n\\s*\\n\\s*\\n+", "\\n\\n", clean)
    return clean.strip() + RESET

def extract_answer(raw_answer: str, clean_question: str) -> str:
    \"\"\"Extract answer side, eliminating question repetition from {{FrontSide}} templates.\"\"\"
    split_parts = re.split(r"<hr\\s*id=[\"']?answer[\"']?[^>]*>", raw_answer, flags=re.IGNORECASE)
    if len(split_parts) > 1:
        clean_a = clean_html(split_parts[1])
    else:
        clean_a = clean_html(raw_answer)
        if clean_a.startswith(clean_question):
            clean_a = clean_a[len(clean_question):].lstrip()
    return clean_a
""",

    "src/clanki/core/models.py": """from dataclasses import dataclass
from enum import IntEnum

class Ease(IntEnum):
    AGAIN = 1
    HARD = 2
    GOOD = 3
    EASY = 4

@dataclass(frozen=True)
class DeckStats:
    new: int = 0
    learn: int = 0
    due: int = 0
    total: int = 0

@dataclass(frozen=True)
class DeckNode:
    full_name: str
    short_name: str
    depth: int
    stats: DeckStats
    has_children: bool
    child_count: int

@dataclass(frozen=True)
class Card:
    id: int
    question: str
    answer: str
""",

    "src/clanki/core/tree.py": """from typing import Dict, List
from clanki.core.models import DeckNode, DeckStats

def filter_valid_decks(decks: List[str], stats: Dict[str, DeckStats]) -> List[str]:
    \"\"\"Prune empty orphan/ghost decks unless they or their descendants contain cards.\"\"\"
    has_any_total = any(st.total > 0 for st in stats.values())
    if not has_any_total:
        return sorted(decks)

    valid = [
        d for d in decks
        if stats.get(d, DeckStats()).total > 0
        or any(child.startswith(d + "::") and stats.get(child, DeckStats()).total > 0 for child in decks)
    ]
    return sorted(valid)

def build_deck_tree(
    valid_decks: List[str],
    stats: Dict[str, DeckStats],
    show_subdecks: bool = False
) -> List[DeckNode]:
    \"\"\"Convert deck paths into hierarchical DeckNode structures.\"\"\"
    nodes: List[DeckNode] = []
    for name in valid_decks:
        parts = name.split("::")
        depth = len(parts) - 1
        short_name = parts[-1]

        if depth > 0 and not show_subdecks:
            continue

        has_children = any(d.startswith(name + "::") for d in valid_decks)
        child_count = sum(1 for d in valid_decks if d.startswith(name + "::")) if has_children else 0
        st = stats.get(name, DeckStats())

        nodes.append(DeckNode(
            full_name=name,
            short_name=short_name,
            depth=depth,
            stats=st,
            has_children=has_children,
            child_count=child_count,
        ))
    return nodes
""",

    "src/clanki/client/anki_connect.py": """import sys
from typing import Any, Dict, List, Optional
import requests
from clanki.core.models import Card, DeckStats, Ease

DEFAULT_ANKI_URL = "http://127.0.0.1:8765"

class AnkiConnectClient:
    def __init__(self, url: str = DEFAULT_ANKI_URL, timeout: int = 5):
        self.url = url
        self.timeout = timeout

    def request(self, action: str, suppress_error: bool = False, **params: Any) -> Optional[Any]:
        payload = {"action": action, "version": 6, "params": params}
        try:
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            if data.get("error"):
                if not suppress_error:
                    print(f"\\n⚠️  AnkiConnect error on '{action}': {data['error']}", file=sys.stderr)
                return None
            return data.get("result")
        except requests.exceptions.ConnectionError:
            if not suppress_error:
                print(
                    f"\\n❌ Could not connect to AnkiConnect at {self.url}."
                    "\\nEnsure Anki desktop is open and AnkiConnect is installed.",
                    file=sys.stderr,
                )
            return None
        except requests.exceptions.RequestException as err:
            if not suppress_error:
                print(f"\\n❌ Network error: {err}", file=sys.stderr)
            return None

    def is_alive(self) -> bool:
        return self.request("version", suppress_error=True) is not None

    def get_deck_names(self) -> List[str]:
        res = self.request("deckNames")
        return res if isinstance(res, list) else []

    def navigate_browser(self) -> None:
        self.request("guiDeckBrowser", suppress_error=True)

    def get_deck_stats(self, deck_names: List[str]) -> Dict[str, DeckStats]:
        stats: Dict[str, DeckStats] = {d: DeckStats() for d in deck_names}
        if not deck_names:
            return stats

        # Attempt 1: Native getDeckStats (fastest)
        raw = self.request("getDeckStats", suppress_error=True, decks=deck_names)
        if isinstance(raw, dict) and raw:
            for _, info in raw.items():
                if isinstance(info, dict) and "name" in info:
                    stats[info["name"]] = DeckStats(
                        new=int(info.get("new_count", 0)),
                        learn=int(info.get("learn_count", 0)),
                        due=int(info.get("review_count", 0)),
                        total=int(info.get("total_in_deck", 0)),
                    )
            return stats

        # Attempt 2: Resilient batch multi query fallback
        actions = []
        for d in deck_names:
            safe = d.replace('"', '\\\\"')
            actions.append({"action": "findCards", "params": {"query": f'deck:"{safe}" is:new'}})
            actions.append({"action": "findCards", "params": {"query": f'deck:"{safe}" is:learn'}})
            actions.append({"action": "findCards", "params": {"query": f'deck:"{safe}" is:due -is:new -is:learn'}})
            actions.append({"action": "findCards", "params": {"query": f'deck:"{safe}"'}})

        results = self.request("multi", suppress_error=True, actions=actions)
        if isinstance(results, list) and len(results) == len(deck_names) * 4:
            for i, d in enumerate(deck_names):
                new_cards = results[i * 4]
                learn_cards = results[i * 4 + 1]
                due_cards = results[i * 4 + 2]
                total_cards = results[i * 4 + 3]
                stats[d] = DeckStats(
                    new=len(new_cards) if isinstance(new_cards, list) else 0,
                    learn=len(learn_cards) if isinstance(learn_cards, list) else 0,
                    due=len(due_cards) if isinstance(due_cards, list) else 0,
                    total=len(total_cards) if isinstance(total_cards, list) else 0,
                )
        return stats

    def start_deck_review(self, deck_name: str) -> bool:
        res = self.request("guiDeckReview", name=deck_name)
        return res is not False

    def get_current_card(self) -> Optional[Card]:
        data = self.request("guiCurrentCard", suppress_error=True)
        if not isinstance(data, dict) or "question" not in data:
            return None
        return Card(
            id=int(data.get("cardId", 0)),
            question=data.get("question", ""),
            answer=data.get("answer", "")
        )

    def show_answer(self) -> None:
        self.request("guiShowAnswer")

    def answer_card(self, ease: Ease) -> None:
        self.request("guiAnswerCard", ease=int(ease))
""",

    "src/clanki/client/process.py": """import atexit
import os
import shutil
import signal
import subprocess
import sys
import time
from typing import Any, Optional
from clanki.client.anki_connect import AnkiConnectClient
from clanki.ui.theme import C_CYAN, C_GREEN, C_RED, RESET

class AnkiProcessManager:
    \"\"\"Manages lifecycle of headless Anki desktop subprocess.\"\"\"

    def __init__(self, client: Optional[AnkiConnectClient] = None):
        self.client = client or AnkiConnectClient()
        self._proc: Optional[subprocess.Popen] = None
        self._registered = False

    def ensure_running(self, timeout: float = 15.0) -> bool:
        # Reuse existing desktop or headless instance
        if self.client.is_alive():
            return True

        anki_bin = shutil.which("anki")
        if not anki_bin:
            print(
                f"\\n{C_RED}❌ 'anki' executable not found in PATH.{RESET}\\n"
                "Ensure Anki desktop is installed and accessible via your PATH.",
                file=sys.stderr,
            )
            return False

        print(
            f"\\n{C_CYAN}🔄 Starting headless Anki session in background (QT_QPA_PLATFORM=offscreen)...{RESET}",
            end="",
            flush=True,
        )

        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "offscreen"

        try:
            self._proc = subprocess.Popen(
                [anki_bin],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as err:
            print(f"\\n{C_RED}❌ Failed to start Anki subprocess: {err}{RESET}", file=sys.stderr)
            return False

        self._register_hooks()

        start_time = time.time()
        while time.time() - start_time < timeout:
            if self._proc.poll() is not None:
                print(
                    f"\\n{C_RED}❌ Headless Anki exited unexpectedly (exit code {self._proc.returncode}).{RESET}",
                    file=sys.stderr,
                )
                self._proc = None
                return False

            if self.client.is_alive():
                print(f" {C_GREEN}ready!{RESET}")
                return True

            time.sleep(0.4)

        print(f"\\n{C_RED}❌ Timed out waiting for AnkiConnect at {self.client.url}.{RESET}", file=sys.stderr)
        self.shutdown()
        return False

    def shutdown(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
            self._proc = None

    def _register_hooks(self) -> None:
        if not self._registered:
            atexit.register(self.shutdown)
            signal.signal(signal.SIGTERM, self._signal_handler)
            signal.signal(signal.SIGINT, self._signal_handler)
            self._registered = True

    def _signal_handler(self, signum: int, frame: Any) -> None:
        self.shutdown()
        sys.exit(0)
""",

    "src/clanki/ui/deck_menu.py": """import re
from typing import Dict, List, Optional, Tuple
from clanki.core.models import DeckNode
from clanki.ui.display import pad_display
from clanki.ui.theme import (
    BOLD, C_BLUE, C_CYAN, C_DIM, C_GREEN, C_MAGENTA, C_RED, C_YELLOW, DIM, RESET
)

class DeckMenuUI:
    def __init__(self):
        self.show_subdecks = False

    def render_and_select(self, nodes: List[DeckNode], valid_decks: List[str]) -> Tuple[Optional[str], str]:
        print(f"\\n{BOLD}{C_MAGENTA}╔{'═' * 66}╗")
        header_title = pad_display(" 📚 DECKS", 39)
        header_counts = (
            f"{BOLD}{C_BLUE}{'New':>7}{RESET}  "
            f"{BOLD}{C_RED}{'Learn':>7}{RESET}  "
            f"{BOLD}{C_GREEN}{'Due':>7}{RESET}"
        )
        print(f"║ {header_title}{header_counts} {C_MAGENTA}║")
        print(f"╚{'═' * 66}╝{RESET}")

        selectable_map: Dict[int, str] = {}
        current_idx = 1

        for node in nodes:
            selectable_map[current_idx] = node.full_name
            st = node.stats

            if node.depth == 0:
                icon = "📁 " if node.has_children else "📄 "
                if not self.show_subdecks and node.has_children:
                    name_display = f"{icon}{BOLD}{node.short_name}{RESET} {DIM}(+{node.child_count} subdecks){RESET}"
                else:
                    name_display = f"{icon}{BOLD}{node.short_name}{RESET}"
                prefix = f" {BOLD}{C_CYAN}[{current_idx:2d}]{RESET} {name_display}"
            else:
                parent_prefix = node.full_name.rsplit("::", 1)[0]
                siblings = [
                    d for d in valid_decks
                    if d.startswith(parent_prefix + "::") and len(d.split("::")) - 1 == node.depth
                ]
                is_last = (node.full_name == siblings[-1]) if siblings else True
                branch = "└─ " if is_last else "├─ "
                indent = "    " * node.depth
                prefix = f"{indent}{C_DIM}{branch}{RESET}{BOLD}{C_CYAN}[{current_idx:2d}]{RESET} {BOLD}{node.short_name}{RESET}"

            new_str = f"{BOLD}{C_BLUE}{st.new:>7d}{RESET}" if st.new > 0 else f"{DIM}{'0':>7}{RESET}"
            learn_str = f"{BOLD}{C_RED}{st.learn:>7d}{RESET}" if st.learn > 0 else f"{DIM}{'0':>7}{RESET}"
            due_str = f"{BOLD}{C_GREEN}{st.due:>7d}{RESET}" if st.due > 0 else f"{DIM}{'0':>7}{RESET}"

            left_col = pad_display(prefix, 38)
            print(f"{left_col}{new_str}  {learn_str}  {due_str}")
            current_idx += 1

        sub_status = f"{C_GREEN}Shown{RESET}" if self.show_subdecks else f"{C_YELLOW}Hidden{RESET}"
        print(f"{C_MAGENTA}{'─' * 66}{RESET}")
        print(f" {BOLD}[s]{RESET} Toggle Subdecks ({sub_status})   {BOLD}[r]{RESET} Refresh   {BOLD}[q]{RESET} Quit")
        print(f"{C_MAGENTA}{'─' * 66}{RESET}")

        raw_choice = input(f"\\n{BOLD}Select deck number or action:{RESET} ").strip().lower()
        choice = re.sub(r"\\033\\[[0-9;]*[a-zA-Z~]", "", raw_choice).strip()

        if not choice:
            return (None, "refresh")
        if choice in ["q", "quit", "exit"]:
            return (None, "quit")
        if choice in ["s", "sub", "toggle"]:
            self.show_subdecks = not self.show_subdecks
            return (None, "toggle")
        if choice in ["r", "refresh"]:
            return (None, "refresh")

        digits = re.findall(r"\\d+", choice)
        if digits:
            num = int(digits[0])
            if num in selectable_map:
                return (selectable_map[num], "select")

        print(f"{C_RED}Invalid input. Enter 1-{len(selectable_map)}, 's', 'r', or 'q'.{RESET}")
        return (None, "invalid")
""",

    "src/clanki/ui/reviewer.py": """from typing import Optional, Tuple
from clanki.core.models import Ease
from clanki.ui.html import clean_html, extract_answer
from clanki.ui.theme import (
    BG_CYAN, BG_GREEN, BOLD, C_BLACK, C_CYAN, C_DIM, C_GREEN, C_MAGENTA, C_RED, C_YELLOW, DIM, RESET
)

class ReviewerUI:
    def show_active_deck_banner(self, deck_name: str) -> None:
        print(f"\\n{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}")

    def show_question(self, question_html: str) -> Tuple[str, bool]:
        clean_q = clean_html(question_html)
        print(f"\\n{BG_CYAN}{C_BLACK}{BOLD} ❓ QUESTION {RESET}")
        print(f"{C_CYAN}{'─' * 62}{RESET}")
        print(clean_q)
        print(f"{C_CYAN}{'─' * 62}{RESET}")

        prompt = f"\\n{DIM}[Press ENTER to reveal answer, or 'q' to return to decks]{RESET}: "
        user_input = input(prompt).strip().lower()
        quit_requested = user_input in ["q", "quit", "exit"]
        return clean_q, quit_requested

    def show_answer(self, answer_html: str, clean_question: str) -> Optional[Ease]:
        clean_a = extract_answer(answer_html, clean_question)
        print(f"\\n{BG_GREEN}{C_BLACK}{BOLD} 💡 ANSWER {RESET}")
        print(f"{C_GREEN}{'─' * 62}{RESET}")
        print(clean_a)
        print(f"{C_GREEN}{'─' * 62}{RESET}")

        rating_prompt = (
            f"\\n{BOLD}Rating:{RESET} "
            f"{C_RED}[1] Again{RESET}  "
            f"{C_YELLOW}[2] Hard{RESET}  "
            f"{C_GREEN}[3] Good{RESET}  "
            f"{C_CYAN}[4] Easy{RESET}  "
            f"{DIM}[q: Return to decks]{RESET}: "
        )
        ease_input = input(rating_prompt).strip().lower()
        if ease_input in ["1", "2", "3", "4"]:
            return Ease(int(ease_input))
        if ease_input in ["q", "quit", "exit"]:
            return None
        print(f"{C_DIM}Invalid input, skipping grading...{RESET}")
        return None

    def show_session_summary(self, deck_name: str, cards_reviewed: int) -> None:
        if cards_reviewed == 0:
            print(f"\\n{BOLD}{C_GREEN}🎉 No cards currently due in '{deck_name}'!{RESET}")
        else:
            print(f"\\n{BOLD}{C_GREEN}🎉 All due cards finished in '{deck_name}'! ({cards_reviewed} reviewed){RESET}")
        input(f"\\n{DIM}[Press ENTER to return to decks]{RESET}")

    def show_review_launch_error(self, deck_name: str) -> None:
        print(f"\\n{C_RED}⚠️  Could not launch review session for '{deck_name}'.{RESET}")
        input(f"\\n{DIM}[Press ENTER to return to decks]{RESET}")

    def show_returning(self) -> None:
        print(f"\\n{C_YELLOW}Returning to deck menu...{RESET}")
""",

    "src/clanki/app.py": """from typing import Optional
from clanki.client.anki_connect import AnkiConnectClient
from clanki.client.process import AnkiProcessManager
from clanki.core.tree import build_deck_tree, filter_valid_decks
from clanki.ui.deck_menu import DeckMenuUI
from clanki.ui.reviewer import ReviewerUI
from clanki.ui.theme import C_RED, C_YELLOW, RESET

class AppSession:
    \"\"\"Top-level coordinator managing the review workflow and lifecycle.\"\"\"

    def __init__(self, client: Optional[AnkiConnectClient] = None, proc_mgr: Optional[AnkiProcessManager] = None):
        self.client = client or AnkiConnectClient()
        self.proc_mgr = proc_mgr or AnkiProcessManager(self.client)
        self.deck_menu_ui = DeckMenuUI()
        self.reviewer_ui = ReviewerUI()

    def run(self, initial_deck: Optional[str] = None) -> None:
        if not self.proc_mgr.ensure_running():
            return

        try:
            if initial_deck:
                self.review_deck(initial_deck)
                return

            while True:
                deck = self.select_deck()
                if not deck:
                    print(f"\\n{C_YELLOW}Exited clanki. Happy studying!{RESET}")
                    break
                self.review_deck(deck)
        finally:
            self.proc_mgr.shutdown()

    def select_deck(self) -> Optional[str]:
        while True:
            self.client.navigate_browser()
            deck_names = self.client.get_deck_names()
            if not deck_names:
                print(f"\\n{C_RED}❌ No decks found or failed to query Anki.{RESET}")
                return None

            stats = self.client.get_deck_stats(deck_names)
            valid_decks = filter_valid_decks(deck_names, stats)
            nodes = build_deck_tree(valid_decks, stats, self.deck_menu_ui.show_subdecks)

            selected, action = self.deck_menu_ui.render_and_select(nodes, valid_decks)
            if action == "quit":
                return None
            if action == "select" and selected:
                return selected

    def review_deck(self, deck_name: str) -> None:
        if not self.client.start_deck_review(deck_name):
            self.reviewer_ui.show_review_launch_error(deck_name)
            return

        self.reviewer_ui.show_active_deck_banner(deck_name)
        cards_reviewed = 0

        while True:
            card = self.client.get_current_card()
            if not card:
                self.reviewer_ui.show_session_summary(deck_name, cards_reviewed)
                break

            clean_q, quit_requested = self.reviewer_ui.show_question(card.question)
            if quit_requested:
                self.reviewer_ui.show_returning()
                break

            self.client.show_answer()
            ease = self.reviewer_ui.show_answer(card.answer, clean_q)
            if ease is not None:
                self.client.answer_card(ease)
                cards_reviewed += 1
            else:
                self.reviewer_ui.show_returning()
                break
""",

    "src/clanki/cli.py": """import sys
from clanki.app import AppSession
from clanki.ui.theme import BOLD, C_CYAN, RESET

def main() -> None:
    initial_deck = None
    if len(sys.argv) > 1:
        arg = " ".join(sys.argv[1:]).strip()
        if arg in ["-h", "--help", "help"]:
            print(f"\\n{BOLD}{C_CYAN}clanki{RESET} - Minimalist Terminal Reviewer for Anki\\n")
            print(f"{BOLD}Usage:{RESET}")
            print("  ank                 Interactive deck selection and study session")
            print("  ank <deck_name>     Directly launch review for <deck_name>")
            print("  ank -h, --help      Display this help menu\\n")
            return
        initial_deck = arg

    session = AppSession()
    session.run(initial_deck)

if __name__ == "__main__":
    main()
""",

    "main.py": """\"\"\"Backward-compatibility shim for clanki.
Original monolithic main.py has been moved to archive/main.py.
\"\"\"
from pathlib import Path
import sys

# Ensure src/ is accessible if invoked directly as `python main.py`
src_dir = str(Path(__file__).resolve().parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from clanki.cli import main

if __name__ == "__main__":
    main()
"""
}

# Add empty __init__.py files for packages
PACKAGE_DIRS = [
    "src/clanki",
    "src/clanki/core",
    "src/clanki/client",
    "src/clanki/ui",
]


def run_migration() -> None:
    print("\n🚀 Starting clanki modular architecture migration...\n")

    # 1. Archive legacy main.py
    legacy_main = BASE_DIR / "main.py"
    archive_dir = BASE_DIR / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    if legacy_main.exists() and not (archive_dir / "main.py").exists():
        shutil.copy2(legacy_main, archive_dir / "main.py")
        print(f"📦 Archived legacy main.py -> archive/main.py")

    # 2. Create package directories
    for rel_dir in PACKAGE_DIRS:
        dir_path = BASE_DIR / rel_dir
        dir_path.mkdir(parents=True, exist_ok=True)
        init_file = dir_path / "__init__.py"
        if not init_file.exists() and str(rel_dir) != "src/clanki":
            init_file.write_text('"""Subpackage initialization."""\n', encoding="utf-8")

    # 3. Write all modular files
    for rel_path, content in FILES.items():
        file_path = BASE_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        print(f"  ✅ Created: {rel_path}")

    print("\n🎉 Migration completed successfully!")
    print("\nNext steps:")
    print("  1. Run `python3 main.py` or `python3 -m clanki` to test review immediately.")
    print("  2. Run `pip install -e .` to install the `ank` and `clanki` CLI system commands.")
    print("  3. You can safely remove `restructure.py` once satisfied.")


if __name__ == "__main__":
    run_migration()