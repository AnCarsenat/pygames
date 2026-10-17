import argparse
import sys
from pathlib import Path

from engine.app import App
from engine.config import DEFAULT_ROUNDS
from engine.loader import load_games

GAMES_DIR = Path(__file__).resolve().parent / "games"


def parse_args():
    parser = argparse.ArgumentParser(description="Local multiplayer party game.")
    parser.add_argument("--rounds", type=int, default=DEFAULT_ROUNDS)
    parser.add_argument("--layout", choices=("azerty", "qwerty"), default="azerty")
    parser.add_argument("--game", help="only play this mini-game (file name or title)")
    parser.add_argument("--seed", type=int)
    return parser.parse_args()


def normalize(name):
    return name.lower().replace(" ", "_").replace("-", "_")


def select_games(games, wanted):
    if not wanted:
        return games
    key = normalize(wanted)
    chosen = [g for g in games if key in (g.slug, normalize(g.name))]
    if not chosen:
        available = ", ".join(g.slug for g in games)
        sys.exit(f"Unknown game '{wanted}'. Available: {available}")
    return chosen


def main():
    args = parse_args()
    games = load_games(GAMES_DIR)
    if not games:
        sys.exit(f"No mini-games found in {GAMES_DIR}")
    App(
        select_games(games, args.game),
        rounds=max(1, args.rounds),
        layout=args.layout,
        seed=args.seed,
    ).run()


if __name__ == "__main__":
    main()
