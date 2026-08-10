"""Pull the league-wide game corpus for a season: every regular-season
PlayByPlayV3 + BoxScoreTraditionalV3 pair, verbatim, append-only.

RESUMABLE BY DESIGN — run it, let it work, rerun until it reports complete.
A game with an existing snapshot pair is skipped; a failed game is recorded
and retried on the next run; both files of a pair are fetched before either
is written, so an interrupted run can never leave a half-pair that looks
complete.

LOCAL ONLY: stats.nba.com blocks cloud IPs. Run from a developer machine:

  python ingestion/pull_league_games.py --season 2025-26
  python ingestion/pull_league_games.py --season 2024-25

Optional: --limit 200 caps one session; --sleep adjusts pacing (be gentle).
Discovery (the season's game-ID list) is cached under
data/raw/_league/<season>/games/ and reused; --rediscover forces a fresh
discovery pull.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

try:
    from nba_api.stats.endpoints import (
        boxscoretraditionalv3,
        leaguegamefinder,
        playbyplayv3,
    )
except ImportError:
    sys.exit("nba_api not installed. Run: pip install nba_api")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import season_game_prefix  # noqa: E402


def discover_game_ids(season: str, timeout: int) -> list[str]:
    """All regular-season game IDs for a season, from LeagueGameFinder."""
    finder = leaguegamefinder.LeagueGameFinder(
        season_nullable=season,
        season_type_nullable="Regular Season",
        league_id_nullable="00",
        timeout=timeout,
    )
    frame = finder.get_data_frames()[0]
    prefix = season_game_prefix(season)
    ids = sorted(
        {str(g) for g in frame["GAME_ID"].astype(str) if str(g).startswith(prefix)}
    )
    if not ids:
        sys.exit(f"discovery returned no regular-season games for {season}")
    return ids


def cached_game_ids(raw_root: Path, season: str, timeout: int, rediscover: bool) -> list[str]:
    cache_dir = raw_root / "_league" / season / "games"
    cached = sorted(cache_dir.glob("*.json"))
    if cached and not rediscover:
        snapshot = json.loads(cached[-1].read_text(encoding="utf-8"))
        ids = [str(g) for g in snapshot.get("game_ids", [])]
        print(f"discovery cache: {len(ids)} games ({cached[-1].name})")
        return ids
    ids = discover_game_ids(season, timeout)
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{date.today().isoformat()}.json"
    path.write_text(
        json.dumps(
            {
                "_meta": {
                    "season": season,
                    "season_type": "Regular Season",
                    "pull_date": date.today().isoformat(),
                    "source": "stats.nba.com leaguegamefinder (unofficial)",
                },
                "game_ids": ids,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"discovered {len(ids)} regular-season games -> {path}")
    return ids


def snapshot(game_id: str, pull_date: str, source: str, response: dict) -> dict:
    return {
        "_meta": {
            "game_id": game_id,
            "pull_date": pull_date,
            "pull_unit": "game",
            "source": source,
        },
        "response": response,
    }


def paired_snapshot_exists(raw_root: Path, game_id: str) -> bool:
    pbp_dir = raw_root / "play-by-play" / game_id
    box_dir = raw_root / "box-score" / game_id
    pbp = {p.name for p in pbp_dir.glob("*.json")} if pbp_dir.exists() else set()
    box = {p.name for p in box_dir.glob("*.json")} if box_dir.exists() else set()
    orphaned = sorted(pbp ^ box)
    if orphaned:
        sys.exit(f"game {game_id} has orphaned raw snapshots: {', '.join(orphaned)}")
    return bool(pbp)


def write_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        sys.exit(f"refusing to overwrite append-only artifact: {path}")
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Pull a season's league-wide game corpus.")
    ap.add_argument("--season", required=True, help="e.g. 2025-26")
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--sleep", type=float, default=0.6,
                    help="seconds between games (be gentle; unofficial API)")
    ap.add_argument("--timeout", type=int, default=45)
    ap.add_argument("--retries", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0,
                    help="max games to pull this session (0 = no cap)")
    ap.add_argument("--rediscover", action="store_true")
    args = ap.parse_args()

    raw_root = Path(args.raw_root)
    pull_date = date.today().isoformat()
    ids = cached_game_ids(raw_root, args.season, args.timeout, args.rediscover)

    todo = [g for g in ids if not paired_snapshot_exists(raw_root, g)]
    done_before = len(ids) - len(todo)
    print(f"{args.season}: {len(ids)} games · {done_before} already on disk · "
          f"{len(todo)} to pull")
    if not todo:
        print("CORPUS COMPLETE — nothing to pull.")
        return

    session = todo[: args.limit] if args.limit else todo
    pulled, failed = 0, []
    started = time.monotonic()
    for index, game_id in enumerate(session, start=1):
        if pulled:
            time.sleep(args.sleep)
        ok = False
        for attempt in range(1, args.retries + 1):
            try:
                pbp_raw = playbyplayv3.PlayByPlayV3(
                    game_id=game_id, start_period=0, end_period=14,
                    timeout=args.timeout,
                ).get_dict()
                box_raw = boxscoretraditionalv3.BoxScoreTraditionalV3(
                    game_id=game_id, timeout=args.timeout,
                ).get_dict()
                ok = True
                break
            except Exception as exc:  # noqa: BLE001 — network boundary
                if attempt == args.retries:
                    failed.append((game_id, str(exc)))
                else:
                    delay = max(args.sleep, 1.0) * (2 ** attempt)
                    print(f"  {game_id} attempt {attempt} failed: {exc} — "
                          f"retry in {delay:.0f}s", flush=True)
                    time.sleep(delay)
        if not ok:
            continue
        # Both fetched before either is written: no half-pairs, ever.
        write_new(
            raw_root / "play-by-play" / game_id / f"{pull_date}.json",
            snapshot(game_id, pull_date, "NBA Stats PlayByPlayV3", pbp_raw),
        )
        write_new(
            raw_root / "box-score" / game_id / f"{pull_date}.json",
            snapshot(game_id, pull_date, "NBA Stats BoxScoreTraditionalV3", box_raw),
        )
        pulled += 1
        if index % 25 == 0 or index == len(session):
            rate = pulled / max(time.monotonic() - started, 1)
            remaining = len(todo) - index
            eta_min = remaining / rate / 60 if rate > 0 else 0
            print(f"[{index}/{len(session)}] pulled {pulled} · "
                  f"{rate * 60:.1f} games/min · ~{eta_min:.0f} min to corpus "
                  f"complete", flush=True)

    remaining = len(todo) - pulled
    print(f"\nsession done: {pulled} pulled · {len(failed)} failed · "
          f"{remaining} still missing")
    for game_id, error in failed:
        print(f"  FAILED {game_id}: {error}")
    if remaining:
        print("RERUN this command to continue (append-only; completed games skip).")
    else:
        print(f"CORPUS COMPLETE for {args.season}.")


if __name__ == "__main__":
    main()
