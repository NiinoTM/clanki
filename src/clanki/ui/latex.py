"""LaTeX and MathJax formula transliteration into clean Unicode terminal text."""

import re

# Greek Alphabet mapping (Upper & Lower)
GREEK_SYMBOLS = {
    r"\alpha": "α", r"\beta": "β", r"\gamma": "γ", r"\delta": "δ",
    r"\epsilon": "ε", r"\varepsilon": "ε", r"\zeta": "ζ", r"\eta": "η",
    r"\theta": "θ", r"\vartheta": "θ", r"\iota": "ι", r"\kappa": "κ",
    r"\lambda": "λ", r"\mu": "μ", r"\nu": "ν", r"\xi": "ξ",
    r"\pi": "π", r"\rho": "ρ", r"\sigma": "σ", r"\tau": "τ",
    r"\upsilon": "υ", r"\phi": "φ", r"\varphi": "ϕ", r"\chi": "χ",
    r"\psi": "ψ", r"\omega": "ω",
    r"\Gamma": "Γ", r"\Delta": "Δ", r"\Theta": "Θ", r"\Lambda": "Λ",
    r"\Xi": "Ξ", r"\Pi": "Π", r"\Sigma": "Σ", r"\Upsilon": "Υ",
    r"\Phi": "Φ", r"\Psi": "Ψ", r"\Omega": "Ω",
}

# Common mathematical & physical operators
MATH_SYMBOLS = {
    r"\times": "×", r"\cdot": "·", r"\div": "÷", r"\pm": "±", r"\mp": "∓",
    r"\approx": "≈", r"\sim": "∼", r"\neq": "≠", r"\ne": "≠",
    r"\leq": "≤", r"\le": "≤", r"\geq": "≥", r"\ge": "≥",
    r"\ll": "≪", r"\gg": "≫", r"\equiv": "≡", r"\propto": "∝",
    r"\infty": "∞", r"\partial": "∂", r"\nabla": "∇",
    r"\sum": "∑", r"\prod": "∏", r"\int": "∫", r"\oint": "∮",
    r"\sqrt": "√", r"\circ": "°", r"\hbar": "ħ",
    r"\rightarrow": "→", r"\to": "→", r"\leftarrow": "←",
    r"\Rightarrow": "⇒", r"\Leftarrow": "⇐", r"\leftrightarrow": "↔",
    r"\in": "∈", r"\notin": "∉", r"\forall": "∀", r"\exists": "∃",
    r"\dots": "...", r"\ldots": "...", r"\cdots": "···", r"\vdots": "⋮", r"\ddots": "⋱",
}

# Subscript & Superscript mapping tables
SUPERSCRIPTS = str.maketrans({
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
    "n": "ⁿ", "i": "ⁱ", "x": "ˣ", "y": "ʸ",
})

SUBSCRIPTS = str.maketrans({
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄",
    "5": "₅", "6": "₆", "7": "₇", "8": "₈", "9": "₉",
    "+": "₊", "-": "₋", "=": "₌", "(": "₍", ")": "₎",
    "a": "ₐ", "e": "ₑ", "i": "ᵢ", "j": "ⱼ", "k": "ₖ",
    "m": "ₘ", "n": "ₙ", "o": "ₒ", "p": "ₚ", "r": "ᵣ",
    "s": "ₛ", "t": "ₜ", "u": "ᵤ", "v": "ᵥ", "x": "ₓ",
})


def _sub_sup(match: re.Match) -> str:
    marker = match.group(1)
    content = match.group(2) or match.group(3)
    if not content:
        return ""
    table = SUPERSCRIPTS if marker == "^" else SUBSCRIPTS
    # Translate characters that exist in table, preserve others
    translated = content.translate(table)
    return translated if all(ch in table.values() for ch in translated) else f"{marker}{content}"


def render_latex(text: str) -> str:
    """Transform LaTeX math expressions into readable Unicode terminal text."""
    if not text:
        return ""

    out = text

    # 1. Fractions: \frac{num}{den} -> (num / den)
    out = re.sub(r"\\frac\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"(\1 / \2)", out)

    # 2. Square roots: \sqrt{x} -> √(x)
    out = re.sub(r"\\sqrt\s*\{([^{}]+)\}", r"√(\1)", out)

    # 3. Text, font & underline wrappers: \text{...}, \mathrm{...}, \underline{...} -> ...
    out = re.sub(r"\\(?:text|mathrm|mathbf|mathit|textbf|bm|underline)\s*\{([^{}]+)\}", r"\1", out)

    # 4. Vectors: \vec{x} -> x⃗
    out = re.sub(r"\\vec\s*\{([a-zA-Z])\}", lambda m: f"{m.group(1)}\u20D7", out)
    out = re.sub(r"\\vec\s*([a-zA-Z])", lambda m: f"{m.group(1)}\u20D7", out)

    # 5. Greek characters & operators
    for macro, unicode_char in GREEK_SYMBOLS.items():
        out = re.sub(re.escape(macro) + r"(?![a-zA-Z])", unicode_char, out)

    for macro, unicode_char in MATH_SYMBOLS.items():
        out = re.sub(re.escape(macro) + r"(?![a-zA-Z])", unicode_char, out)

    # 6. Superscripts (^2, ^{12}) and Subscripts (_1, _{max})
    out = re.sub(r"([\^_])(?:\{([^{}]+)\}|([0-9a-zA-Z+-]))", _sub_sup, out)

    # 7. Formatting & spacing macros
    out = re.sub(r"\\[,;:]", " ", out)
    out = re.sub(r"\\(?:quad|qquad)", "   ", out)

    # 8. Strip MathJax and Anki LaTeX delimiters
    out = re.sub(r"\\\(|\\\)", "", out)
    out = re.sub(r"\\\[|\\\]", "", out)
    out = re.sub(r"\[/?\$?\$?\]", "", out)
    out = re.sub(r"\[/?latex\]", "", out, flags=re.IGNORECASE)

    # 9. Clean up any leftover macro backslashes before plain words
    out = re.sub(r"\\([a-zA-Z]+)", r"\1", out)

    return out