# The trip economy, 2024-25 (league-wide, exact)

547 players with any free-throw activity; 277 qualified at ≥300 FGA. All rates per 100 FGA unless noted.

## Channel generation rates — distribution across qualified players

| rate | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| SF2 trips | 0.24 | 2.99 | 4.99 | 7.76 | 10.17 | 13.04 | 23.12 |
| SF3 trips | 0.00 | 0.00 | 0.00 | 0.17 | 0.49 | 0.96 | 3.78 |
| bonus trips | 0.00 | 0.68 | 1.05 | 1.62 | 2.25 | 3.06 | 6.32 |
| and-one trips | 0.00 | 0.80 | 1.55 | 2.35 | 3.38 | 4.16 | 6.97 |
| other add-on | 0.00 | 0.00 | 0.00 | 0.15 | 0.31 | 0.47 | 1.01 |
| all trips | 1.27 | 5.82 | 8.65 | 12.25 | 16.11 | 19.54 | 35.01 |

## Channel mix — share of trips

| share | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| SF2 | 0.08 | 0.47 | 0.55 | 0.62 | 0.68 | 0.72 | 0.86 |
| SF3 | 0.00 | 0.00 | 0.00 | 0.01 | 0.05 | 0.09 | 0.33 |
| bonus | 0.00 | 0.07 | 0.10 | 0.14 | 0.19 | 0.25 | 0.50 |
| and-one | 0.00 | 0.12 | 0.16 | 0.19 | 0.23 | 0.26 | 0.42 |

## The 0.44 coefficient's error structure

| quantity | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| true coefficient | 0.284 | 0.387 | 0.407 | 0.426 | 0.442 | 0.453 | 0.478 |
| ΔTS (pp) | -0.68 | -0.16 | -0.02 | 0.15 | 0.34 | 0.59 | 1.49 |

Correlates of the true coefficient (Pearson): and-one share -0.40 · technical FTA share -0.73 · SF3 share -0.55 · FTA rate 0.25

Largest TS understatements (conventional below exact):
- Kentavious Caldwell-Pope (MEM): 1.49 · trueCoef=0.28
- Chris Paul (SAS): 1.18 · trueCoef=0.30
- Luke Kennard (MEM): 1.14 · trueCoef=0.30
- Brandon Clarke (MEM): 0.97 · trueCoef=0.37
- Julian Champagnie (SAS): 0.94 · trueCoef=0.32
- James Harden (LAC): 0.93 · trueCoef=0.40
- Zach Edey (MEM): 0.89 · trueCoef=0.39
- Tyrese Haliburton (IND): 0.89 · trueCoef=0.37

Largest TS overstatements:
- Jonathan Kuminga (GSW): -0.68 · trueCoef=0.48
- Jake LaRavia (SAC): -0.51 · trueCoef=0.47
- Rudy Gobert (MIN): -0.42 · trueCoef=0.45
- Joel Embiid (PHI): -0.39 · trueCoef=0.46
- Brandon Boston Jr. (NOP): -0.33 · trueCoef=0.47
- Cody Martin (PHX): -0.31 · trueCoef=0.48
- Scoot Henderson (POR): -0.30 · trueCoef=0.46
- De'Andre Hunter (CLE): -0.30 · trueCoef=0.46

## The line premium (two-shot trip EV at own conversion vs own field PPS)

| quantity | min | p10 | p25 | median | p75 | p90 | max |
|---|--:|--:|--:|--:|--:|--:|--:|
| premium (pts/attempt) | -0.302 | 0.208 | 0.359 | 0.505 | 0.631 | 0.721 | 0.905 |

Players whose two-shot trip is worth LESS than their average field attempt: 6 of 277: Jalen Duren (-0.05), Daniel Gafford (-0.03), Nic Claxton (-0.11), Walker Kessler (-0.30), Clint Capela (-0.05), Ryan Dunn (-0.06)

## Channel extremes (qualified players)

Highest SF3 generation (fouled on threes, per 100 FGA):
- James Harden (LAC): 3.78
- Damian Lillard (MIL): 3.12
- Jordan Clarkson (UTA): 1.83
- Mike Conley (MIN): 1.71
- Kevin Porter Jr. (MIL): 1.69
- Tim Hardaway Jr. (DET): 1.62
- Donovan Mitchell (CLE): 1.52
- Spencer Dinwiddie (DAL): 1.47

Highest bonus generation (off-ball, per 100 FGA):
- Trae Young (ATL): 6.32
- De'Andre Hunter (CLE): 5.38
- Jonathan Isaac (ORL): 5.25
- Nikola Jokić (DEN): 5.06
- Jimmy Butler III (GSW): 5.03
- Draymond Green (GSW): 4.72
- Jalen Brunson (NYK): 4.42
- Dennis Schröder (DET): 4.23

Highest and-one generation (per 100 FGA):
- Giannis Antetokounmpo (MIL): 6.97
- Zion Williamson (NOP): 6.89
- Walker Kessler (UTA): 6.68
- Daniel Gafford (DAL): 6.45
- Jimmy Butler III (GSW): 6.20
- Brandon Clarke (MEM): 6.05
- Deni Avdija (POR): 6.04
- Mark Williams (CHA): 5.59