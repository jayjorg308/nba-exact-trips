# The Trip Economy: Which Foul-Drawing Skills Travel?

## Introduction

In 2025-26, a two-shot trip at league conversion yielded 1.57 expected
points against 1.09 for the average field attempt. Yet foul drawing is
measured coarsely. Free-throw rate treats all trips alike, and possession
arithmetic approximates trip counts with the 0.44 coefficient. Recent work
folded the free throws earned on fouled shots into shot value, and
existing tools can count the rest of the trip economy. We ask how players
actually get to the line and which channels are repeatable player skills
rather than circumstance.

## Methods

We reconstruct every regular-season NBA free-throw trip, meaning the free
throws awarded from a single non-technical foul, from official
play-by-play across the three most recent seasons (2023-24 through
2025-26, 3,690 games). We link each trip to its recorded causing foul and
classify trips by foul type under documented rules into eight classes in
two tiers. Attempt-equivalent trips replace a field-goal attempt as the
possession's scoring attempt (two- and three-shot shooting fouls, bonus).
Add-on trips stack points on a possession that already stands (and-ones
and rarer classes). Trip counts are exact rather than estimated:
reconstructed free-throw makes and attempts reconcile with the official
box score for every player-game and with an independent season-totals
source for every one of 1,723 league player-seasons, yielding 88,347
trips with zero discrepancies. The dataset and pipeline are public.

## Results

The trip economy varies structurally across the 284 players with 300 or
more field-goal attempts in 2025-26 (Table 1); James Harden leads in
three-shot fouls drawn (3.8 per 100). Channels persist differently year
over year (422 player-season transitions; the pattern holds in both
season pairs): two-shot shooting fouls r = .87, three-shot fouls .76,
and-ones .75, bonus .58, residual classes .31. Two-shot fouls persist
near their within-season (split-half) reliability of .89 to .92; bonus
trips fall short of a lower .65 to .78, noisier to measure and less
stable (Figure 1). Across 54 mover and 284 stayer transitions (midseason
changes excluded), movers showed lower persistence in every main
channel: all trips .74 against .87 (player-cluster bootstrap 95%
interval for the gap +.02 to +.26). The bonus gap was largest (.62
against .40) but its interval spans zero (−.05 to +.58), so
channel-specific differences remain uncertain. The conventional 0.44
coefficient tends to mismeasure the same players every year: its true
value spans .277 to .481, persists at r = .53, and moves True Shooting
by a median 0.15 and up to 1.5 percentage points (Table 1).

## Conclusion

Two-shot shooting-foul generation is the most persistent of the four
main channels, for stayers and movers alike; non-shooting bonus
generation is the least. The split motivates channel-specific
projections, with portability differences across team changes still
uncertain, and exact trip accounting corrects a persistent,
player-shaped error in efficiency metrics.
