import os
import json
from datetime import datetime, timedelta
import pandas as pd
from openai import OpenAI
import hashlib

MODEL = "gpt-4o-mini"
CACHE_DIR = "data/derived"
CACHE_EXPIRY_DAYS = 3  # regenerate summaries older than 3 days


def _data_hash(df: pd.DataFrame) -> str:
    """Generate a compact hash for the board’s input data (top 10 rows)."""
    snippet = df.head(10).to_csv(index=False)
    return hashlib.sha1(snippet.encode("utf-8")).hexdigest()


def summarize_board(board_name: str, data: pd.DataFrame) -> str:
    """
    Generate a 1–2 sentence AI summary for a given board (cached & refreshed automatically).
    Ensures natural tone and complete, grammatically closed sentences.
    """
    os.makedirs(CACHE_DIR, exist_ok=True)
    today = datetime.utcnow().date().isoformat()
    cache_path = os.path.join(CACHE_DIR, f"ai_summaries_{today}.json")

    # Load existing cache
    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache = json.load(f)

    # Generate a unique signature to detect data changes
    signature = _data_hash(data)
    now = datetime.utcnow()

    # Check if cached summary is valid
    if (
        board_name in cache
        and "summary" in cache[board_name]
        and "timestamp" in cache[board_name]
        and "signature" in cache[board_name]
    ):
        last_ts = datetime.fromisoformat(cache[board_name]["timestamp"])
        is_expired = (now - last_ts) > timedelta(days=CACHE_EXPIRY_DAYS)
        same_data = cache[board_name]["signature"] == signature

        if not is_expired and same_data:
            print(f"♻️ Using cached summary for {board_name}")
            return cache[board_name]["summary"]

    # --- Generate new summary ---
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""
    You are an NBA analyst writing a short tweet summary for the {board_name}.

    Data snapshot:
    {data.head(10).to_string(index=False)}

    Write 1–2 sentences (max 280 characters) with natural language and light analytical tone.
    Avoid clichés, filler, or unfinished phrasing. Do not use ellipses (...).
    End your response with a complete sentence.
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise, insightful NBA analyst. "
                    "Write natural, tweet-sized summaries that sound like a human observer. "
                    "Avoid lists, hashtags, emojis, and dramatic hype. "
                    "End every response with a grammatically complete sentence — "
                    "no ellipses, no trailing dots, and no cliffhangers."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.65,
        max_tokens=120,
    )

    summary = response.choices[0].message.content.strip()

    # Clean potential trailing punctuation or ellipsis (just in case)
    summary = summary.rstrip(".… ").strip() + "."

    # --- Update cache ---
    cache[board_name] = {
        "summary": summary,
        "timestamp": now.isoformat(),
        "signature": signature,
    }

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    print(f"💾 Cached summary for {board_name}")
    return summary
