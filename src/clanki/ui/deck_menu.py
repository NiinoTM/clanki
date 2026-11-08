import re
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
        print(f"\n{BOLD}{C_MAGENTA}╔{'═' * 66}╗")
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

        raw_choice = input(f"\n{BOLD}Select deck number or action:{RESET} ").strip().lower()
        choice = re.sub(r"\033\[[0-9;]*[a-zA-Z~]", "", raw_choice).strip()

        if not choice:
            return (None, "refresh")
        if choice in ["q", "quit", "exit"]:
            return (None, "quit")
        if choice in ["s", "sub", "toggle"]:
            self.show_subdecks = not self.show_subdecks
            return (None, "toggle")
        if choice in ["r", "refresh"]:
            return (None, "refresh")

        digits = re.findall(r"\d+", choice)
        if digits:
            num = int(digits[0])
            if num in selectable_map:
                return (selectable_map[num], "select")

        print(f"{C_RED}Invalid input. Enter 1-{len(selectable_map)}, 's', 'r', or 'q'.{RESET}")
        return (None, "invalid")
