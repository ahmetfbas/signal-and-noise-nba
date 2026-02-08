import os
import json
import hashlib
from datetime import datetime, timedelta
import pandas as pd
from openai import OpenAI

MODEL = "gpt-4.1-mini"

CACHE_DIR = "data/derived"
CACHE_FILE = "ai_pregame_summaries_cache.json"
CACHE_EXPIRY_DAYS = 3


# ------------------------------
# Hash helper (stable, small)
# ------------------------------
def _data_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


# ------------------------------
# Main summarizer
# ------------------------------
def summarize_pregame_matchup(matchup_name: str, signals: dict) -> str:
    """
    Generate a short AI explanation for a pregame matchup.

    Allowed inputs ONLY:
      - identity
      - momentum
      - fatigue
      - consistency
      - environment
    """

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, CACHE_FILE)

    cache = {}
    if os.path.exists(cache_path):
        with open(cache_path, "r") as f:
            cache = json.load(f)

    signature = _data_hash(signals)
    cache_key = f"{matchup_name}:{signature}"
    now = datetime.utcnow()

    # ------------------------------
    # Cache hit
    # ------------------------------
    if cache_key in cache:
        entry = cache[cache_key]
        last_ts = datetime.fromisoformat(entry["timestamp"])
        if (now - last_ts) <= timedelta(days=CACHE_EXPIRY_DAYS):
            return entry["summary"]

    # ------------------------------
    # AI generation (fail soft)
    # ------------------------------
    try:
        client = OpenAI(api_key=api_key)

        system_prompt = """
You are an NBA analytics assistant.

You may ONLY reason using the provided metrics.
You must NOT:
- Predict game outcomes
- Invent injuries, tactics, or narratives
- Use betting language
- Add information not present in the inputs

If signals are weak, mixed, or inconclusive, say so plainly.

Metric definitions:
- Identity: season-long team profile based on win rate, consistency, and performance vs expectation.
- Momentum: recent directional trend (positive or negative), not absolute strength.
- Fatigue: physical load indicator (higher = more strain).
- Consistency: stability of game-to-game performance (higher = more predictable).
- Environment: overall volatility risk of the matchup (Clean, Mixed, Noisy).

Write like a calm analyst.
"""

        user_prompt = f"""
Pregame matchup: {matchup_name}

Signals:
{json.dumps(signals, indent=2)}

Write 2–4 short sentences (max 280 characters total).
Do not hype.
Do not predict a winner.
If nothing stands out, say that the signals are neutral or unclear.
End with a complete sentence.
"""

        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.55,
            max_output_tokens=140,
        )

        summary = response.output_text.strip()
        summary = summary.rstrip(".… ").strip() + "."

    except Exception:
        return ""

    # ------------------------------
    # Save cache
    # ------------------------------
    cache[cache_key] = {
        "summary": summary,
        "timestamp": now.isoformat(),
        "signature": signature,
        "matchup": matchup_name,
    }

    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

    return summary
