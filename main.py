# main.py
from datetime import datetime
from fal import run_fatigue
from pve import run_pve

def main():
    RUN_DATE = datetime.utcnow().date()
    WINDOW_DAYS = 15

    print("\n=== Fatigue & Load ===")
    run_fatigue(RUN_DATE)

    print("\n=== Performance vs Expectation ===")
    run_pve(RUN_DATE, WINDOW_DAYS)

if __name__ == "__main__":
    main()
