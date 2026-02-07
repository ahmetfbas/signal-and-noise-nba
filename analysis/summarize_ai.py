import os
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from openai import OpenAI


MODEL = "gpt-4.1-mini"
CACHE_DIR = "data/derived"
CACHE_FILE = "ai_summaries_cache.json"
CACHE_EXPIRY_DAYS = 3


def _data_hash(df: pd.DataFrame) -> str:
    snippet = (
        df.sort_index()
        .head(10)
        .to_csv(index=False)
    )
    return hashlib.sha1(snippet.encode("utf-8")).hexdigest()


def summarize_board(board_name: str, data: pd.DataFrame) -> str:
    if data.empty:
        return ""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, CACHE_FILE)

    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache = json.load(f)

    signature = _data_hash(data)
    cache_key = f"{board_name}:{signature}"
    now = datetime.utcnow()

    # Cache hit
    if cache_key in cache:
        entry = cache[cache_key]
        last_ts = datetime.fromisoformat(entry["timestamp"])
        if (now - last_ts) <= timedelta(days=CACHE_EXPIRY_DAYS):
            return entry["summary"]

    # Generate summary (fail soft)
    try:
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

    except Exception:
        return ""

    cache[cache_key] = {
        "summary": summary,
        "timestamp": now.isoformat(),
        "signature": signature,
        "board": board_name,
    }

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    return summary
