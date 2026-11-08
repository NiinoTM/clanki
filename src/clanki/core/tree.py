from typing import Dict, List
from clanki.core.models import DeckNode, DeckStats

def filter_valid_decks(decks: List[str], stats: Dict[str, DeckStats]) -> List[str]:
    """Prune empty orphan/ghost decks unless they or their descendants contain cards."""
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
    """Convert deck paths into hierarchical DeckNode structures."""
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
