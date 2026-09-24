# Robustness: the persistence gradient (pooled transitions, 2023-24 … 2025-26)

## 1. Panel-threshold sensitivity (per 100 FGA)

| channel | FGA≥200 | FGA≥300 | FGA≥400 |
|---|--:|--:|--:|
| _pooled transitions_ | 516 | 422 | 336 |
| SF2 | 0.848 | 0.868 | 0.881 |
| SF3 | 0.722 | 0.755 | 0.786 |
| bonus | 0.581 | 0.580 | 0.635 |
| and-one | 0.716 | 0.750 | 0.781 |
| all trips | 0.850 | 0.861 | 0.875 |

## 2. Exposure basis (pooled, FGA≥300)

| channel | per 100 FGA | per 36 min |
|---|--:|--:|
| SF2 | 0.868 | 0.878 |
| SF3 | 0.755 | 0.743 |
| bonus | 0.580 | 0.689 |
| and-one | 0.750 | 0.802 |
| all trips | 0.861 | 0.874 |

## 3. The context test — stayers vs team-changers (pooled, FGA≥300)

Stayer transitions: 284 · mover transitions: 54 · mixed (midseason change, excluded): 84

| channel | stayers r | movers r | gap | Fisher z | p (two-sided) | bootstrap 95% CI |
|---|--:|--:|--:|--:|--:|--:|
| SF2 | 0.875 | 0.768 | +0.108 | 2.24 | 0.025 | [+0.008, +0.231] |
| SF3 | 0.775 | 0.623 | +0.151 | 1.98 | 0.048 | [-0.053, +0.341] |
| bonus | 0.623 | 0.401 | +0.221 | 2.00 | 0.046 | [-0.047, +0.583] |
| and-one | 0.764 | 0.708 | +0.056 | 0.81 | 0.420 | [-0.133, +0.252] |
| all trips | 0.870 | 0.743 | +0.127 | 2.46 | 0.014 | [+0.020, +0.256] |

Mixed folded into movers:

| channel | stayers r | movers+mixed r | gap | p (two-sided) |
|---|--:|--:|--:|--:|
| SF2 | 0.875 | 0.855 | +0.021 | 0.430 |
| SF3 | 0.775 | 0.728 | +0.047 | 0.301 |
| bonus | 0.623 | 0.485 | +0.137 | 0.057 |
| and-one | 0.764 | 0.716 | +0.047 | 0.315 |
| all trips | 0.870 | 0.843 | +0.026 | 0.345 |

## 4. The context test at each FGA bar (mixed excluded)

| FGA bar | stayers / movers | SF2 gap (p) | bonus gap (p) | bonus bootstrap 95% CI |
|---|--:|--:|--:|--:|
| ≥200 | 337 / 68 | +0.087 (0.052) | +0.254 (0.013) | [+0.007, +0.536] |
| ≥300 | 284 / 54 | +0.108 (0.025) | +0.221 (0.046) | [-0.047, +0.583] |
| ≥400 | 239 / 40 | +0.070 (0.162) | +0.207 (0.089) | [-0.098, +0.644] |