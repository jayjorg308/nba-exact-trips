# The trip economy, 2023-24 (league-wide, exact)

537 players with any free-throw activity; 261 qualified at ≥300 FGA. All rates per 100 FGA unless noted.

## Channel generation rates — distribution across qualified players

| rate | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| SF2 trips | 0.27 | 3.30 | 4.93 | 7.30 | 10.29 | 12.88 | 20.20 |
| SF3 trips | 0.00 | 0.00 | 0.00 | 0.15 | 0.42 | 0.76 | 3.89 |
| bonus trips | 0.00 | 0.64 | 0.97 | 1.58 | 2.30 | 3.41 | 7.98 |
| and-one trips | 0.00 | 1.02 | 1.57 | 2.36 | 3.48 | 4.41 | 7.95 |
| other add-on | 0.00 | 0.00 | 0.00 | 0.16 | 0.29 | 0.40 | 1.59 |
| all trips | 1.10 | 5.91 | 8.80 | 12.06 | 16.40 | 19.92 | 35.18 |

## Channel mix — share of trips

| share | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| SF2 | 0.14 | 0.47 | 0.55 | 0.61 | 0.67 | 0.72 | 0.85 |
| SF3 | 0.00 | 0.00 | 0.00 | 0.01 | 0.04 | 0.08 | 0.24 |
| bonus | 0.00 | 0.06 | 0.09 | 0.14 | 0.19 | 0.26 | 0.56 |
| and-one | 0.00 | 0.13 | 0.16 | 0.20 | 0.24 | 0.28 | 0.38 |

## The 0.44 coefficient's error structure

| quantity | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| true coefficient | 0.311 | 0.385 | 0.403 | 0.420 | 0.437 | 0.448 | 0.486 |
| ΔTS (pp) | -0.56 | -0.12 | 0.03 | 0.22 | 0.44 | 0.64 | 1.39 |

Correlates of the true coefficient (Pearson): and-one share -0.42 · technical FTA share -0.66 · SF3 share -0.51 · FTA rate 0.18

Largest TS understatements (conventional below exact):
- Jalen Brunson (NYK): 1.39 · trueCoef=0.35
- James Harden (LAC): 1.37 · trueCoef=0.38
- Tyrese Haliburton (IND): 1.34 · trueCoef=0.33
- Isaiah Hartenstein (NYK): 1.27 · trueCoef=0.39
- Luke Kennard (MEM): 1.13 · trueCoef=0.31
- Kentavious Caldwell-Pope (DEN): 0.93 · trueCoef=0.35
- Trayce Jackson-Davis (GSW): 0.91 · trueCoef=0.40
- Devin Booker (PHX): 0.91 · trueCoef=0.39

Largest TS overstatements:
- Ivica Zubac (LAC): -0.56 · trueCoef=0.47
- Andre Drummond (CHI): -0.40 · trueCoef=0.46
- Kevin Love (MIA): -0.36 · trueCoef=0.46
- Jose Alvarado (NOP): -0.31 · trueCoef=0.48
- Alex Caruso (CHI): -0.29 · trueCoef=0.47
- Kyle Anderson (MIN): -0.28 · trueCoef=0.46
- Patrick Williams (CHI): -0.28 · trueCoef=0.47
- Bam Adebayo (MIA): -0.28 · trueCoef=0.45

## The line premium (two-shot trip EV at own conversion vs own field PPS)

| quantity | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| premium (pts/attempt) | -0.282 | 0.217 | 0.351 | 0.501 | 0.613 | 0.685 | 0.824 |

Players whose two-shot trip is worth LESS than their average field attempt: 6 of 261: Rudy Gobert (-0.05), Nic Claxton (-0.16), Daniel Gafford (-0.10), Trayce Jackson-Davis (-0.28), Jakob Poeltl (-0.21), Walker Kessler (-0.12)

## Channel extremes (qualified players)

Highest SF3 generation (fouled on threes, per 100 FGA):
- James Harden (LAC): 3.89
- Julian Champagnie (SAS): 2.24
- Damian Lillard (MIL): 1.88
- Keyonte George (UTA): 1.35
- Jordan Hawkins (NOP): 1.32
- Luke Kennard (MEM): 1.27
- Spencer Dinwiddie (LAL): 1.25
- Isaiah Joe (OKC): 1.24

Highest bonus generation (off-ball, per 100 FGA):
- Rudy Gobert (MIN): 7.98
- Trae Young (ATL): 7.14
- Kevin Love (MIA): 5.29
- Shai Gilgeous-Alexander (OKC): 4.91
- Giannis Antetokounmpo (MIL): 4.75
- Kelly Olynyk (TOR): 4.63
- Nikola Jokić (DEN): 4.46
- Damian Lillard (MIL): 4.46

Highest and-one generation (per 100 FGA):
- Isaiah Hartenstein (NYK): 7.95
- Giannis Antetokounmpo (MIL): 7.67
- Zion Williamson (NOP): 7.22
- Rudy Gobert (MIN): 6.84
- Trayce Jackson-Davis (GSW): 6.63
- Moritz Wagner (ORL): 6.52
- Amen Thompson (HOU): 6.05
- James Wiseman (DET): 5.90