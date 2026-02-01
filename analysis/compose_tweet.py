import textwrap
import hashlib
from analysis.summarize_ai import summarize_board


def _stable_hint(hints, seed: str) -> str:
    """
    Deterministic hint selection based on content hash.
    """
    h = int(hashlib.sha1(seed.encode("utf-8")).hexdigest(), 16)
    return hints[h % len(hints)]


def compose_tweet(
    board_name: str,
    data,
    header: str,
    body_text: str = None,
    mode: str = "board",
):
    """
    Returns two parts for thread posting:
    - tweet_main: coded metrics and formatted header
    - tweet_ai: concise human-style AI commentary

    mode ∈ {"board", "pregame", "postgame"}
    """

    ai_text = summarize_board(f"{mode.capitalize()} - {board_name}", data)

    prefix = {
        "board": "📊",
        "pregame": "🏀",
        "postgame": "🏁",
    }.get(mode, "")

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

    body_text = body_text.strip() if body_text else ""

    hint_seed = f"{mode}:{board_name}:{header}"
    comment_hint = _stable_hint(
        hints.get(mode, ["🗣️ Comment below ⤵️"]),
        hint_seed,
    )

    header_block = f"{prefix} {header}".strip()

    # Safely shorten ONLY the body if needed
    if body_text:
        max_body_len = 280 - len(header_block) - len(comment_hint) - 4
        body_text = textwrap.shorten(
            body_text,
            width=max_body_len,
            placeholder="…",
            break_long_words=False,
            break_on_hyphens=False,
        )

    tweet_main = "\n".join(
        part for part in [header_block, body_text, "", comment_hint] if part
    ).strip()

    tweet_ai = ai_text.strip()

    return tweet_main, tweet_ai
