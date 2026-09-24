"""Per-game player lines from the box-score corpus — the analysis layer's
denominators and team histories, committed so the analysis reproduces
from a fresh clone without touching stats.nba.com.

Per season: data/derived/<season>/player_games.csv — one row per player
who logged minutes in a game (game_id, player_id, player_name,
team_tricode, min, fgm, fga, fta, ftm, pts), sorted by game, team,
player — plus player_games.meta.json (provenance and oracle results).

Oracle: per player-season sums must equal the league totals artifact
EXACTLY for FTA, FTM, and PTS (hard-fail otherwise). FGA is compared and
every disagreement is recorded in the meta sidecar: the two NBA endpoints
are known to disagree by a single attempt for a handful of players (a
stat correction applied to one feed and not the other). The analysis
uses the box-score sums, which are self-consistent with the per-game
splits it needs.

  python ingestion/derive_player_games.py --season 2025-26
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
)
from derive_league_trips import latest_league_totals  # noqa: E402

COLUMNS = ("game_id", "player_id", "player_name", "team_tricode", "min",
           "fgm", "fga", "fta", "ftm", "pts")
ORACLE_EXACT = ("fta", "ftm", "pts")


def parse_minutes(text: str) -> float:
    """Box-score minutes are 'MM:SS'; a blank means the player did not play."""
    minutes, seconds = text.split(":")
    return int(minutes) + int(seconds) / 60


def league_totals(path: Path, season: str) -> dict[int, dict]:
    artifact = load(path)
    meta = artifact.get("_meta", {})
    if str(meta.get("season", "")) != season or meta.get("per_mode") != "Totals":
        raise CorpusError(f"league totals artifact mismatch: {path}")
    result = artifact["response"]["resultSets"][0]
    headers = result["headers"]
    col = {name: headers.index(name) for name in
           ("PLAYER_ID", "PLAYER_NAME", "GP", "FGA", "FTA", "FTM", "PTS")}
    return {
        int(row[col["PLAYER_ID"]]): {
            "name": str(row[col["PLAYER_NAME"]]),
            "gp": int(row[col["GP"]]),
            "fga": int(row[col["FGA"]]),
            "fta": int(row[col["FTA"]]),
            "ftm": int(row[col["FTM"]]),
            "pts": int(row[col["PTS"]]),
        }
        for row in result["rowSet"]
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Derive per-game player lines.")
    ap.add_argument("--season", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out-root", default="data/derived")
    args = ap.parse_args()

    raw_root = Path(args.raw_root)
    game_ids = season_game_ids_on_disk(raw_root, args.season)
    if not game_ids:
        sys.exit(f"no {args.season} games in {raw_root} — run pull_league_games.py")
    totals_path = latest_league_totals(raw_root, args.season)
    if totals_path is None:
        sys.exit("the oracle requires a league totals artifact — run pull_league_totals.py")
    league = league_totals(totals_path, args.season)

    rows: list[dict] = []
    for game_id in game_ids:
        pair = latest_pair_paths(raw_root, game_id)
        if pair is None:
            sys.exit(f"{game_id}: no complete play-by-play/box-score pair on disk")
        box = load(pair[1])["response"]["boxScoreTraditional"]
        if str(box["gameId"]) != game_id:
            raise CorpusError(f"{game_id}: box-score payload game ID disagrees")
        for side in ("homeTeam", "awayTeam"):
            team = box[side]
            for player in team["players"]:
                stats = player["statistics"]
                if not stats or not stats.get("minutes"):
                    continue
                rows.append({
                    "game_id": game_id,
                    "player_id": int(player["personId"]),
                    "player_name": f"{player['firstName']} {player['familyName']}".strip(),
                    "team_tricode": str(team["teamTricode"]),
                    "min": round(parse_minutes(stats["minutes"]), 2),
                    "fgm": int(stats["fieldGoalsMade"]),
                    "fga": int(stats["fieldGoalsAttempted"]),
                    "fta": int(stats["freeThrowsAttempted"]),
                    "ftm": int(stats["freeThrowsMade"]),
                    "pts": int(stats["points"]),
                })
    rows.sort(key=lambda r: (r["game_id"], r["team_tricode"], r["player_id"]))

    # Oracle against the league totals artifact.
    sums: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for row in rows:
        for key in ("gp", "fga", "fta", "ftm", "pts"):
            sums[row["player_id"]][key] += 1 if key == "gp" else row[key]
    exact_failures = []
    fga_disagreements = []
    gp_disagreements = []
    for player_id, line in league.items():
        mine = sums.get(player_id)
        if mine is None:
            exact_failures.append(f"{line['name']} ({player_id}): absent from box scores")
            continue
        for key in ORACLE_EXACT:
            if mine[key] != line[key]:
                exact_failures.append(
                    f"{line['name']} ({player_id}): {key} box-score {mine[key]} "
                    f"vs artifact {line[key]}")
        if mine["fga"] != line["fga"]:
            fga_disagreements.append({
                "playerId": player_id, "name": line["name"],
                "boxScoreFga": mine["fga"], "artifactFga": line["fga"],
            })
        if mine["gp"] != line["gp"]:
            gp_disagreements.append({
                "playerId": player_id, "name": line["name"],
                "boxScoreGp": mine["gp"], "artifactGp": line["gp"],
            })
    unlisted = sorted(set(sums) - set(league))
    if exact_failures:
        sys.exit("ORACLE FAILED (FTA/FTM/PTS must reconcile exactly):\n  "
                 + "\n  ".join(exact_failures))

    out_dir = Path(args.out_root) / args.season
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "player_games.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    meta = {
        "season": args.season,
        "deriveDate": date.today().isoformat(),
        "games": len(game_ids),
        "playerGames": len(rows),
        "playerSeasons": len(sums),
        "oracle": {
            "artifact": str(totals_path).replace("\\", "/"),
            "artifactPlayers": len(league),
            "exactFtaFtmPts": len(league),
            "fgaDisagreements": fga_disagreements,
            "gpDisagreements": gp_disagreements,
            "playersNotInArtifact": unlisted,
        },
    }
    (out_dir / "player_games.meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"{args.season}: {len(rows):,} player-games across {len(game_ids):,} games, "
          f"{len(sums)} player-seasons; FTA/FTM/PTS exact for all {len(league)} "
          f"artifact players; FGA disagreements: {len(fga_disagreements)}; "
          f"GP disagreements: {len(gp_disagreements)}; not in artifact: {len(unlisted)}")
    for item in fga_disagreements:
        print(f"  FGA {item['name']}: box-score {item['boxScoreFga']} vs artifact {item['artifactFga']}")
    print(f"-> {csv_path}")


if __name__ == "__main__":
    main()
