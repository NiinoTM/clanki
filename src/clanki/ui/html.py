import html
import re
from clanki.ui.theme import (
    BOLD, C_CYAN, C_GREEN, C_YELLOW, ITALIC, OFF_BOLD, OFF_ITALIC, OFF_UNDERLINE, RESET, UNDERLINE
)

def clean_html(raw_html: str) -> str:
    """Convert card HTML markup into formatted ANSI terminal text."""
    # 1. Remove JavaScript and CSS completely
    clean = re.sub(r"<(script|style).*?</\1>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)

    # 2. Convert structural HTML tags to newlines & bullet points
    clean = re.sub(r"<(br|p|div|h[1-6])[^>]*>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</(p|div|h[1-6])>", "\n", clean, flags=re.IGNORECASE)
    clean = re.sub(r"<li[^>]*>", "\n  • ", clean, flags=re.IGNORECASE)
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

    clean = re.sub(r"<mark[^>]*>", "\033[7;33m", clean, flags=re.IGNORECASE)
    clean = re.sub(r"</mark>", "\033[27;39m", clean, flags=re.IGNORECASE)

    # 4. Strip any remaining unsupported HTML tags
    clean = re.sub(r"<[^>]+>", "", clean)

    # 5. Decode HTML entities (&lt;, &gt;, &amp;, &quot;, &#39;, etc.)
    clean = html.unescape(clean)

    # 6. Normalize spacing while preserving paragraph gaps
    clean = re.sub(r"\n\s*\n\s*\n+", "\n\n", clean)
    return clean.strip() + RESET

def extract_answer(raw_answer: str, clean_question: str) -> str:
    """Extract answer side, eliminating question repetition from {{FrontSide}} templates."""
    split_parts = re.split(r"""<hr\s*id=["']?answer["']?[^>]*>""", raw_answer, flags=re.IGNORECASE)
    if len(split_parts) > 1:
        clean_a = clean_html(split_parts[1])
    else:
        clean_a = clean_html(raw_answer)
        if clean_a.startswith(clean_question):
            clean_a = clean_a[len(clean_question):].lstrip()
    return clean_a
