"""Pilot: the trip economy across every player with an exact free-throw
payload (nine nba-analytics heroes + pilot derives), one season (2025-26).

The kill-test question: do players' free-throw economies differ by CHANNEL
(how trips arise) in ways the season line hides — and how far off is the
0.44 estimator player by player?

Reads committed/derived payloads only; computes everything from trip rows.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
NBA_ANALYTICS = RESEARCH.parent / "nba-analytics"

ATTEMPT_EQUIVALENT = {"shootingFoul2", "shootingFoul3", "bonus"}
CLASSES = [
    "shootingFoul2", "shootingFoul3", "bonus", "andOne",
    "flagrant", "awayFromPlay", "transitionTake", "clearPath",
]


def payload_paths() -> list[Path]:
    paths = sorted(NBA_ANALYTICS.glob("public/data/*/2025-26.freethrow.json"))
    paths += sorted(RESEARCH.glob("data/derived/*/2025-26.freethrow.json"))
    return paths


def analyze(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = payload["_meta"]
    trips = payload["trips"]
    league = payload["leagueBaseline"]

    by_class = {c: [t for t in trips if t["tripClass"] == c] for c in CLASSES}
    n = {c: len(v) for c, v in by_class.items()}
    ftm_by_class = {c: sum(t["ftm"] for t in v) for c, v in by_class.items()}
    fta_by_class = {c: sum(t["fta"] for t in v) for c, v in by_class.items()}

    ae_trips = sum(n[c] for c in ATTEMPT_EQUIVALENT)
    fta = meta["seasonFta"]
    ftm = meta["seasonFtm"]
    fga = meta["seasonFga"]
    pts = meta["seasonPoints"]

    ts_conv = pts / (2 * (fga + 0.44 * fta)) if fga else None
    ts_exact = pts / (2 * (fga + ae_trips)) if fga else None

    conv = ftm / fta if fta else None
    field_pps = (pts - ftm) / fga if fga else None

    return {
        "player": meta["player"],
        "games": meta["gamesIncluded"],
        "fga": fga,
        "fta": fta,
        "ftm": ftm,
        "pts": pts,
        "technicalFta": meta["technicalFta"],
        "technicalFtm": meta["technicalFtm"],
        "trips": len(trips),
        "n": n,
        "ftmByClass": ftm_by_class,
        "ftaByClass": fta_by_class,
        "aeTrips": ae_trips,
        "trueCoef": ae_trips / fta if fta else None,
        "tsConv": ts_conv,
        "tsExact": ts_exact,
        "tsDeltaPp": (ts_exact - ts_conv) * 100 if ts_conv else None,
        "conversion": conv,
        "fieldPps": field_pps,
        "twoShotEv": 2 * conv if conv else None,
        "ftaRate": fta / fga if fga else None,
        "ftPtsShare": ftm / pts if pts else None,
        "leagueConv": league["ftm"] / league["fta"],
        "leagueFtaRate": league["fta"] / league["fga"],
        "leagueFtPtsShare": league["ftm"] / league["points"],
    }


def fmt(x, digits=3):
    return "—" if x is None else f"{x:.{digits}f}"


def main() -> None:
    rows = [analyze(p) for p in payload_paths()]
    rows.sort(key=lambda r: -(r["ftaRate"] or 0))

    lines: list[str] = []
    out = lines.append

    out("# Pilot: the trip economy, 2025-26 (11 players, exact reconstruction)")
    out("")
    lg = rows[0]
    out(f"League line: conversion {fmt(lg['leagueConv'])} · FTA rate "
        f"{fmt(lg['leagueFtaRate'])} · FT points share {fmt(lg['leagueFtPtsShare'])}")
    out("")

    out("## Season lines and the 0.44 error")
    out("")
    out("| player | games | FTA | FTA rate | conv | FT pts share | trips | AE trips | true coef | 0.44 err | TS conv | TS exact | ΔTS (pp) |")
    out("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for r in rows:
        coef_err = (r["trueCoef"] - 0.44) if r["trueCoef"] is not None else None
        out(
            f"| {r['player']} | {r['games']} | {r['fta']} | {fmt(r['ftaRate'])} "
            f"| {fmt(r['conversion'])} | {fmt(r['ftPtsShare'])} | {r['trips']} "
            f"| {r['aeTrips']} | {fmt(r['trueCoef'])} | {fmt(coef_err, 3)} "
            f"| {fmt(r['tsConv'], 4)} | {fmt(r['tsExact'], 4)} | {fmt(r['tsDeltaPp'], 2)} |"
        )
    out("")

    out("## Channel mix — share of trips by class")
    out("")
    out("| player | SF2 | SF3 | bonus | and-1 | AFP | trans | flag | CP | tech FTA |")
    out("|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|")
    for r in rows:
        t = r["trips"] or 1
        out(
            f"| {r['player']} "
            f"| {r['n']['shootingFoul2'] / t:.0%} "
            f"| {r['n']['shootingFoul3'] / t:.0%} "
            f"| {r['n']['bonus'] / t:.0%} "
            f"| {r['n']['andOne'] / t:.0%} "
            f"| {r['n']['awayFromPlay'] / t:.0%} "
            f"| {r['n']['transitionTake'] / t:.0%} "
            f"| {r['n']['flagrant'] / t:.0%} "
            f"| {r['n']['clearPath'] / t:.0%} "
            f"| {r['technicalFta']} |"
        )
    out("")

    out("## Channel economics — FT points by class and the line premium")
    out("")
    out("| player | FT pts | from SF2 | from SF3 | from bonus | from and-1 | field PPS | 2-shot trip EV | premium |")
    out("|---|--:|--:|--:|--:|--:|--:|--:|--:|")
    for r in rows:
        ftm = r["ftm"] or 1
        premium = (r["twoShotEv"] - r["fieldPps"]) if r["twoShotEv"] and r["fieldPps"] else None
        out(
            f"| {r['player']} | {r['ftm']} "
            f"| {r['ftmByClass']['shootingFoul2'] / ftm:.0%} "
            f"| {r['ftmByClass']['shootingFoul3'] / ftm:.0%} "
            f"| {r['ftmByClass']['bonus'] / ftm:.0%} "
            f"| {r['ftmByClass']['andOne'] / ftm:.0%} "
            f"| {fmt(r['fieldPps'], 3)} | {fmt(r['twoShotEv'], 3)} "
            f"| {fmt(premium, 3)} |"
        )
    out("")

    report = "\n".join(lines)
    out_path = HERE / "output" / "pilot-trip-economy.md"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nreport -> {out_path}")


if __name__ == "__main__":
    main()
