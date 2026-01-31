import pandas as pd
from analysis.summarize_ai import summarize_board

def main():
    boards = {
        "Fatigue Board": "data/derived/team_game_metrics.csv",
        "Momentum Board": "data/derived/team_game_metrics_with_rpmi_cvv.csv",
        "Consistency Board": "data/derived/team_game_metrics_with_rpmi_cvv.csv",
    }

    for name, path in boards.items():
        df = pd.read_csv(path)
        text = summarize_board(name, df)
        print(f"\n{name} Summary:\n{text}\n")

if __name__ == "__main__":
    main()
