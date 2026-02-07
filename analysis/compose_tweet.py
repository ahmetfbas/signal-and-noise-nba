import textwrap
import hashlib
from typing import Optional, Tuple

from analysis.summarize_ai import summarize_board


# --------------------------------------------------
# Deterministic helpers
# --------------------------------------------------

def _stable_hint(hints, seed: str) -> str:
    """
    Deterministic hint selection based on content hash.
    Falls back safely if hints are empty.
    """
    if not hints:
        return "🗣️ Context below ⤵️"

    h = int(hashlib.sha1(seed.encode("utf-8")).hexdigest(), 16)
    return hints[h % len(hints)]


# --------------------------------------------------
# Main composer
# --------------------------------------------------

def compose_tweet(
    board_name: str,
    data,
    header: str,
    body_text: Optional[str] = None,
    mode: str = "board",
) -> Tuple[str, Optional[str]]:
    """
    Compose a two-part tweet thread.

    Returns:
    - tweet_main: formatted metrics / header tweet
    - tweet_ai: optional AI commentary (None if unavailable)

    mode ∈ {"board", "pregame", "postgame"}
    """

    allowed_modes = {"board", "pregame", "postgame"}
    if mode not in allowed_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {allowed_modes}")

    # --------------------------------------------------
    # AI summary (optional)
    # --------------------------------------------------
    try:
        ai_text = summarize_board(f"{mode.capitalize()} - {board_name}", data)
        ai_text = ai_text.strip()
    except Exception:
        ai_text = ""

    tweet_ai = ai_text if ai_text else None

    # --------------------------------------------------
    # Prefix & hints
    # --------------------------------------------------
    prefix = {
        "board": "📊",
        "pregame": "🏀",
        "postgame": "🏁",
    }[mode]

    hints = {
        "board": [
            "🧠 Analyst note below ⤵️",
            "💬 Quick context below ⤵️",
            "🔎 Analyst context below ⤵️",
        ],
        "pregame": [
            "💭 Context below ⤵️",
            "📊 Breakdown below ⤵️",
            "🗣️ Analyst view below ⤵️",
        ],
        "postgame": [
            "🔎 Postgame insight below ⤵️",
            "💭 What it means below ⤵️",
            "🧠 Takeaway below ⤵️",
        ],
    }

    hint_seed = f"{mode}:{board_name}:{header}"
    comment_hint = _stable_hint(hints.get(mode), hint_seed)

    # --------------------------------------------------
    # Header & body formatting
    # --------------------------------------------------
    header_block = f"{prefix} {header}".strip()
    body_text = body_text.strip() if body_text else ""

    if body_text:
        max_body_len = 280 - len(header_block) - len(comment_hint) - 4

        if max_body_len > 20:  # guard against pathological cases
            body_text = textwrap.shorten(
                body_text,
                width=max_body_len,
                placeholder="…",
                break_long_words=False,
                break_on_hyphens=False,
            )
        else:
            body_text = ""

    tweet_main = "\n".join(
        part for part in [header_block, body_text, "", comment_hint] if part
    ).strip()

    return tweet_main, tweet_ai
