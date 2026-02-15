import subprocess
import sys


def run(cmd: str):
    print("\n" + "=" * 60)
    print(f"▶ Running: {cmd}")
    print("=" * 60 + "\n")

    result = subprocess.run(
        cmd.split(),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )

    if result.returncode != 0:
        print(f"\n❌ Command failed: {cmd}")
        sys.exit(result.returncode)


def main():
    print("\n🌙 EVENING RUN — Pregame + Fatigue\n")

    run("python -m scripts.print_pregame_lens")
    run("python -m scripts.print_fatigue_matchups_thread")
    print("\n✅ Evening run completed.\n")


if __name__ == "__main__":
    main()
