from typing import Optional, Tuple
from clanki.core.models import Ease
from clanki.ui.html import clean_html, extract_answer
from clanki.ui.theme import (
    BG_CYAN, BG_GREEN, BOLD, C_BLACK, C_CYAN, C_DIM, C_GREEN, C_MAGENTA, C_RED, C_YELLOW, DIM, RESET
)

import sys
from clanki.ui.display import clear_screen
from clanki.ui.theme import CURSOR_SHOW

class ReviewerUI:
    def show_question(self, deck_name: str, question_html: str) -> Tuple[str, str]:
        clear_screen()
        print(f"{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}")

        clean_q = clean_html(question_html)
        print(f"\n{BG_CYAN}{C_BLACK}{BOLD} ❓ QUESTION {RESET}")
        print(f"{C_CYAN}{'─' * 62}{RESET}")
        print(clean_q)
        print(f"{C_CYAN}{'─' * 62}{RESET}")

        prompt = f"\n{DIM}[Press ENTER to reveal answer, 'e' to edit, 'q' to return]{RESET}: "
        sys.stdout.write(CURSOR_SHOW)
        sys.stdout.flush()
        user_input = input(prompt).strip().lower()

        if user_input in ["q", "quit", "exit"]:
            return clean_q, "quit"
        if user_input in ["e", "edit"]:
            return clean_q, "edit"
        return clean_q, "reveal"

    def show_answer(self, deck_name: str, clean_question: str, answer_html: str) -> Tuple[Optional[Ease], str]:
        clear_screen()
        print(f"{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}")

        print(f"\n{BG_CYAN}{C_BLACK}{BOLD} ❓ QUESTION {RESET}")
        print(f"{C_CYAN}{'─' * 62}{RESET}")
        print(clean_question)
        print(f"{C_CYAN}{'─' * 62}{RESET}")

        clean_a = extract_answer(answer_html, clean_question)
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
            f"{DIM}[e: Edit  q: Return to decks]{RESET}: "
        )
        sys.stdout.write(CURSOR_SHOW)
        sys.stdout.flush()
        user_input = input(rating_prompt).strip().lower()

        if user_input in ["1", "2", "3", "4"]:
            return Ease(int(user_input)), "rate"
        if user_input in ["e", "edit"]:
            return None, "edit"
        return None, "quit"

    def show_session_summary(self, deck_name: str, cards_reviewed: int) -> None:
        clear_screen()
        print(f"{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}\n")
        if cards_reviewed == 0:
            print(f"{BOLD}{C_GREEN}🎉 No cards currently due in '{deck_name}'!{RESET}")
        else:
            print(f"{BOLD}{C_GREEN}🎉 All due cards finished in '{deck_name}'! ({cards_reviewed} reviewed){RESET}")
        sys.stdout.write(CURSOR_SHOW)
        sys.stdout.flush()
        input(f"\n{DIM}[Press ENTER to return to decks]{RESET}")

    def show_review_launch_error(self, deck_name: str) -> None:
        clear_screen()
        print(f"{C_RED}⚠️  Could not launch review session for '{deck_name}'.{RESET}")
        sys.stdout.write(CURSOR_SHOW)
        sys.stdout.flush()
        input(f"\n{DIM}[Press ENTER to return to decks]{RESET}")
