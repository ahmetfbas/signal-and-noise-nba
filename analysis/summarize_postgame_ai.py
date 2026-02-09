import os
import json
import hashlib
from datetime import datetime, timedelta
from openai import OpenAI


MODEL = "gpt-4.1-mini"

CACHE_DIR = "data/derived"
CACHE_FILE = "ai_postgame_summaries_cache.json"
CACHE_EXPIRY_DAYS = 5


# --------------------------------------------------
# Hash helper
# --------------------------------------------------
def _data_hash(payload: dict) -> str:
    blob = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------
# Main summarizer
# --------------------------------------------------
def summarize_postgame_matchup(matchup_name: str, evaluation: dict) -> str:
    """
    Generate ONE sentence explaining how pregame signals
    related to the final outcome.

    The AI MUST:
    - Comment on fatigue, momentum, and consistency
    - Explicitly note asymmetry vs no asymmetry
    - Prefer one dominant factor if clear
    - Otherwise say signals were mixed or neutral
    - Never invent new information
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

    signature = _data_hash(evaluation)
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
    # AI generation
    # ------------------------------
    try:
        client = OpenAI(api_key=api_key)

        system_prompt = """
You are an NBA analytics assistant.

You are analyzing a POSTGAME result using ONLY structured pregame signals.

Rules:
- You must write exactly ONE sentence.
- You must mention fatigue, momentum, and consistency.
- If a metric had no asymmetry, say it was balanced or neutral.
- If a metric conflicted with the result, say so plainly.
- If a metric aligned with the result, say so cautiously.
- If no metric stood out, say signals were mixed or unclear.
- Do NOT predict, praise, blame, or speculate.
- Do NOT invent injuries, tactics, or player impact.
- Do NOT use hype or emotional language.
- Write like a calm analyst.

Your goal is explanation, not justification.
"""

        user_prompt = f"""
Postgame matchup: {matchup_name}

Structured evaluation:
{json.dumps(evaluation, indent=2)}

Write ONE calm, complete sentence (max 35 words).
"""

        response = client.responses.create(
            model=MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.4,
            max_output_tokens=60,
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
