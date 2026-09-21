# The Trip Economy: Which Foul-Drawing Skills Travel?

## Introduction

A trip to the free-throw line is the most valuable scoring attempt in
basketball. At league conversion, a two-shot trip yields 1.57 expected
points, more than a shot from any zone on the floor. Yet foul drawing is
measured coarsely. Free-throw rate treats all trips alike, and possession
arithmetic approximates trip counts with the 0.44 coefficient. Recent work
folded the free throws earned on fouled shots into shot value; the rest
of the trip economy, and the skill behind it, remain unmeasured. We ask how players
actually get to the line, what each channel of foul generation is worth,
and which channels are repeatable player skills rather than circumstance.

## Methods

We reconstruct every NBA free-throw trip, meaning the free throws awarded
from a single non-technical foul, from official play-by-play across the
three most recent seasons (2023-24 through 2025-26, 3,690 games). We trace each
trip to the foul that caused it and classify the trips into eight classes
in two tiers. Attempt-equivalent
trips end the possession in place of a field-goal attempt (two- and
three-shot shooting fouls, bonus). Add-on trips stack points on a
possession that already stands (and-ones and rarer classes). Reconstruction
is exact rather than estimated. Every player-game reconciles with the
official box score and every player-season with an independent league
source, yielding 88,347 trips across 1,723 player-seasons with zero
discrepancies. The dataset and pipeline are public.

## Results

The trip economy varies structurally across players. Among 284 players
with 300 or more field-goal attempts in 2025-26, two-shot shooting-foul
generation spans 3.1 to 14.0 trips per 100 attempts (10th to 90th
percentile). Within that group, James Harden leads in three-shot fouls
drawn (3.8 per 100), Nikola Jokić in off-ball bonus trips (7.0). A
two-shot trip at a player's own conversion out-values his average field
attempt for 279 of the 284 players; the median player gains +0.51 points
per attempt. Channels persist differently year over year (422
player-season transitions across two season pairs, same ordering in
both): two-shot shooting
fouls r = .87, three-shot fouls .76, and-ones .75, bonus .58, residual
classes .31. Within-season (split-half) reliabilities of .81 to .95 show
the gradient is not measurement noise (Figure 1). The bonus gap is
context: for players who changed teams, bonus persistence falls from
.635 to .420 (p = .006), while every other channel travels intact (gaps
at most .04, p > .2). The conventional 0.44 coefficient mismeasures the
same players every year: its true value spans .277 to .481, persists at
r = .53, and moves True Shooting by up to 1.5 percentage points
(Table 1).

## Conclusion

Drawing shooting fouls and finishing and-ones are player skills that
travel. The off-ball bonus trip partly belongs to the team. The split is
directly actionable.
Shooting-foul generation projects across team changes, bonus volume
deserves a discount in trades and free agency, and exact trip accounting
removes a persistent, player-shaped error from efficiency metrics.
