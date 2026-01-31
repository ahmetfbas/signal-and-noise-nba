import textwrap
import random
from analysis.summarize_ai import summarize_board


def compose_tweet(board_name: str, data, header: str, body_text: str = None, mode: str = "board"):
    """
    Returns two parts for thread posting:
    - tweet_main: coded metrics and formatted matchup
    - tweet_ai: concise human-style AI commentary

    mode ∈ {"board", "pregame", "postgame"}
    """

    ai_text = summarize_board(f"{mode.capitalize()} - {board_name}", data)

    prefix = {
        "board": "📊",
        "pregame": "🏀",
        "postgame": "🏁",
    }.get(mode, "")

    # Comment hints vary by mode
    hints = {
        "board": [
            "🧠 Analyst note below ⤵️",
            "💬 Quick context below ⤵️",
            "🔎 Read the analyst's comment ⤵️",
        ],
        "pregame": [
            "💭 See the breakdown below ⤵️",
            "📊 Context follows ⤵️",
            "🗣️ Comment below ⤵️",
        ],
        "postgame": [
            "🔎 Full insight below ⤵️",
            "💭 Postgame reflection below ⤵️",
            "🧠 What it means, see below ⤵️",
        ],
    }

    comment_hint = random.choice(hints.get(mode, ["🗣️ Comment below ⤵️"]))

    body_text = body_text.strip() if body_text else ""
    tweet_main = f"{prefix} {header}\n{body_text}\n\n{comment_hint}".strip()

    # Trim safely if too long
    if len(tweet_main) > 280:
        cutoff = tweet_main[:277].rfind(".")
        tweet_main = tweet_main[:cutoff + 1] if cutoff != -1 else textwrap.shorten(tweet_main, width=277, placeholder="…")

    tweet_ai = ai_text.strip()

    return tweet_main, tweet_ai
