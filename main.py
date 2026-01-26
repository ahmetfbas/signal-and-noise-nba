"""
Signal & Noise – Daily Pipeline Entrypoint

This script is executed by GitHub Actions.
It must be deterministic and non-interactive.
"""

from analysis.build_team_game_metrics import build_team_game_metrics
from analysis.build_rpmi import compute_rpmi
from analysis.build_cvv import compute_cvv
from analysis.build_game_environment import main as build_game_environment

import pandas as pd


def main():
    # --------------------------------------------------
    # 1) Build base team-game metrics (PvE + fatigue)
    # --------------------------------------------------
    df = build_team_game_metrics(
        start_date=None,
        end_date=None,
        output_csv="data/derived/team_game_metrics.csv"
    )

    # --------------------------------------------------
    # 2) RPMI
    # --------------------------------------------------
    df = compute_rpmi(df)
    df.to_csv("data/derived/team_game_metrics_with_rpmi.csv", index=False)

    # --------------------------------------------------
    # 3) Consistency vs Volatility
    # --------------------------------------------------
    df = compute_cvv(df)
    df.to_csv(
        "data/derived/team_game_metrics_with_rpmi_cvv.csv",
        index=False
    )

    # --------------------------------------------------
    # 4) Game environment classification
    # --------------------------------------------------
    build_game_environment()


if __name__ == "__main__":
    main()
