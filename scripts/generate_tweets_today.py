import os
from datetime import datetime
from pathlib import Path
import io
import sys

from scripts.print_pregame_lens import main as run_pregame
from scripts.print_fatigue_matchups_thread import main as run_fatigue
from scripts.print_postgame_lens import main as run_postgame


EXPORT_DIR = "data/exports"


def capture_output(func):
    buffer = io.StringIO()
    sys_stdout = sys.stdout
    sys.stdout = buffer

    try:
        func()
    finally:
        sys.stdout = sys_stdout

    return buffer.getvalue()


def main():
    today = datetime.utcnow().date().isoformat()

    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    filepath = os.path.join(EXPORT_DIR, f"tweets_{today}.txt")

    print("Generating tweets file...")

    content = []

    content.append("=== PREGAME ===\n")
    content.append(capture_output(run_pregame))

    content.append("\n=== FATIGUE THREAD ===\n")
    content.append(capture_output(run_fatigue))

    content.append("\n=== POSTGAME ===\n")
    content.append(capture_output(run_postgame))

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

    print(f"✅ Tweets saved to {filepath}")


if __name__ == "__main__":
    main()
