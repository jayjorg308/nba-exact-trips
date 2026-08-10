"""Pilot trip derive: reuse nba-analytics' proven free-throw reconstruction
(grammar + oracle battery) for players outside its hero registry, extending
the versioned grammar for two cases the hero corpus never produced:

1. TRUNCATED TRIP (lane violation): a declared N-of-M sequence legitimately
   missing its tail because a lane violation cancelled the remaining attempt
   (first observed: Markkanen, game 0022500098 — FT 1 of 2, then a double
   lane violation and a jump ball). Accepted only when a same-period,
   same-clock lane Violation event exists; fta counts free throws actually
   shot. The per-game box-score oracle still verifies the line.

2. ONE-SHOT NON-SHOOTING TRIP (away-from-play administration): a declared
   1-of-1 caused by a non-shooting foul (first observed: Kyshawn George,
   game 0022500592 — loose-ball foul at the same clock as a teammate's made
   three, one free throw awarded). The NBA's one-free-throw administration
   for non-shooting fouls is the away-from-play family, so the trip
   classifies awayFromPlay.

PILOT CAVEAT: a truncated bonus trip carries fta=1, which the product Zod
schema's per-class bounds would reject — pilot payloads are for analysis,
not deployment. The real research pipeline will carry its own schema.

Run from the nba-analytics repo root (raw corpus + derive modules live
there):
  python ../nba-exact-trips/ingestion/pilot_derive_trips.py \
      --shot-payload-file data/derived/<slug>/<season>/<date>.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

NBA_ANALYTICS = Path(__file__).resolve().parents[2] / "nba-analytics"
sys.path.insert(0, str(NBA_ANALYTICS / "ingestion"))

import derive_freethrow as df  # noqa: E402  (the proven grammar + oracles)


def _lane_violation_at(actions: list, period: int, clock: str) -> bool:
    return any(
        isinstance(a, dict)
        and a.get("actionType") == "Violation"
        and "Lane" in str(a.get("subType", ""))
        and int(a.get("period", 0)) == period
        and str(a.get("clock", "")) == clock
        for a in actions
    )


def reconstruct_game_trips_extended(
    game_id: str, actions: list, player_id: int, made_shot_ids: set[int]
) -> tuple[list, int, int]:
    """df.reconstruct_game_trips with the two pilot grammar extensions."""
    hero_team = 0
    for action in actions:
        if (
            isinstance(action, dict)
            and int(action.get("personId", 0)) == player_id
            and int(action.get("teamId", 0))
        ):
            hero_team = int(action["teamId"])
            break

    groups: dict[tuple[int, str, str], list[tuple[int, bool, int, int]]] = {}
    technical_ftm = technical_fta = 0
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or action.get("actionType") != "Free Throw":
            continue
        if int(action.get("personId", 0)) != player_id:
            continue
        subtype = str(action.get("subType", ""))
        match = df.FT_SUBTYPE.fullmatch(subtype)
        if not match:
            df.fail(
                f"game {game_id} action {action.get('actionNumber')}: "
                f"unknown free-throw subtype {subtype!r}"
            )
        description = str(action.get("description", ""))
        if "Free Throw" not in description:
            df.fail(
                f"game {game_id} action {action.get('actionNumber')}: "
                f"free-throw description grammar drift: {description!r}"
            )
        made = not description.startswith("MISS")
        kind = match.group("kind") or "regular"
        if kind == "Technical":
            technical_fta += 1
            technical_ftm += int(made)
            continue
        if match.group("n") is None:
            df.fail(
                f"game {game_id} action {action.get('actionNumber')}: "
                f"non-technical free throw without an N-of-M sequence: {subtype!r}"
            )
        key = (int(action.get("period", 0)), str(action.get("clock", "")), kind)
        groups.setdefault(key, []).append(
            (index, made, int(match.group("n")), int(match.group("m")))
        )

    if groups and hero_team == 0:
        df.fail(f"game {game_id}: hero has free throws but no team identity")

    trips: list[df.Trip] = []
    for key in sorted(groups, key=lambda k: groups[k][0][0]):
        period, clock, kind = key
        events = groups[key]
        declared_sizes = {declared for (_, _, _, declared) in events}
        if len(declared_sizes) != 1:
            df.fail(
                f"game {game_id} P{period} {clock}: trip mixes declared sizes "
                f"{sorted(declared_sizes)}"
            )
        declared = declared_sizes.pop()
        numbers = sorted(number for (_, _, number, _) in events)
        fta = declared
        if numbers != list(range(1, declared + 1)):
            # Extension 1: a gap-free PREFIX of the declared sequence plus a
            # same-clock lane violation is a truncated trip, not corruption —
            # the violation cancelled the remaining attempt(s). The box-score
            # oracle still checks the resulting line.
            is_prefix = numbers == list(range(1, len(numbers) + 1))
            if is_prefix and _lane_violation_at(actions, period, clock):
                fta = len(numbers)
            else:
                df.fail(
                    f"game {game_id} P{period} {clock}: partial or duplicated "
                    f"trip sequence {numbers} of {declared} — investigate "
                    f"before persisting"
                )
        ftm = sum(1 for (_, made, _, _) in events if made)
        first_index = events[0][0]

        shot_id: int | None = None
        if kind == "Flagrant":
            trip_class = "flagrant"
        elif kind == "Clear Path":
            trip_class = "clearPath"
        else:
            and_one_shot, foul_subtype = df._trip_context(
                actions, first_index, period, clock, player_id, hero_team
            )
            if declared == 1 and and_one_shot is not None:
                trip_class = "andOne"
                shot_id = int(and_one_shot.get("actionNumber", -1))
                if shot_id not in made_shot_ids:
                    df.fail(
                        f"game {game_id}: and-one linkage failed — made shot "
                        f"{shot_id} absent from the sibling shot payload"
                    )
            elif foul_subtype in df.SHOOTING_FOULS and declared == 2:
                trip_class = "shootingFoul2"
            elif foul_subtype in df.SHOOTING_FOULS and declared == 3:
                trip_class = "shootingFoul3"
            elif foul_subtype in df.BONUS_FOULS and declared == 2:
                trip_class = "bonus"
            elif foul_subtype == "Away From Play" and declared == 1:
                trip_class = "awayFromPlay"
            elif foul_subtype == "Transition Take" and declared == 1:
                trip_class = "transitionTake"
            elif foul_subtype in df.BONUS_FOULS and declared == 1:
                # Extension 2: one free throw from a non-shooting foul is the
                # away-from-play administration, whatever the scorer's foul
                # subtype (first observed as 'Loose Ball' beside a teammate's
                # same-clock made basket).
                trip_class = "awayFromPlay"
            else:
                df.fail(
                    f"game {game_id} P{period} {clock}: unclassifiable trip "
                    f"(M={declared}, causing foul {foul_subtype!r}) — "
                    f"taxonomy totality"
                )
        trips.append(
            df.Trip(
                game_id=game_id,
                period=period,
                clock=clock,
                trip_class=trip_class,
                ftm=ftm,
                fta=fta,
                shot_id=shot_id,
            )
        )
    return trips, technical_ftm, technical_fta


def main() -> None:
    ap = argparse.ArgumentParser(description="Pilot trip derive (research repo).")
    ap.add_argument("--shot-payload-file", required=True)
    ap.add_argument("--raw-root", default="data/raw")
    ap.add_argument("--out-root", default=str(Path(__file__).resolve().parents[1] / "data" / "derived"))
    args = ap.parse_args()

    df.reconstruct_game_trips = reconstruct_game_trips_extended

    shot = df._load(Path(args.shot_payload_file))
    meta = shot.get("_meta", {})
    season = str(meta.get("season", ""))
    player_id = int(meta.get("playerId", 0))
    games = df.load_freethrow_game_snapshots(
        shot, Path(args.raw_root), player_id, allow_missing_games=False
    )
    league_path = df._latest_league_totals(Path(args.raw_root), season)
    league = df._load(league_path)

    payload = df.derive(
        shot,
        games,
        league,
        source_shot_payload=args.shot_payload_file,
        source_league_totals=str(league_path).replace("\\", "/"),
    )
    slug = str(payload["_meta"]["player"]).lower().replace(" ", "-")
    out_path = Path(args.out_root) / slug / f"{season}.freethrow.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"pilot free-throw payload -> {out_path}")


if __name__ == "__main__":
    main()
