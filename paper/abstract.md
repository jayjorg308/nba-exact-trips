# The Trip Economy: Which Ways of Getting to the Line Are Skills?

## Introduction

A trip to the free-throw line is the most valuable scoring attempt in
basketball. At league conversion, a two-shot trip yields 1.57 expected
points, more than a shot from any zone on the floor. Yet foul drawing is
measured coarsely. Free-throw rate treats all trips alike, and possession
arithmetic approximates trip counts with the 0.44 coefficient. Recent work
priced shot-pursuant free throws into shot value, but the off-ball line
economy and the skill question remain unmeasured. We ask how players
actually get to the line, what each channel of foul generation is worth,
and which channels are repeatable player skills rather than circumstance.

## Methods

We reconstruct every NBA free-throw trip, meaning the free throws awarded
from a single non-technical foul, from official play-by-play across the
three most recent seasons (2023-24 through 2025-26, 3,690 games). A
versioned grammar groups free-throw events into trips and classifies each
by its causing foul into eight classes in two tiers. Attempt-equivalent
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
attempt for 279 of 284 (median premium +0.51 points per attempt). Channels persist differentially year over year (422 pooled
player-transitions, ordering identical in both transitions): two-shot
shooting fouls r = .87, three-shot fouls .76, and-ones .75, bonus .58,
residual classes .31, against split-half reliabilities of .81 to .95
(Figure 1). The bonus gap is context, not noise. For players who changed
teams, bonus persistence falls from .635 to .420 (Fisher z = 2.75,
p = .006), while every other channel's stayer-mover gap is at most .04
(p > .2). The true attempt-equivalent coefficient spans .277 to .481
against the conventional 0.44, shifts True Shooting by up to 1.5
percentage points, and itself persists at r = .53 (Table 1).

## Conclusion

Foul drawing decomposes into portable player skills, drawing shooting
fouls and finishing and-ones, and a channel that partly belongs to the
team, the off-ball bonus trip. The split is directly actionable.
Shooting-foul generation projects across team changes, bonus volume
deserves a discount in trades and free agency, and exact trip accounting
removes a persistent, player-shaped error from efficiency metrics. The
oracle-verified dataset is released for reuse.
