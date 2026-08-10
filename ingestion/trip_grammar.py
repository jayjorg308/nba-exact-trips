"""The versioned free-throw trip grammar, league-wide.

Ported from nba-analytics' derive_freethrow.py (the hero-grain original,
proven on 146 games and the 11-player pilot) and generalized to reconstruct
EVERY player's trips in a game.

Two modes:
- survey: an unclassifiable trip or oracle mismatch becomes an Anomaly
  record instead of a failure, so one pass over a whole corpus yields the
  complete triage list (the league-scale drift workflow).
- strict: the product repo's discipline — the first violation raises. The
  final dataset derive runs strict; survey exists to get there.

GRAMMAR VERSION 3 — the 2026-08-10 league triage (45 cases, two seasons,
every rule below written from inspected event windows; the box-score and
season oracles validate every one):

- v1: the nba-analytics hero grammar (same-clock grouping, N-of-M
  sequences, backward causing-foul scan).
- v2: pilot extensions (lane-violation-truncated trips; one-free-throw
  non-shooting fouls as away-from-play administrations) + multi-player.
- v3: PlayByPlayV3 stores amended events out of list order, so the causing
  foul is found via a whole-game (period, clock) foul index, with the
  backward scan as fallback and a period-boundary rule for administrations
  carried to the next quarter's start. One free throw from a shooting foul
  is classified as the and-one administration by rule (no other
  administration awards exactly one), covering replacement shooters,
  sub-second clock drift on the made basket, and goaltending-awarded
  baskets. Three free throws from any non-technical foul classify as a
  shooting foul on a three (no other administration awards three). The
  lane-violation truncation accepts any same-clock own-team turnover as
  the cancellation record while a sequence is an incomplete prefix (the
  scorer's subtype is sometimes blank), because mid-trip the ball is dead
  and an own-team turnover at the trip's clock can only be a free-throw
  violation; the box oracle validates every acceptance. A two-free-throw
  away-from-play foul is the penalty administration (bonus). Mid-trip
  declared-size corrections ("1 of 3" then "2 of 2") resolve to the final
  declared size. A period-opening trip with no same-clock foul inherits
  the previous period's last opponent non-technical foul (a deferred
  penalty administration whose foul event the feed misplaced).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

GRAMMAR_VERSION = 3

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

# Fallback backward scan (v1) for causing fouls whose clock drifted from the
# trip's; the primary search is the whole-game same-clock foul index.
FOUL_SEARCH_WINDOW = 12

# A made basket can carry a slightly different clock than its and-one free
# throw (0.1s drift observed); match within this tolerance.
AND_ONE_CLOCK_TOLERANCE = 1.0

CLOCK = re.compile(r"PT(\d+)M([\d.]+)S")


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
    # The and-one's made-shot actionNumber within the same game feed when the
    # shooter's own basket is identified; None otherwise (including
    # replacement-shooter administrations, where the scorer has no basket).
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


def clock_seconds(clock: str) -> float | None:
    match = CLOCK.fullmatch(clock)
    return int(match.group(1)) * 60 + float(match.group(2)) if match else None


def _team_of(actions: list, player_id: int) -> tuple[int, str]:
    for action in actions:
        if (
            isinstance(action, dict)
            and int(action.get("personId", 0)) == player_id
            and int(action.get("teamId", 0))
        ):
            return int(action["teamId"]), str(action.get("teamTricode", ""))
    return 0, ""


class _GameIndex:
    """Whole-game indexes; robust to PlayByPlayV3's amended-event list order."""

    def __init__(self, actions: list) -> None:
        self.actions = actions
        # (period, clock) -> [(teamId, subtype)] for non-technical fouls
        self.fouls: dict[tuple[int, str], list[tuple[int, str]]] = {}
        # personId -> [(period, seconds, clock, actionNumber)] for made shots
        self.made_shots: dict[int, list[tuple[int, float, str, int]]] = {}
        # (period, clock) -> [teamId] for trip-cancelling records: lane
        # Violations and ANY Turnover (mid-trip the ball is dead, so an
        # own-team turnover at the trip's clock is a free-throw violation
        # whatever subtype the scorer left on it)
        self.cancellations: dict[tuple[int, str], list[int]] = {}
        for action in actions:
            if not isinstance(action, dict):
                continue
            period = int(action.get("period", 0))
            clock = str(action.get("clock", ""))
            action_type = action.get("actionType")
            subtype = str(action.get("subType", ""))
            if action_type == "Foul":
                if "Technical" not in subtype and subtype != "Flopping":
                    self.fouls.setdefault((period, clock), []).append(
                        (int(action.get("teamId", 0)), subtype)
                    )
            elif action_type == "Made Shot":
                seconds = clock_seconds(clock)
                if seconds is not None:
                    self.made_shots.setdefault(int(action.get("personId", 0)), []).append(
                        (period, seconds, clock, int(action.get("actionNumber", -1)))
                    )
            elif (action_type == "Violation" and "Lane" in subtype) or (
                action_type == "Turnover"
            ):
                self.cancellations.setdefault((period, clock), []).append(
                    int(action.get("teamId", 0))
                )

    def causing_foul(
        self, first_index: int, period: int, clock: str, team_id: int
    ) -> str | None:
        """The opponent foul that caused a trip at (period, clock).

        Primary: the same-clock foul index (immune to list order). Fallback:
        the v1 backward scan (clock-drifted fouls). Last: the previous
        period's final-second fouls, for administrations carried to the next
        quarter's start.
        """
        candidates = [
            subtype
            for (foul_team, subtype) in self.fouls.get((period, clock), [])
            if foul_team != team_id
        ]
        if not candidates:
            for j in range(first_index - 1, max(-1, first_index - 1 - FOUL_SEARCH_WINDOW), -1):
                action = self.actions[j]
                if not isinstance(action, dict) or int(action.get("period", 0)) != period:
                    break
                if (
                    action.get("actionType") == "Foul"
                    and int(action.get("teamId", 0)) != team_id
                ):
                    subtype = str(action.get("subType", ""))
                    if "Technical" not in subtype and subtype != "Flopping":
                        candidates = [subtype]
                        break
        if not candidates and clock.startswith("PT12M00"):
            # A period-opening trip with no recorded foul: a deferred penalty
            # administration. Inherit the previous period's LAST opponent
            # non-technical foul (the one closest to the period's end).
            best: tuple[float, str] | None = None
            for (key, fouls) in self.fouls.items():
                if key[0] != period - 1:
                    continue
                seconds = clock_seconds(key[1])
                if seconds is None:
                    continue
                for (foul_team, subtype) in fouls:
                    if foul_team != team_id and (best is None or seconds < best[0]):
                        best = (seconds, subtype)
            if best is not None:
                candidates = [best[1]]
        if not candidates:
            return None
        for preferred in ("Shooting", "Away From Play", "Transition Take"):
            if preferred in candidates:
                return preferred
        return candidates[0]

    def own_made_shot(self, player_id: int, period: int, clock: str) -> int | None:
        """The shooter's own made basket at (or within tolerance of) the
        trip's clock — the and-one link."""
        anchor = clock_seconds(clock)
        best: tuple[float, int] | None = None
        for (shot_period, seconds, shot_clock, action_number) in self.made_shots.get(
            player_id, []
        ):
            if shot_period != period:
                continue
            if shot_clock == clock:
                return action_number
            if anchor is not None:
                drift = abs(seconds - anchor)
                if drift <= AND_ONE_CLOCK_TOLERANCE and (best is None or drift < best[0]):
                    best = (drift, action_number)
        return best[1] if best else None

    def own_team_cancellation(self, period: int, clock: str, team_id: int) -> bool:
        """A shooter's-team violation or turnover at the trip's clock — the
        record that the remaining attempt(s) were cancelled."""
        return team_id in self.cancellations.get((period, clock), [])


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

    game = _GameIndex(actions)
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
        by_position = sorted(events, key=lambda e: e[2])
        positions = [n for (_, _, n, _) in by_position]
        if len(declared_sizes) == 1:
            declared = declared_sizes.pop()
        elif (
            positions == list(range(1, len(events) + 1))
            and by_position[-1][3] == len(events)
        ):
            # Mid-trip scorer correction ("1 of 3" then "2 of 2"): the final
            # event's declared size is the corrected administration.
            declared = len(events)
        else:
            anomaly(player_id, name, period, clock, "mixed-declared-sizes",
                    str(sorted(declared_sizes)))
            continue
        fta = declared
        if positions != list(range(1, declared + 1)):
            # A gap-free prefix plus a same-clock lane violation by the
            # shooter's own team is a truncated trip — the violation
            # cancelled the remaining attempt(s); the box oracle still
            # checks the resulting line.
            is_prefix = positions == list(range(1, len(positions) + 1))
            if is_prefix and game.own_team_cancellation(period, clock, team_id):
                fta = len(positions)
            else:
                anomaly(player_id, name, period, clock, "partial-sequence",
                        f"{positions} of {declared}")
                continue
        ftm = sum(1 for (_, made, _, _) in events if made)
        first_index = events[0][0]

        shot_id: int | None = None
        if kind == "Flagrant":
            trip_class = "flagrant"
        elif kind == "Clear Path":
            trip_class = "clearPath"
        else:
            foul_subtype = game.causing_foul(first_index, period, clock, team_id)
            own_shot = game.own_made_shot(player_id, period, clock)
            if declared == 1 and own_shot is not None:
                trip_class = "andOne"
                shot_id = own_shot
            elif declared == 1 and foul_subtype in SHOOTING_FOULS:
                # One free throw from a shooting foul is the and-one
                # administration by rule; the scorer's basket is a teammate's
                # (replacement shooter) or unrecorded (goaltending award), so
                # no shot link exists.
                trip_class = "andOne"
            elif foul_subtype in SHOOTING_FOULS and declared == 2:
                trip_class = "shootingFoul2"
            elif declared == 3 and foul_subtype is not None:
                # Three free throws are awarded only for a foul on a
                # three-point attempt, whatever subtype the scorer chose.
                trip_class = "shootingFoul3"
            elif foul_subtype in BONUS_FOULS and declared == 2:
                trip_class = "bonus"
            elif foul_subtype == "Away From Play" and declared == 2:
                # In the penalty an away-from-play foul administers two free
                # throws with no retained possession — the bonus tier.
                trip_class = "bonus"
            elif foul_subtype == "Away From Play" and declared == 1:
                trip_class = "awayFromPlay"
            elif foul_subtype == "Transition Take" and declared == 1:
                trip_class = "transitionTake"
            elif foul_subtype in BONUS_FOULS and declared == 1:
                # One free throw from a non-shooting foul is the
                # away-from-play administration, whatever the scorer's foul
                # subtype.
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
