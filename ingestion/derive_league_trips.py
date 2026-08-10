"""Derive a season's league-wide trip dataset from the raw game corpus.

Two modes (see trip_grammar):
- --mode survey (default): process every game, collect every grammar gap and
  oracle mismatch into anomalies.csv — the triage list that drives grammar
  extensions. Partial corpora are fine; the season oracle reports coverage
  instead of failing.
- --mode strict: the dataset run. Every trip classifies, every player-game
  reconciles with the box score, and (when the corpus is complete) every
  player-season reconciles exactly with the league totals artifact. Any
  violation fails the derive; nothing partial is written.

Outputs under data/derived/<season>/:
  trips.csv        one row per trip (the open dataset's core table)
  players.csv      per player-season: totals, per-class counts, oracle status
  anomalies.csv    survey mode: the triage list (absent when empty)
  meta.json        provenance: games, grammar version, mode, oracle results

Usage:
  python ingestion/derive_league_trips.py --season 2025-26
  python ingestion/derive_league_trips.py --season 2025-26 --mode strict
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corpus import (  # noqa: E402
    CorpusError,
    latest_pair_paths,
    load,
    season_game_ids_on_disk,
    validate_game_pair,
)
from trip_grammar import (  # noqa: E402
    ATTEMPT_EQUIVALENT,
    Anomaly,
    GRAMMAR_VERSION,
    GrammarError,
    TRIP_CLASSES,
    box_free_throw_lines,
    reconstruct_game,
)


def latest_league_totals(raw_root: Path, season: str) -> Path | None:
    totals_dir = raw_root / "_league" / season / "totals"
    files = sorted(totals_dir.glob("*.json")) if totals_dir.exists() else []
    return files[-1] if files else None


def league_totals_lines(path: Path, season: str) -> dict[int, tuple[int, int, str]]:
    """player_id -> (season FTM, season FTA, player name) from the artifact."""
    artifact = load(path)
    meta = artifact.get("_meta", {})
    if str(meta.get("season", "")) != season or meta.get("per_mode") != "Totals":
        raise CorpusError(f"league totals artifact mismatch: {path}")
    result = artifact["response"]["resultSets"][0]
    if result.get("name") != "LeagueDashPlayerStats":
        raise CorpusError("league totals artifact first result set is unexpected")
    headers = result["headers"]
    col = {name: headers.index(name) for name in ("PLAYER_ID", "PLAYER_NAME", "FTM", "FTA")}
    return {
        int(row[col["PLAYER_ID"]]): (
            int(row[col["FTM"]]),
            int(row[col["FTA"]]),
            str(row[col["PLAYER_NAME"]]),
        )
        for row in result["rowSet"]
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive the league-wide trip dataset.")
    ap.add_argument("--season", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out-root", default="data/derived")
    ap.add_argument("--mode", choices=["survey", "strict"], default="survey")
    args = ap.parse_args()

    strict = args.mode == "strict"
    raw_root = Path(args.raw_root)
    game_ids = season_game_ids_on_disk(raw_root, args.season)
    if not game_ids:
        sys.exit(f"no {args.season} games in {raw_root} — run pull_league_games.py")

    all_trips = []
    anomalies = []
    technicals: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    names: dict[int, str] = {}
    box_mismatch_games = 0
    source_games = []

    for index, game_id in enumerate(game_ids, start=1):
        pair = latest_pair_paths(raw_root, game_id)
        if pair is None:
            sys.exit(f"game {game_id} listed but pairless — corpus corruption")
        pbp_snapshot, box_snapshot = load(pair[0]), load(pair[1])
        try:
            pbp_game, box_game, parsed_id = validate_game_pair(pbp_snapshot, box_snapshot)
        except CorpusError as exc:
            sys.exit(f"game {game_id}: {exc}")
        if parsed_id != game_id:
            sys.exit(f"snapshot directory {game_id} != parsed game ID {parsed_id}")
        actions = pbp_game.get("actions")
        if not isinstance(actions, list):
            sys.exit(f"game {game_id}: play-by-play game missing actions")

        try:
            recon = reconstruct_game(game_id, actions, strict=strict)
        except GrammarError as exc:
            sys.exit(f"grammar violation (strict): {exc}")
        all_trips.extend(recon.trips)
        anomalies.extend(recon.anomalies)
        for player_id, (ftm, fta) in ((p, tuple(v)) for p, v in recon.technicals.items()):
            technicals[player_id][0] += ftm
            technicals[player_id][1] += fta

        # Per-player per-game box oracle.
        game_lines: dict[int, list[int]] = defaultdict(lambda: [0, 0])
        for trip in recon.trips:
            names.setdefault(trip.player_id, trip.player_name)
            game_lines[trip.player_id][0] += trip.ftm
            game_lines[trip.player_id][1] += trip.fta
        for player_id, (ftm, fta) in recon.technicals.items():
            game_lines[player_id][0] += ftm
            game_lines[player_id][1] += fta
        box_lines = box_free_throw_lines(box_game)
        game_ok = True
        for player_id, expected in box_lines.items():
            got = tuple(game_lines.get(player_id, [0, 0]))
            if got != expected:
                game_ok = False
                message = (f"reconstructed {got[0]}/{got[1]} != box "
                           f"{expected[0]}/{expected[1]}")
                if strict:
                    sys.exit(f"box oracle failed: game {game_id} player "
                             f"{player_id}: {message}")
                anomalies.append(Anomaly(
                    game_id, player_id, names.get(player_id, ""), 0, "",
                    "box-mismatch", message,
                ))
        for player_id in game_lines:
            if player_id not in box_lines and any(game_lines[player_id]):
                sys.exit(f"game {game_id}: reconstructed line for player "
                         f"{player_id} absent from box score")
        box_mismatch_games += 0 if game_ok else 1

        source_games.append({
            "gameId": game_id,
            "pullDate": str(pbp_snapshot["_meta"]["pull_date"]),
        })
        if index % 100 == 0 or index == len(game_ids):
            print(f"[{index}/{len(game_ids)}] {len(all_trips)} trips · "
                  f"{len(anomalies)} anomalies", flush=True)

    # Season oracle against the league totals artifact.
    totals_path = latest_league_totals(raw_root, args.season)
    season_oracle: dict = {"artifact": None}
    if totals_path is not None:
        league_lines = league_totals_lines(totals_path, args.season)
        recon_lines: dict[int, list[int]] = defaultdict(lambda: [0, 0])
        for trip in all_trips:
            recon_lines[trip.player_id][0] += trip.ftm
            recon_lines[trip.player_id][1] += trip.fta
        for player_id, (ftm, fta) in technicals.items():
            recon_lines[player_id][0] += ftm
            recon_lines[player_id][1] += fta
        exact = short = over = 0
        for player_id, (ftm, fta, name) in league_lines.items():
            got = tuple(recon_lines.get(player_id, [0, 0]))
            if got == (ftm, fta):
                exact += 1
            elif got[1] < fta:
                short += 1  # missing games in a partial corpus, or drift
            else:
                over += 1
                if strict:
                    sys.exit(f"season oracle: {name} reconstructed {got} exceeds "
                             f"league line {ftm}/{fta} — contradiction")
            names.setdefault(player_id, name)
        season_oracle = {
            "artifact": str(totals_path).replace("\\", "/"),
            "playersExact": exact,
            "playersShort": short,
            "playersOver": over,
        }
        if strict and (short or over):
            sys.exit(f"season oracle failed: {short} short, {over} over — "
                     f"corpus incomplete or grammar drifted")
        print(f"season oracle: {exact} exact · {short} short · {over} over "
              f"(vs {totals_path.name})")
    elif strict:
        sys.exit("strict mode requires a league totals artifact — "
                 "run pull_league_totals.py")

    # Outputs.
    out_dir = Path(args.out_root) / args.season
    out_dir.mkdir(parents=True, exist_ok=True)

    with (out_dir / "trips.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["game_id", "player_id", "player_name", "team_id",
                         "team_tricode", "period", "clock", "trip_class",
                         "tier", "ftm", "fta", "and_one_shot_id"])
        for trip in all_trips:
            writer.writerow([
                trip.game_id, trip.player_id, trip.player_name, trip.team_id,
                trip.team_tricode, trip.period, trip.clock, trip.trip_class,
                "attemptEquivalent" if trip.trip_class in ATTEMPT_EQUIVALENT
                else "addOn",
                trip.ftm, trip.fta,
                "" if trip.shot_id is None else trip.shot_id,
            ])

    per_player: dict[int, dict] = {}
    for trip in all_trips:
        row = per_player.setdefault(trip.player_id, {
            "player_id": trip.player_id,
            "player_name": names.get(trip.player_id, trip.player_name),
            "trips": 0, "trip_ftm": 0, "trip_fta": 0,
            **{f"n_{c}": 0 for c in TRIP_CLASSES},
        })
        row["trips"] += 1
        row["trip_ftm"] += trip.ftm
        row["trip_fta"] += trip.fta
        row[f"n_{trip.trip_class}"] += 1
    for player_id, (ftm, fta) in technicals.items():
        row = per_player.setdefault(player_id, {
            "player_id": player_id, "player_name": names.get(player_id, ""),
            "trips": 0, "trip_ftm": 0, "trip_fta": 0,
            **{f"n_{c}": 0 for c in TRIP_CLASSES},
        })
        row["technical_ftm"] = ftm
        row["technical_fta"] = fta
    with (out_dir / "players.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["player_id", "player_name", "trips", "trip_ftm", "trip_fta",
                  "technical_ftm", "technical_fta"] + [f"n_{c}" for c in TRIP_CLASSES]
        writer = csv.DictWriter(handle, fieldnames=fields, restval=0)
        writer.writeheader()
        for row in sorted(per_player.values(), key=lambda r: -r["trip_fta"]):
            writer.writerow(row)

    anomalies_path = out_dir / "anomalies.csv"
    if anomalies:
        with anomalies_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["game_id", "player_id", "player_name", "period",
                             "clock", "reason", "detail"])
            for a in anomalies:
                writer.writerow([a.game_id, a.player_id, a.player_name,
                                 a.period, a.clock, a.reason, a.detail])
    elif anomalies_path.exists():
        anomalies_path.unlink()

    reasons: dict[str, int] = defaultdict(int)
    for a in anomalies:
        reasons[a.reason] += 1
    (out_dir / "meta.json").write_text(json.dumps({
        "season": args.season,
        "mode": args.mode,
        "grammarVersion": GRAMMAR_VERSION,
        "deriveDate": date.today().isoformat(),
        "gamesProcessed": len(game_ids),
        "trips": len(all_trips),
        "players": len(per_player),
        "anomalies": dict(sorted(reasons.items())),
        "gamesWithBoxMismatch": box_mismatch_games,
        "seasonOracle": season_oracle,
    }, indent=2), encoding="utf-8")

    print(f"\n{args.mode} derive: {len(all_trips)} trips · {len(per_player)} "
          f"players · {len(game_ids)} games · {len(anomalies)} anomalies "
          f"({dict(sorted(reasons.items())) or 'none'})")
    print(f"outputs -> {out_dir}")


if __name__ == "__main__":
    main()
