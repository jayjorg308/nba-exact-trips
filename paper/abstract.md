# The Trip Economy: Which Foul-Drawing Skills Travel?

## Introduction

A trip to the free-throw line is the most valuable scoring attempt in
basketball. At league conversion, a two-shot trip yields 1.57 expected
points, more than a shot from any zone on the floor. Yet foul drawing is
measured coarsely. Free-throw rate treats all trips alike, and possession
arithmetic approximates trip counts with the 0.44 coefficient. Recent work
folded the free throws earned on fouled shots into shot value; the rest
of the trip economy is countable with existing tools but unstudied as a
skill. We ask how players actually get to the line and which channels are
repeatable player skills rather than circumstance.

## Methods

We reconstruct every regular-season NBA free-throw trip, meaning the free
throws awarded from a single non-technical foul, from official
play-by-play across the three most recent seasons (2023-24 through
2025-26, 3,690 games). We trace each trip to the foul that caused it and
classify the trips into eight classes in two tiers. Attempt-equivalent
trips replace a field-goal attempt as the possession's scoring attempt
(two- and three-shot shooting fouls, bonus). Add-on trips stack points on
a possession that already stands (and-ones and rarer classes).
Reconstruction is exact rather than estimated. Every player-game
reconciles with the official box score and every one of 1,723 league
player-seasons with an independent season-totals source, yielding 88,347
trips with zero discrepancies. The dataset and pipeline are public.

## Results

The trip economy varies structurally across the 284 players with 300 or
more field-goal attempts in 2025-26 (Table 1); James Harden leads in
three-shot fouls drawn (3.8 per 100). Channels persist differently year
over year (422 player-season transitions; the pattern holds in both
season pairs): two-shot shooting fouls r = .87, three-shot fouls .76,
and-ones .75, bonus .58, residual classes .31. Two-shot fouls persist
near their split-half reliability ceiling (.89 to .92); bonus trips fall
short of a lower one (.65 to .78), noisier to measure and less stable
(Figure 1). Changing teams lowers persistence in every channel: for 54
players who moved between seasons without a midseason change, all-trip
persistence is .74 against .87 for 284 stayers (p = .014), with the
largest drop in bonus (.62 to .40, p = .046). With 54 movers the bonus
gap's bootstrap interval spans zero, so channel-specificity is
suggestive, not established. The conventional 0.44 coefficient
mismeasures the same players every year: its true value spans .277 to
.481, persists at r = .53, and moves True Shooting by a median 0.15 and
up to 1.5 percentage points (Table 1).

## Conclusion

Drawing shooting fouls is the most repeatable route to the line; the
non-shooting bonus channel is the least stable and the least portable
across a team change. The split is actionable with care: shooting-foul
generation projects across team changes, bonus volume should be projected
with destination-team context and wider uncertainty, and exact trip
accounting removes a persistent, player-shaped error from efficiency
metrics.
