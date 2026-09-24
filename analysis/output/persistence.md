# Channel persistence across three seasons (2023-24 … 2025-26)

Panels (≥300 FGA and ≥1 trip both seasons): 2023-24→2024-25: 215 · 2024-25→2025-26: 207 · pooled player-transitions: 422 · two-year lag (2023-24→2025-26): 184

## Year-over-year persistence, per transition and pooled

Split-half: odd/even-game rates per 100 FGA within a season, Spearman-Brown corrected — the within-season ceiling.

| metric | 2023-24→2024-25 | 2024-25→2025-26 | pooled r | pooled ρ | split-half (3-season range) |
|---|--:|--:|--:|--:|--:|
| FTA rate (benchmark) | 0.858 | 0.854 | 0.851 | 0.822 | — |
| FT conversion (benchmark) | 0.769 | 0.745 | 0.757 | 0.730 | — |
| all trips /100 FGA | 0.867 | 0.863 | 0.861 | 0.840 | 0.92–0.95 |
| SF2 /100 FGA | 0.881 | 0.856 | 0.868 | 0.840 | 0.89–0.92 |
| SF3 /100 FGA | 0.772 | 0.741 | 0.755 | 0.704 | 0.74–0.83 |
| bonus /100 FGA | 0.580 | 0.603 | 0.580 | 0.533 | 0.65–0.78 |
| and-one /100 FGA | 0.748 | 0.772 | 0.750 | 0.734 | 0.79–0.79 |
| other add-on /100 FGA | 0.322 | 0.314 | 0.309 | 0.271 | — |
| true 0.44 coefficient | 0.550 | 0.514 | 0.528 | 0.516 | — |
| line premium | 0.756 | 0.732 | 0.744 | 0.698 | — |

## Decay: adjacent-season vs two-year-lag correlation

| channel | adjacent (pooled) | two-year lag | retention |
|---|--:|--:|--:|
| SF2 | 0.868 | 0.782 | 90% |
| SF3 | 0.755 | 0.701 | 93% |
| bonus | 0.580 | 0.536 | 92% |
| and-one | 0.750 | 0.746 | 99% |
| all trips | 0.861 | 0.802 | 93% |

## The context test — by game-level team history

Stayer: one team in both seasons, the same one. Mover: one team each season, different. Mixed: a midseason change in either season (excluded from the main comparison; folded into movers below).

Stayer transitions: 284 · mover transitions: 54 · mixed transitions: 84

### Pooled, stayers vs movers (mixed excluded)

Bootstrap: player-cluster resampling (2,000 reps) of the gap, so a player's two transitions and their shared middle season travel together.

| channel | stayers r [95% CI] | movers r [95% CI] | gap [95% CI] | P(gap ≤ 0) | Fisher p (independent samples, reference only) |
|---|--:|--:|--:|--:|--:|
| SF2 | 0.875 [0.831, 0.905] | 0.768 [0.638, 0.858] | +0.108 [+0.008, +0.231] | 0.019 | 0.025 |
| SF3 | 0.775 [0.671, 0.848] | 0.623 [0.436, 0.797] | +0.151 [-0.053, +0.341] | 0.081 | 0.048 |
| bonus | 0.623 [0.519, 0.710] | 0.401 [0.063, 0.645] | +0.221 [-0.047, +0.583] | 0.054 | 0.046 |
| and-one | 0.764 [0.685, 0.821] | 0.708 [0.511, 0.881] | +0.056 [-0.133, +0.252] | 0.367 | 0.420 |
| all trips | 0.870 [0.827, 0.899] | 0.743 [0.605, 0.847] | +0.127 [+0.020, +0.256] | 0.011 | 0.014 |

### Per transition (mixed excluded)

| transition | channel | stayers r (n) | movers r (n) | gap | Fisher p |
|---|---|--:|--:|--:|--:|
| 2023-24→2024-25 | SF2 | 0.877 (144) | 0.825 (29) | +0.052 | 0.372 |
| 2023-24→2024-25 | SF3 | 0.821 (144) | 0.495 (29) | +0.325 | 0.004 |
| 2023-24→2024-25 | bonus | 0.639 (144) | 0.271 (29) | +0.368 | 0.025 |
| 2023-24→2024-25 | and-one | 0.740 (144) | 0.744 (29) | -0.003 | 0.974 |
| 2023-24→2024-25 | all trips | 0.873 (144) | 0.773 (29) | +0.100 | 0.138 |
| 2024-25→2025-26 | SF2 | 0.878 (140) | 0.647 (25) | +0.231 | 0.009 |
| 2024-25→2025-26 | SF3 | 0.713 (140) | 0.632 (25) | +0.081 | 0.519 |
| 2024-25→2025-26 | bonus | 0.662 (140) | 0.520 (25) | +0.142 | 0.337 |
| 2024-25→2025-26 | and-one | 0.808 (140) | 0.701 (25) | +0.106 | 0.276 |
| 2024-25→2025-26 | all trips | 0.885 (140) | 0.689 (25) | +0.196 | 0.016 |

### Sensitivity: mixed transitions folded into movers

| channel | stayers r | movers+mixed r | gap | Fisher p |
|---|--:|--:|--:|--:|
| SF2 | 0.875 | 0.855 | +0.021 | 0.430 |
| SF3 | 0.775 | 0.728 | +0.047 | 0.301 |
| bonus | 0.623 | 0.485 | +0.137 | 0.057 |
| and-one | 0.764 | 0.716 | +0.047 | 0.315 |
| all trips | 0.870 | 0.843 | +0.026 | 0.345 |

### Mean change in rate, season to season (per 100 FGA)

| channel | stayers mean Δ | movers mean Δ | movers − stayers |
|---|--:|--:|--:|
| SF2 | +0.463 | +0.135 | -0.328 |
| SF3 | +0.115 | +0.097 | -0.019 |
| bonus | +0.249 | -0.093 | -0.342 |
| and-one | +0.008 | -0.034 | -0.042 |
| all trips | +0.875 | +0.124 | -0.752 |

## Channel-mix stability (share of trips, pooled)

| share | r | ρ |
|---|--:|--:|
| SF2 | 0.615 | 0.558 |
| SF3 | 0.710 | 0.738 |
| bonus | 0.519 | 0.491 |
| and-one | 0.169 | 0.225 |