import sys
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
                    print(f"\n⚠️  AnkiConnect error on '{action}': {data['error']}", file=sys.stderr)
                return None
            return data.get("result")
        except requests.exceptions.ConnectionError:
            if not suppress_error:
                print(
                    f"\n❌ Could not connect to AnkiConnect at {self.url}."
                    "\nEnsure Anki desktop is open and AnkiConnect is installed.",
                    file=sys.stderr,
                )
            return None
        except requests.exceptions.RequestException as err:
            if not suppress_error:
                print(f"\n❌ Network error: {err}", file=sys.stderr)
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
            safe = d.replace('"', '\\"')
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
