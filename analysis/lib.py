"""Shared analysis loaders and statistics over the committed datasets: the
trip layer (trips.csv, players.csv) joined to the per-game box-score lines
(player_games.csv — denominators, exposure, and team histories). Nothing
here reads data/raw, so a fresh clone reproduces every report."""

from __future__ import annotations

import csv
import math
import random
from collections import defaultdict
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parent
RESEARCH = ANALYSIS.parent
DERIVED = RESEARCH / "data" / "derived"

TRIP_CLASSES = (
    "shootingFoul2", "shootingFoul3", "bonus", "andOne",
    "flagrant", "awayFromPlay", "transitionTake", "clearPath",
)
ATTEMPT_EQUIVALENT = {"shootingFoul2", "shootingFoul3", "bonus"}
OTHER_ADDON = ("flagrant", "awayFromPlay", "transitionTake", "clearPath")


# ---- loaders ------------------------------------------------------------

def player_games(season: str) -> list[dict]:
    """player_games.csv, typed, in file (game) order."""
    rows: list[dict] = []
    with (DERIVED / season / "player_games.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rows.append({
                "game_id": row["game_id"],
                "player_id": int(row["player_id"]),
                "name": row["player_name"],
                "team": row["team_tricode"],
                "min": float(row["min"]),
                **{k: int(row[k]) for k in ("fgm", "fga", "fta", "ftm", "pts")},
            })
    return rows


def season_lines(season: str) -> dict[int, dict]:
    """Per player-season sums and team history from the per-game lines.
    `teams` lists the distinct teams in the order played; `team` joins
    them ("MIA/GSW" for a midseason move)."""
    lines: dict[int, dict] = {}
    for row in player_games(season):
        line = lines.get(row["player_id"])
        if line is None:
            line = lines[row["player_id"]] = {
                "name": row["name"], "teams": [], "gp": 0, "min": 0.0,
                "fgm": 0, "fga": 0, "fta": 0, "ftm": 0, "pts": 0,
            }
        if row["team"] not in line["teams"]:
            line["teams"].append(row["team"])
        line["gp"] += 1
        line["min"] += row["min"]
        for key in ("fgm", "fga", "fta", "ftm", "pts"):
            line[key] += row[key]
    for line in lines.values():
        line["team"] = "/".join(line["teams"])
    return lines


def player_seasons(season: str) -> dict[int, dict]:
    """players.csv joined to the per-game sums, plus derived metrics."""
    totals = season_lines(season)
    path = DERIVED / season / "players.csv"
    players: dict[int, dict] = {}
    with path.open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = int(row["player_id"])
            line = totals.get(player_id)
            if line is None:
                continue
            n = {c: int(row[f"n_{c}"]) for c in TRIP_CLASSES}
            trips = int(row["trips"])
            ae = sum(n[c] for c in ATTEMPT_EQUIVALENT)
            fga, fta, ftm, pts = line["fga"], line["fta"], line["ftm"], line["pts"]
            record = {
                "player_id": player_id,
                "season": season,
                **line,
                "trips": trips,
                "n": n,
                "aeTrips": ae,
                "technicalFta": int(row["technical_fta"]),
                "technicalFtm": int(row["technical_ftm"]),
            }
            if fga > 0:
                for c in TRIP_CLASSES:
                    record[f"{c}Per100Fga"] = 100 * n[c] / fga
                record["otherAddonPer100Fga"] = 100 * sum(n[c] for c in OTHER_ADDON) / fga
                record["tripsPer100Fga"] = 100 * trips / fga
                record["ftaRate"] = fta / fga
                record["fieldPps"] = (pts - ftm) / fga
                record["tsConv"] = pts / (2 * (fga + 0.44 * fta))
                record["tsExact"] = pts / (2 * (fga + ae))
                record["tsDeltaPp"] = 100 * (record["tsExact"] - record["tsConv"])
            if fta > 0:
                record["conversion"] = ftm / fta
                record["trueCoef"] = ae / fta
                record["twoShotEv"] = 2 * record["conversion"]
                if fga > 0:
                    record["premium"] = record["twoShotEv"] - record["fieldPps"]
            if trips > 0:
                for c in TRIP_CLASSES:
                    record[f"{c}Share"] = n[c] / trips
            players[player_id] = record
    return players


# ---- panels and the context test ----------------------------------------

def build_panel(prior: dict, current: dict, min_fga: int) -> list[tuple[dict, dict]]:
    """Consecutive-season pairs for players at or above the FGA bar with at
    least one trip in both seasons."""
    return [
        (prior[p], current[p])
        for p in sorted(set(prior) & set(current))
        if prior[p]["fga"] >= min_fga and current[p]["fga"] >= min_fga
        and prior[p].get("trips", 0) > 0 and current[p].get("trips", 0) > 0
    ]


def corr(panel: list[tuple[dict, dict]], key: str, method=None) -> float:
    method = method or pearson
    xs = [a[key] for (a, b) in panel if key in a and key in b]
    ys = [b[key] for (a, b) in panel if key in a and key in b]
    return method(xs, ys)


def classify_transition(a: dict, b: dict) -> str:
    """A consecutive-season pair by game-level team history: 'stayer' (one
    team in both seasons, the same one), 'mover' (one team each season,
    different), or 'mixed' (a midseason change in either season)."""
    if len(a["teams"]) > 1 or len(b["teams"]) > 1:
        return "mixed"
    return "stayer" if a["teams"] == b["teams"] else "mover"


