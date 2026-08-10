"""The versioned free-throw trip grammar, league-wide.

Ported from nba-analytics' derive_freethrow.py (the hero-grain original,
proven on 146 games and the 11-player pilot) and generalized to reconstruct
EVERY player's trips in a game. Includes the two pilot grammar extensions
(lane-violation-truncated trips; one-free-throw non-shooting fouls as
away-from-play administrations).

Two modes:
- survey: an unclassifiable trip or oracle mismatch becomes an Anomaly
  record instead of a failure, so one pass over a whole corpus yields the
  complete triage list (the league-scale drift workflow).
- strict: the product repo's discipline — the first violation raises. The
  final dataset derive runs strict; survey exists to get there.

GRAMMAR VERSION: 2 (v1 = nba-analytics hero grammar; v2 = pilot extensions
+ multi-player reconstruction).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

GRAMMAR_VERSION = 2

TRIP_CLASSES = (
    "shootingFoul2",
    "shootingFoul3",
    "bonus",
    "andOne",
    "flagrant",
    "awayFromPlay",
    "transitionTake",
    "clearPath",
)
ATTEMPT_EQUIVALENT = frozenset({"shootingFoul2", "shootingFoul3", "bonus"})

FT_SUBTYPE = re.compile(
    r"Free Throw(?: (?P<kind>Technical|Flagrant|Clear Path))?"
    r"(?: (?P<n>\d) of (?P<m>\d))?"
)

SHOOTING_FOULS = frozenset({"Shooting"})
BONUS_FOULS = frozenset({"Personal", "Loose Ball", "Personal Take", "Double Personal"})

# Actions scanned backward from a trip's first free throw for the causing
# foul and any same-clock own made shot (and-one detection).
FOUL_SEARCH_WINDOW = 12


class GrammarError(Exception):
    """Strict-mode violation: drift or an oracle breach."""


@dataclass(frozen=True)
class Trip:
    game_id: str
    player_id: int
    player_name: str
    team_id: int
    team_tricode: str
    period: int
    clock: str
    trip_class: str
    ftm: int
    fta: int
    # The and-one's made-shot actionNumber within the same game feed;
    # None for every other class.
    shot_id: int | None


@dataclass(frozen=True)
class Anomaly:
    game_id: str
    player_id: int
    player_name: str
    period: int
    clock: str
    reason: str
    detail: str


@dataclass
class GameReconstruction:
    trips: list[Trip] = field(default_factory=list)
    # player_id -> [technical_ftm, technical_fta]
    technicals: dict[int, list[int]] = field(default_factory=dict)
    anomalies: list[Anomaly] = field(default_factory=list)


def _team_of(actions: list, player_id: int) -> tuple[int, str]:
    for action in actions:
        if (
            isinstance(action, dict)
            and int(action.get("personId", 0)) == player_id
            and int(action.get("teamId", 0))
        ):
            return int(action["teamId"]), str(action.get("teamTricode", ""))
    return 0, ""


def _trip_context(
    actions: list, first_index: int, period: int, clock: str, player_id: int, team_id: int
) -> tuple[dict | None, str | None]:
    """The trip's same-clock own made shot and causing opponent foul."""
    and_one_shot: dict | None = None
    foul_subtype: str | None = None
    for j in range(first_index - 1, max(-1, first_index - 1 - FOUL_SEARCH_WINDOW), -1):
        action = actions[j]
        if not isinstance(action, dict) or int(action.get("period", 0)) != period:
            break
        action_type = action.get("actionType")
        if (
            and_one_shot is None
            and action_type == "Made Shot"
            and int(action.get("personId", 0)) == player_id
            and str(action.get("clock", "")) == clock
        ):
            and_one_shot = action
        if (
            foul_subtype is None
            and action_type == "Foul"
            and str(action.get("clock", "")) == clock
            and int(action.get("teamId", 0)) != team_id
        ):
            subtype = str(action.get("subType", ""))
            if "Technical" not in subtype and subtype != "Flopping":
                foul_subtype = subtype
        if and_one_shot is not None and foul_subtype is not None:
            break
    return and_one_shot, foul_subtype


def _lane_violation_at(actions: list, period: int, clock: str) -> bool:
    return any(
        isinstance(a, dict)
        and a.get("actionType") == "Violation"
        and "Lane" in str(a.get("subType", ""))
        and int(a.get("period", 0)) == period
        and str(a.get("clock", "")) == clock
        for a in actions
    )


