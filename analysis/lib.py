"""Shared analysis loaders: the derived trip dataset joined to the league
totals artifact (the denominators: FGA, FTA, FTM, PTS, GP, MIN)."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ANALYSIS = Path(__file__).resolve().parent
RESEARCH = ANALYSIS.parent

TRIP_CLASSES = (
    "shootingFoul2", "shootingFoul3", "bonus", "andOne",
    "flagrant", "awayFromPlay", "transitionTake", "clearPath",
)
ATTEMPT_EQUIVALENT = {"shootingFoul2", "shootingFoul3", "bonus"}
OTHER_ADDON = ("flagrant", "awayFromPlay", "transitionTake", "clearPath")


def latest_totals(season: str) -> dict[int, dict]:
    totals_dir = RESEARCH / "data" / "raw" / "_league" / season / "totals"
    path = sorted(totals_dir.glob("*.json"))[-1]
    artifact = json.loads(path.read_text(encoding="utf-8"))
    result = artifact["response"]["resultSets"][0]
    headers = result["headers"]
    col = {name: headers.index(name) for name in (
        "PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION", "GP", "MIN",
        "FGM", "FGA", "FTM", "FTA", "PTS",
    )}
    lines: dict[int, dict] = {}
    for row in result["rowSet"]:
        lines[int(row[col["PLAYER_ID"]])] = {
            "name": str(row[col["PLAYER_NAME"]]),
            "team": str(row[col["TEAM_ABBREVIATION"]]),
            "gp": int(row[col["GP"]]),
            "min": float(row[col["MIN"]]),
            "fgm": int(row[col["FGM"]]),
            "fga": int(row[col["FGA"]]),
            "ftm": int(row[col["FTM"]]),
            "fta": int(row[col["FTA"]]),
            "pts": int(row[col["PTS"]]),
        }
    return lines


def player_seasons(season: str) -> dict[int, dict]:
    """players.csv joined to the totals artifact, plus derived metrics."""
    totals = latest_totals(season)
    path = RESEARCH / "data" / "derived" / season / "players.csv"
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
                "name": line["name"],
                "team": line["team"],
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
