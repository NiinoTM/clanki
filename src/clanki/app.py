from typing import Optional
from clanki.client.anki_connect import AnkiConnectClient
from clanki.client.process import AnkiProcessManager
from clanki.core.tree import build_deck_tree, filter_valid_decks
from clanki.ui.deck_menu import DeckMenuUI
from clanki.ui.display import TerminalScreen
from clanki.ui.editor import CardEditor
from clanki.ui.reviewer import ReviewerUI
from clanki.ui.theme import C_RED, C_YELLOW, RESET

class AppSession:
    """Top-level coordinator managing the review workflow and lifecycle."""

    def __init__(self, client: Optional[AnkiConnectClient] = None, proc_mgr: Optional[AnkiProcessManager] = None):
        self.client = client or AnkiConnectClient()
        self.editor = CardEditor()
        self.proc_mgr = proc_mgr or AnkiProcessManager(self.client)
        self.deck_menu_ui = DeckMenuUI()
        self.reviewer_ui = ReviewerUI()

    def run(self, initial_deck: Optional[str] = None) -> None:
        if not self.proc_mgr.ensure_running():
            return

        try:
            with TerminalScreen():
                if initial_deck:
                    self.review_deck(initial_deck)
                    return

                while True:
                    deck = self.select_deck()
                    if not deck:
                        break
                    self.review_deck(deck)
        finally:
            self.proc_mgr.shutdown()

        print(f"\n{C_YELLOW}Exited clanki. Happy studying!{RESET}")

    def select_deck(self) -> Optional[str]:
        while True:
            self.client.navigate_browser()
            deck_names = self.client.get_deck_names()
            if not deck_names:
                print(f"\n{C_RED}❌ No decks found or failed to query Anki.{RESET}")
                return None

            stats = self.client.get_deck_stats(deck_names)
            valid_decks = filter_valid_decks(deck_names, stats)
            nodes = build_deck_tree(valid_decks, stats, self.deck_menu_ui.show_subdecks)

            selected, action = self.deck_menu_ui.render_and_select(nodes, valid_decks)
            if action == "quit":
                return None
            if action == "select" and selected:
                return selected

    def edit_current_card(self, card_id: int) -> None:
        """Suspend alternate screen, open card in $EDITOR, and push updates to Anki."""
        data = self.client.get_note_fields_for_card(card_id)
        if not data:
            return

        note_id, fields = data
        TerminalScreen.suspend()
        try:
            updated_fields = self.editor.edit_fields(fields)
        finally:
            TerminalScreen.resume()

        if updated_fields:
            self.client.update_note_fields(note_id, updated_fields)

    def review_deck(self, deck_name: str) -> None:
        if not self.client.start_deck_review(deck_name):
            self.reviewer_ui.show_review_launch_error(deck_name)
            return

        cards_reviewed = 0
        while True:
            card = self.client.get_current_card()
            if not card:
                self.reviewer_ui.show_session_summary(deck_name, cards_reviewed)
                break

            # Question loop (supports editing before revealing answer)
            while True:
                clean_q, q_action = self.reviewer_ui.show_question(deck_name, card.question)
                if q_action == "quit":
                    return
                if q_action == "edit":
                    self.edit_current_card(card.id)
                    card = self.client.get_current_card() or card
                    continue
                break

            # Answer reveal
            self.client.show_answer()

            # Rating / Answer loop (supports editing after seeing answer)
            while True:
                ease, a_action = self.reviewer_ui.show_answer(deck_name, clean_q, card.answer)
                if a_action == "quit":
                    return
                if a_action == "edit":
                    self.edit_current_card(card.id)
                    card = self.client.get_current_card() or card
                    clean_q = card.question
                    continue
                if a_action == "rate" and ease is not None:
                    self.client.answer_card(ease)
                    cards_reviewed += 1
                    break
