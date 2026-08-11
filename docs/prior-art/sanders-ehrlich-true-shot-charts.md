# Sanders & Ehrlich, "Estimating NBA Team Shot Selection Efficiency from Aggregations of True, Continuous Shot Charts" (SSAC 2024 finalist)

Dissected 2026-08-10 from the full paper (Sloan CDN) and the authors' open
repository (github.com/Syracuse-University-Sport-Analytics/continous_shot_selection).
This is the closest prior art to the trip-economy thesis; the notes below are
what an abstract or manuscript must position against.

Paper: https://www.sloansportsconference.com/research-papers/estimating-nba-team-shot-selection-efficiency-from-aggregations-of-true-continuous-shot-charts-a-generalized-additive-model-approach
Dashboard: https://sportdataviz.syr.edu/TrueShotChart/

## What they did

- "True points" per shot event: field points plus shot-pursuant free-throw
  points (fouled misses and and-ones), smoothed over the half-court with a
  GAM, 2016-17 through 2022-23.
- Team-season summary: Shot Selection Efficiency, the spatial Pearson
  correlation between shot volume and true points, regressed on wins
  (significant; a "moneyball" attribute not priced by payroll).
- Headline: aggregating true shot charts shows a three-point DISPREMIUM
  since 2018-19 (~-0.066 pts/shot in 2021-22) that conventional shot charts
  cannot see.
- Player treatment: two anecdote charts (Harden 2019-20, Butler 2022-23).
  No player-level measure, no skill or persistence analysis.

## Data source: commercial, not publicly reproducible

- Source is BigDataBall play-by-play (named in data_clean.ipynb). Fouled-miss
  locations come from that feed's coordinates. Our probe
  (`docs/probes/2026-08-10-fta-context-measure.md`) established no free
  public NBA endpoint serves fouled-miss locations for any era:
  shotchartdetail rejects ContextMeasure=FTA at the parameter level, and
  shotchartlineupdetail's accepted FTA returns free-throw events with null
  coordinates.
- Replicating their pipeline requires purchasing the same provider data.

## Validation posture

- No box-score or season-total reconciliation anywhere in the pipeline.
- Known source discrepancies are dropped, not resolved: the analysis
  filters rows where free-throw counts disagree, with the comment
  "#filters out the 5 mistakes by source".
- Everything downstream is GAM-smoothed estimation; no exactness claims.

## The open ground (what they never touch)

1. The off-ball line economy: bonus, away-from-play, transition-take, and
   technical free throws are entirely absent — their model sees only
   shot-pursuant fouls. Pilot measurement (11 players, 2025-26): roughly
   one-tenth to one-third of a player's FT production arrives through
   channels invisible to their framework.
2. Any trip taxonomy or attempt-equivalent / add-on tiering.
3. The 0.44 estimator and scoring-attempt denominators (they never touch
   possession arithmetic or TS%).
4. Player-level channel measurement and multi-season skill persistence.
5. Exact reconstruction with oracle reconciliation (per-game box-score
   equality, independent season totals) on freely available data.

## Positioning

Cite as the motivating prior: shot-pursuant free-throw value is spatially
material and analytically neglected (their result stands). Differentiate on
completeness (the whole trip economy, not shot-pursuant only), grain
(player-level channels and persistence, not team-season correlation),
exactness (oracle-verified, zero tolerated discrepancies vs dropped
mistakes), and reproducibility (free public endpoints plus an open derived
dataset vs a commercial feed).
