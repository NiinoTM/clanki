from dataclasses import dataclass
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
