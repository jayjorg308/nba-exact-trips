"""Triage inspector: for every grammar anomaly in a season's survey output,
dump the surrounding play-by-play evidence window so extensions are written
from events, never guesses.

  python ingestion/inspect_anomalies.py --season 2025-26 > triage-2025-26.txt
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import latest_pair_paths, load, validate_game_pair  # noqa: E402

RELEVANT = {
    "Free Throw", "Foul", "Violation", "Made Shot", "Missed Shot",
    "Substitution", "Instant Replay", "Jump Ball", "Turnover", "Timeout",
}


def clock_seconds(clock: str) -> float | None:
    match = re.fullmatch(r"PT(\d+)M([\d.]+)S", clock)
    return int(match.group(1)) * 60 + float(match.group(2)) if match else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--derived-root", default="data/derived")
    ap.add_argument("--window", type=float, default=45.0,
                    help="clock window (seconds) around the anomaly")
    args = ap.parse_args()

    anomalies_path = Path(args.derived_root) / args.season / "anomalies.csv"
    with anomalies_path.open(encoding="utf-8") as handle:
        rows = [r for r in csv.DictReader(handle) if r["reason"] != "box-mismatch"]

    raw_root = Path(args.raw_root)
    for row in rows:
        game_id = row["game_id"]
        period = int(row["period"])
        clock = row["clock"]
        anchor = clock_seconds(clock)
        player_id = int(row["player_id"])
        print(f"\n{'=' * 78}")
        print(f"{game_id} P{period} {clock} {row['player_name']} "
              f"({player_id}) :: {row['reason']} :: {row['detail']}")
        pair = latest_pair_paths(raw_root, game_id)
        pbp_game, _, _ = validate_game_pair(load(pair[0]), load(pair[1]))
        for action in pbp_game.get("actions", []):
            if not isinstance(action, dict):
                continue
            if int(action.get("period", 0)) != period:
                continue
            seconds = clock_seconds(str(action.get("clock", "")))
            in_window = (
                anchor is not None and seconds is not None
                and abs(seconds - anchor) <= args.window
            )
            is_player = int(action.get("personId", 0)) == player_id
            if not in_window and not (
                is_player and action.get("actionType") == "Free Throw"
            ):
                continue
            if action.get("actionType") not in RELEVANT and not is_player:
                continue
            marker = ">>" if is_player else "  "
            print(f"{marker} #{action.get('actionNumber'):>4} "
                  f"{str(action.get('clock', '')):<13} "
                  f"{str(action.get('actionType', '')):<14} "
                  f"{str(action.get('subType', '')):<26} "
                  f"{str(action.get('playerName') or ''):<14} "
                  f"{str(action.get('teamTricode', '')):<3} "
                  f"{str(action.get('description', ''))[:80]}")


if __name__ == "__main__":
    main()
