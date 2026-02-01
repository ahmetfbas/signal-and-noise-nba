# analysis/summarize_ai.py

import os
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from openai import OpenAI


MODEL = "gpt-4.1-mini"
CACHE_DIR = "data/derived"
CACHE_EXPIRY_DAYS = 3  # regenerate summaries older than N days


def _data_hash(df: pd.DataFrame) -> str:
    """
    Generate a compact hash for the board’s input data.
    Uses only the first 10 rows by design (speed > completeness).
    """
    snippet = df.head(10).to_csv(index=False)
    return hashlib.sha1(snippet.encode("utf-8")).hexdigest()


def summarize_board(board_name: str, data: pd.DataFrame) -> str:
    """
    Generate a 1–2 sentence AI summary for a given board.
    Cached by (board_name + data signature).
    """

    if data.empty:
        raise RuntimeError(f"Cannot summarize empty board: {board_name}")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    os.makedirs(CACHE_DIR, exist_ok=True)

    today = datetime.utcnow().date().isoformat()
    cache_path = os.path.join(CACHE_DIR, f"ai_summaries_{today}.json")

    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache = json.load(f)

    signature = _data_hash(data)
    cache_key = f"{board_name}:{signature}"
    now = datetime.utcnow()

    # --------------------------------------------------
    # Cache hit
    # --------------------------------------------------
    if cache_key in cache:
        entry = cache[cache_key]
        last_ts = datetime.fromisoformat(entry["timestamp"])
        if (now - last_ts) <= timedelta(days=CACHE_EXPIRY_DAYS):
            return entry["summary"]

    # --------------------------------------------------
    # Generate new summary
    # --------------------------------------------------
    client = OpenAI(api_key=api_key)

    prompt = f"""
You are an NBA analyst writing a short tweet-style summary for the {board_name}.

Data snapshot:
{data.head(10).to_string(index=False)}

Write 1–2 sentences (max 280 characters).
Use a calm, analytical tone.
Avoid clichés, hype, emojis, hashtags, lists, or ellipses.
End with a complete, grammatically closed sentence.
"""

    response = client.responses.create(
        model=MODEL,
        input=prompt,
        temperature=0.65,
        max_output_tokens=120,
    )

    summary = response.output_text.strip()
    summary = summary.rstrip(".… ").strip() + "."

    cache[cache_key] = {
        "summary": summary,
        "timestamp": now.isoformat(),
        "signature": signature,
        "board": board_name,
    }

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    return summary
