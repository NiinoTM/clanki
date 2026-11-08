from typing import Optional, Tuple
from clanki.core.models import Ease
from clanki.ui.html import clean_html, extract_answer
from clanki.ui.theme import (
    BG_CYAN, BG_GREEN, BOLD, C_BLACK, C_CYAN, C_DIM, C_GREEN, C_MAGENTA, C_RED, C_YELLOW, DIM, RESET
)

class ReviewerUI:
    def show_active_deck_banner(self, deck_name: str) -> None:
        print(f"\n{BOLD}{C_MAGENTA}📖 ACTIVE DECK:{RESET} {BOLD}{deck_name}{RESET}")

    def show_question(self, question_html: str) -> Tuple[str, bool]:
        clean_q = clean_html(question_html)
        print(f"\n{BG_CYAN}{C_BLACK}{BOLD} ❓ QUESTION {RESET}")
        print(f"{C_CYAN}{'─' * 62}{RESET}")
        print(clean_q)
        print(f"{C_CYAN}{'─' * 62}{RESET}")

        prompt = f"\n{DIM}[Press ENTER to reveal answer, or 'q' to return to decks]{RESET}: "
        user_input = input(prompt).strip().lower()
        quit_requested = user_input in ["q", "quit", "exit"]
        return clean_q, quit_requested

    def show_answer(self, answer_html: str, clean_question: str) -> Optional[Ease]:
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
            print(f"\n{BOLD}{C_GREEN}🎉 No cards currently due in '{deck_name}'!{RESET}")
        else:
            print(f"\n{BOLD}{C_GREEN}🎉 All due cards finished in '{deck_name}'! ({cards_reviewed} reviewed){RESET}")
        input(f"\n{DIM}[Press ENTER to return to decks]{RESET}")

    def show_review_launch_error(self, deck_name: str) -> None:
        print(f"\n{C_RED}⚠️  Could not launch review session for '{deck_name}'.{RESET}")
        input(f"\n{DIM}[Press ENTER to return to decks]{RESET}")

    def show_returning(self) -> None:
        print(f"\n{C_YELLOW}Returning to deck menu...{RESET}")