def fisher_p(r1: float, n1: int, r2: float, n2: int) -> tuple[float, float]:
    """Two-sided test of r1 = r2 on Fisher z, treating the panels as
    independent samples."""
    z = (math.atanh(r1) - math.atanh(r2)) / math.sqrt(1 / (n1 - 3) + 1 / (n2 - 3))
    return z, math.erfc(abs(z) / math.sqrt(2))


def bootstrap_r(panel: list[tuple[dict, dict]], key: str,
                reps: int = 2000, seed: int = 7) -> tuple[float, float]:
    """Player-cluster bootstrap 95% interval for one panel's correlation
    (every transition of a resampled player travels with him)."""
    by_player: dict[int, list[tuple[dict, dict]]] = defaultdict(list)
    for a, b in panel:
        by_player[a["player_id"]].append((a, b))
    ids = list(by_player)
    rng = random.Random(seed)
    rs: list[float] = []
    for _ in range(reps):
        sample = [t for player_id in rng.choices(ids, k=len(ids))
                  for t in by_player[player_id]]
        r = corr(sample, key)
        if not math.isnan(r):
            rs.append(r)
    rs.sort()
    return rs[int(0.025 * (len(rs) - 1))], rs[int(0.975 * (len(rs) - 1))]


def bootstrap_gap(stayers: list[tuple[dict, dict]], movers: list[tuple[dict, dict]],
                  key: str, reps: int = 2000, seed: int = 7) -> tuple[float, float, float]:
    """Player-cluster bootstrap of r(stayers) − r(movers): players are
    resampled with replacement and every transition of a resampled player
    travels with him, group and all, so a player's two transitions (and
    their shared middle season) are never split. Returns the 95% interval
    and the share of resamples with a gap at or below zero."""
    by_player: dict[int, list[tuple[str, dict, dict]]] = defaultdict(list)
    for group, panel in (("stayer", stayers), ("mover", movers)):
        for a, b in panel:
            by_player[a["player_id"]].append((group, a, b))
    ids = list(by_player)
    rng = random.Random(seed)
    gaps: list[float] = []
    for _ in range(reps):
        s_panel, m_panel = [], []
        for player_id in rng.choices(ids, k=len(ids)):
            for group, a, b in by_player[player_id]:
                (s_panel if group == "stayer" else m_panel).append((a, b))
        if len(s_panel) < 4 or len(m_panel) < 4:
            continue
        gap = corr(s_panel, key) - corr(m_panel, key)
        if not math.isnan(gap):
            gaps.append(gap)
    gaps.sort()
    lo = gaps[int(0.025 * (len(gaps) - 1))]
    hi = gaps[int(0.975 * (len(gaps) - 1))]
    return lo, hi, sum(g <= 0 for g in gaps) / len(gaps)


def split_half_reliability(season: str, min_fga: int) -> dict[str, float]:
    """Odd/even game-ID split within a season: each qualified player's
    trips per 100 FGA in each half (FGA from his own games in that half),
    correlated across players and Spearman-Brown corrected to full-season
    length — the within-season ceiling on year-over-year persistence."""
    players = player_seasons(season)
    qualified = {p for p, r in players.items() if r["fga"] >= min_fga}
    half_fga: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    for row in player_games(season):
        if row["player_id"] in qualified:
            half_fga[row["player_id"]][int(row["game_id"]) % 2] += row["fga"]
    halves: dict[str, dict[int, list[int]]] = {
        c: defaultdict(lambda: [0, 0]) for c in TRIP_CLASSES
    }
    totals: dict[int, list[int]] = defaultdict(lambda: [0, 0])
    with (DERIVED / season / "trips.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            player_id = int(row["player_id"])
            if player_id not in qualified:
                continue
            half = int(row["game_id"]) % 2
            halves[row["trip_class"]][player_id][half] += 1
            totals[player_id][half] += 1

    result: dict[str, float] = {}
    for label, counts in [("tripsPer100Fga", totals)] + [
        (f"{c}Per100Fga", halves[c]) for c in TRIP_CLASSES
    ]:
        xs, ys = [], []
        for player_id in qualified:
            fga_a, fga_b = half_fga[player_id]
            if fga_a == 0 or fga_b == 0:
                continue
            a, b = counts.get(player_id, [0, 0])
            xs.append(100 * a / fga_a)
            ys.append(100 * b / fga_b)
        r = pearson(xs, ys)
        result[label] = 2 * r / (1 + r)
    return result


# ---- statistics ---------------------------------------------------------

def pearson(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    return sxy / math.sqrt(sxx * syy) if sxx > 0 and syy > 0 else float("nan")


def spearman(xs: list[float], ys: list[float]) -> float:
    def ranks(values: list[float]) -> list[float]:
        order = sorted(range(len(values)), key=lambda i: values[i])
        result = [0.0] * len(values)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
                j += 1
            rank = (i + j) / 2 + 1
            for k in range(i, j + 1):
                result[order[k]] = rank
            i = j + 1
        return result
    return pearson(ranks(xs), ranks(ys))


def quantiles(values: list[float], points=(0.1, 0.25, 0.5, 0.75, 0.9)) -> list[float]:
    ordered = sorted(values)
    result = []
    for p in points:
        idx = p * (len(ordered) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(ordered) - 1)
        result.append(ordered[lo] + (idx - lo) * (ordered[hi] - ordered[lo]))
    return result
