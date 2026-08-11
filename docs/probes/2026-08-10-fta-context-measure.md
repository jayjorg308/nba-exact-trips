# Probe: does any public NBA endpoint serve fouled-miss shot locations?

Ran 2026-08-10, from a local machine (stats.nba.com blocks cloud IPs).
Motivation: Sanders & Ehrlich's true shot charts (SSAC 2024) incorporate
missed shots that drew shooting fouls WITH court locations for 2016-2022,
and the nba-analytics product repo had recorded (2026-07-21) that the
shotchartdetail FTA/POSS_END_FT context measures are rejected by the
current stats API. This probe established whether the rejection is
era-dependent and whether any adjacent endpoint still serves the data.

## Findings

1. **`shotchartdetail` rejects `ContextMeasure=FTA` and `POSS_END_FT` at
   the parameter level, for every era probed.** The server returns the
   validation body `{"ContextMeasure":["Invalid parameters"]}` identically
   for 2017-18 (Harden, peak foul-drawing, inside the Sanders & Ehrlich
   window), 2021-22 (Giannis), and 2025-26 (Gilgeous-Alexander). The block
   is on the parameter itself, not the data era.
2. **`TS_PCT` and `EFG_PCT` context measures are accepted but change
   nothing**: both return the identical row universe as `FGA` (1,449 rows
   for Harden 2017-18) — the measure changes league-average framing, not
   the event set. No fouled misses appear. `PF` returns an empty body.
3. **`shotchartlineupdetail` accepts `ContextMeasure=FTA` but serves no
   locations.** With a real lineup GROUP_ID (HOU 2017-18
   Ariza-Paul-Tucker-Harden-Capela; 465 FGA rows as baseline), FTA
   returned 134 rows — every one a free-throw EVENT
   (`EVENT_TYPE='Free Throw'`) with `SHOT_ZONE_*`, `SHOT_DISTANCE`,
   `LOC_X`, `LOC_Y` all null. A free-throw event list, which play-by-play
   already provides better; not fouled-attempt locations.

## Conclusion

**No public NBA endpoint serves the location of a fouled missed shot, for
any era.** A shooting foul on a miss produces no shot event in
play-by-play either (the free-throw count — 2 vs 3 — is the only surviving
record of the denied attempt's point class). Fouled-miss location work
requires commercial data: Sanders & Ehrlich's repository names BigDataBall
as their source (see `docs/prior-art/sanders-ehrlich-true-shot-charts.md`).
This is why the trip dataset's spatial claims are bounded at the arc split
(2 FT vs 3 FT, exact) plus and-one locations (exact, via the linked made
shot, bias stated), and why this project's reproducibility from free
public endpoints is a real differentiator.
