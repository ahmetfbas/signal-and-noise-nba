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
    print("\n🔄 MONDAY RUN — Weekly Momentum & Consistency\n")

    run("python -m scripts.print_momentum_board")
    run("python -m scripts.print_consistency_board")

    print("\n✅ Monday run completed.\n")


if __name__ == "__main__":
    main()