def reconstruct_game(
    game_id: str, actions: list, *, strict: bool
) -> GameReconstruction:
    """Reconstruct every player's trips and technical lines for one game."""
    result = GameReconstruction()

    def anomaly(player_id: int, name: str, period: int, clock: str,
                reason: str, detail: str) -> None:
        if strict:
            raise GrammarError(
                f"game {game_id} P{period} {clock} {name}: {reason} — {detail}"
            )
        result.anomalies.append(
            Anomaly(game_id, player_id, name, period, clock, reason, detail)
        )

    # (player_id, period, clock, kind) -> [(index, made, n, m)]
    groups: dict[tuple[int, int, str, str], list[tuple[int, bool, int, int]]] = {}
    names: dict[int, str] = {}
    for index, action in enumerate(actions):
        if not isinstance(action, dict) or action.get("actionType") != "Free Throw":
            continue
        player_id = int(action.get("personId", 0))
        if player_id <= 0:
            anomaly(0, "?", int(action.get("period", 0)), str(action.get("clock", "")),
                    "free-throw-without-player", str(action.get("description", "")))
            continue
        names.setdefault(player_id, str(action.get("playerNameI") or action.get("playerName") or ""))
        subtype = str(action.get("subType", ""))
        match = FT_SUBTYPE.fullmatch(subtype)
        if not match:
            anomaly(player_id, names[player_id], int(action.get("period", 0)),
                    str(action.get("clock", "")), "unknown-ft-subtype", subtype)
            continue
        description = str(action.get("description", ""))
        if "Free Throw" not in description:
            anomaly(player_id, names[player_id], int(action.get("period", 0)),
                    str(action.get("clock", "")), "description-drift", description)
            continue
        made = not description.startswith("MISS")
        kind = match.group("kind") or "regular"
        if kind == "Technical":
            line = result.technicals.setdefault(player_id, [0, 0])
            line[0] += int(made)
            line[1] += 1
            continue
        if match.group("n") is None:
            anomaly(player_id, names[player_id], int(action.get("period", 0)),
                    str(action.get("clock", "")), "missing-sequence", subtype)
            continue
        key = (player_id, int(action.get("period", 0)), str(action.get("clock", "")), kind)
        groups.setdefault(key, []).append(
            (index, made, int(match.group("n")), int(match.group("m")))
        )

    teams: dict[int, tuple[int, str]] = {}
    for key in sorted(groups, key=lambda k: groups[k][0][0]):
        player_id, period, clock, kind = key
        name = names.get(player_id, "")
        events = groups[key]
        if player_id not in teams:
            teams[player_id] = _team_of(actions, player_id)
        team_id, tricode = teams[player_id]
        if team_id == 0:
            anomaly(player_id, name, period, clock, "no-team-identity", "")
            continue

        declared_sizes = {declared for (_, _, _, declared) in events}
        if len(declared_sizes) != 1:
            anomaly(player_id, name, period, clock, "mixed-declared-sizes",
                    str(sorted(declared_sizes)))
            continue
        declared = declared_sizes.pop()
        numbers = sorted(number for (_, _, number, _) in events)
        fta = declared
        if numbers != list(range(1, declared + 1)):
            # Extension 1 (pilot): a gap-free prefix plus a same-clock lane
            # violation is a truncated trip — the violation cancelled the
            # remaining attempt(s); the box oracle still checks the line.
            is_prefix = numbers == list(range(1, len(numbers) + 1))
            if is_prefix and _lane_violation_at(actions, period, clock):
                fta = len(numbers)
            else:
                anomaly(player_id, name, period, clock, "partial-sequence",
                        f"{numbers} of {declared}")
                continue
        ftm = sum(1 for (_, made, _, _) in events if made)
        first_index = events[0][0]

        shot_id: int | None = None
        if kind == "Flagrant":
            trip_class = "flagrant"
        elif kind == "Clear Path":
            trip_class = "clearPath"
        else:
            and_one_shot, foul_subtype = _trip_context(
                actions, first_index, period, clock, player_id, team_id
            )
            if declared == 1 and and_one_shot is not None:
                trip_class = "andOne"
                shot_id = int(and_one_shot.get("actionNumber", -1))
            elif foul_subtype in SHOOTING_FOULS and declared == 2:
                trip_class = "shootingFoul2"
            elif foul_subtype in SHOOTING_FOULS and declared == 3:
                trip_class = "shootingFoul3"
            elif foul_subtype in BONUS_FOULS and declared == 2:
                trip_class = "bonus"
            elif foul_subtype == "Away From Play" and declared == 1:
                trip_class = "awayFromPlay"
            elif foul_subtype == "Transition Take" and declared == 1:
                trip_class = "transitionTake"
            elif foul_subtype in BONUS_FOULS and declared == 1:
                # Extension 2 (pilot): one free throw from a non-shooting foul
                # is the away-from-play administration, whatever the scorer's
                # foul subtype.
                trip_class = "awayFromPlay"
            else:
                anomaly(player_id, name, period, clock, "unclassifiable",
                        f"M={declared}, causing foul {foul_subtype!r}")
                continue
        result.trips.append(
            Trip(
                game_id=game_id,
                player_id=player_id,
                player_name=name,
                team_id=team_id,
                team_tricode=tricode,
                period=period,
                clock=clock,
                trip_class=trip_class,
                ftm=ftm,
                fta=fta,
                shot_id=shot_id,
            )
        )
    return result


def box_free_throw_lines(box_game: dict) -> dict[int, tuple[int, int]]:
    """Every player's official (FTM, FTA) from the box score."""
    lines: dict[int, tuple[int, int]] = {}
    for side in ("homeTeam", "awayTeam"):
        team = box_game.get(side)
        if not isinstance(team, dict):
            raise GrammarError(f"box score missing {side}")
        for player in team.get("players", []) or []:
            if not isinstance(player, dict):
                continue
            stats = player.get("statistics")
            if not isinstance(stats, dict):
                continue
            try:
                lines[int(player.get("personId", 0))] = (
                    int(stats["freeThrowsMade"]),
                    int(stats["freeThrowsAttempted"]),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise GrammarError(f"unreadable box free-throw line: {exc}") from exc
    return lines
