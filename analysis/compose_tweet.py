import textwrap
import hashlib
from typing import Optional, Tuple

from analysis.summarize_pregame_ai import summarize_board
from analysis.summarize_postgame_ai import summarize_postgame_matchup


# --------------------------------------------------
# Deterministic helpers
# --------------------------------------------------
def _stable_hint(hints, seed: str) -> Optional[str]:
    """
    Deterministic hint selection based on content hash.
    Returns None if hints list is empty.
    """
    if not hints:
        return None

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
    Compose a tweet.

    For postgame:
    - AI generates the explanatory sentence
    - No separate postgame insight block
    - No continuation hint
    """

    allowed_modes = {"board", "pregame", "postgame"}
    if mode not in allowed_modes:
        raise ValueError(f"Invalid mode '{mode}'. Must be one of {allowed_modes}")

    # --------------------------------------------------
    # AI summary (mode-aware)
    # --------------------------------------------------
    ai_text = ""

    try:
        if mode == "postgame":
            ai_text = summarize_postgame_matchup(board_name, data)
        else:
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
        "postgame": [],  # intentionally empty
    }

    comment_hint = None
    if hints.get(mode):
        hint_seed = f"{mode}:{board_name}:{header}"
        comment_hint = _stable_hint(hints.get(mode), hint_seed)

    # --------------------------------------------------
    # Header & body formatting
    # --------------------------------------------------
    header_block = f"{prefix} {header}".strip()

    # For postgame, body comes ONLY from AI
    final_body = ""
    if mode == "postgame" and tweet_ai:
        final_body = tweet_ai
    elif body_text:
        final_body = body_text.strip()

    if final_body and mode != "postgame":
        max_body_len = 280 - len(header_block) - (len(comment_hint) if comment_hint else 0) - 4

        if max_body_len > 20:
            final_body = textwrap.shorten(
                final_body,
                width=max_body_len,
                placeholder="…",
                break_long_words=False,
                break_on_hyphens=False,
            )
        else:
            final_body = ""

    tweet_parts = [header_block]

    if final_body:
        tweet_parts.append(final_body)

    if comment_hint:
        tweet_parts.append("")
        tweet_parts.append(comment_hint)

    tweet_main = "\n".join(tweet_parts).strip()

    # For postgame we already embedded AI → do not return tweet_ai
    if mode == "postgame":
        return tweet_main, None

    return tweet_main, tweet_ai
