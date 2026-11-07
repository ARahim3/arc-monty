Dataset `oned`: 901 items (test pairs) in 18 tasks; 2703 demo-role items. Dev comparators: 1147 tasks, unit = task.

## Acceptance rules (real and demo roles)

| Rule | Real role | Coverage | Demo roles | Dev (1,147, by task) |
|---|---|---|---|---|
| FA-LOO + (c) | 161/172 = 93.6% [79.1, 98.3] | 19.1% | 479/515 = 93.0% [70.5, 97.5] | 101/102 = 99.0% [96.7, 100.0] |
| FA-LOO (a)+(b) | 161/172 = 93.6% [79.1, 98.3] | 19.1% | 479/522 = 91.8% [67.0, 97.1] | 101/103 = 98.1% [95.0, 100.0] |
| (a) only, full-data answer | 161/172 = 93.6% [79.1, 98.3] | 19.1% | 479/516 = 92.8% [69.6, 97.4] | 102/104 = 98.1% [94.9, 100.0] |
| v5 heuristic (2 attempts) | 167/178 = 93.8% [82.9, 98.3] | 19.8% | 493/531 = 92.8% [75.2, 97.2] | 96/98 = 98.0% [94.7, 100.0] |
| v5 heuristic, top answer only | 167/178 = 93.8% [82.9, 98.3] | 19.8% | 493/531 = 92.8% [75.2, 97.2] | 96/98 = 98.0% [94.7, 100.0] |
| P4 confident (2 attempts) | 161/172 = 93.6% [80.6, 98.2] | 19.1% | 475/509 = 93.3% [73.3, 97.6] | 97/98 = 99.0% [96.6, 100.0] |
| fit to demos only (2 attempts) | 187/285 = 65.6% [39.5, 82.1] | 31.6% | 543/801 = 67.8% [40.6, 83.2] | 111/157 = 70.7% [63.4, 77.6] |
| fit to demos only, top answer only | 187/285 = 65.6% [39.5, 82.1] | 31.6% | 543/801 = 67.8% [40.6, 83.2] | 111/157 = 70.7% [63.4, 77.6] |

pass@2, real role: 198/901 = 22.0% (count CI [79, 345]); tasks with at least one solve: 13/18. Items with any candidate: 327.
Joint P(answer and wrong), FA-LOO + (c), real role: 11/901 = 1.22%. Task-level: 12 tasks answered, 6 with a wrong answer; mean per-task precision 75.9%.

## Test 1. Frames

**behaviour alone.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 179 (11) | 148/154 = 96.1% [85.7, 100.0] | 145/151 = 96.0% [85.7, 100.0] | 148/154 = 96.1% [85.7, 100.0] | 446/461 = 96.7% [80.6, 99.0] | 29; 13/14; 13/13; 12/12 |
| abs | 179 (11) | 148/154 = 96.1% [85.7, 100.0] | 145/151 = 96.0% [85.7, 100.0] | 148/154 = 96.1% [85.7, 100.0] | 446/461 = 96.7% [80.6, 99.0] | 24; 11/12; 11/11; 9/9 |
| both | 179 (11) | 154/160 = 96.2% [88.1, 100.0] | 151/157 = 96.2% [87.9, 100.0] | 148/154 = 96.1% [85.7, 100.0] | 446/461 = 96.7% [80.6, 99.0] | 31; 13/16; 13/15; 11/11 |
| global | 11 (8) | 4/4 = 100.0% [100.0, 100.0] | 4/4 = 100.0% [100.0, 100.0] | 4/4 = 100.0% [100.0, 100.0] | 12/18 = 66.7% [42.9, 75.0] | 2; 1/2; 1/2; 1/1 |

**system.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 198 (13) | 164/175 = 93.7% [80.8, 98.3] | 161/172 = 93.6% [80.6, 98.2] | 161/172 = 93.6% [79.1, 98.3] | 479/516 = 92.8% [69.6, 97.4] | 136; 101/103; 97/98; 103/104 |
| abs | 198 (13) | 164/175 = 93.7% [80.8, 98.3] | 161/172 = 93.6% [80.6, 98.2] | 161/172 = 93.6% [79.1, 98.3] | 479/516 = 92.8% [69.6, 97.4] | 133; 99/102; 96/98; 100/101 |
| both | 198 (13) | 170/181 = 93.9% [82.9, 98.3] | 167/178 = 93.8% [82.9, 98.3] | 161/172 = 93.6% [79.1, 98.3] | 479/515 = 93.0% [70.5, 97.5] | 138; 100/104; 96/98; 101/102 |
| global | 31 (10) | 20/25 = 80.0% [71.4, 100.0] | 20/25 = 80.0% [71.4, 100.0] | 17/22 = 77.3% [64.7, 100.0] | 47/78 = 60.3% [40.4, 72.1] | 118; 93/96; 90/93; 93/94 |
| no behaviour | 20 (5) | 16/21 = 76.2% [66.7, 100.0] | 16/21 = 76.2% [66.7, 100.0] | 14/19 = 73.7% [62.5, 100.0] | 39/64 = 60.9% [28.6, 72.7] | 116; 92/94; 89/91; 94/96 |

**Paired comparisons** (pass@2 total, pairs; CI on the paired difference; sign test on discordant tasks).

| Level | Comparison | oned real role | oned demo roles | Dev |
|---|---|---|---|---|
| behaviour alone | canon minus abs | 179 vs 179: +0 [+0, +0]; tasks 0:0 does not separate | 541 vs 541: +0 [+0, +0]; tasks 0:0 does not separate | 29 vs 24: +5 [-1, +11]; tasks 7:2, sign p = 0.180 does not separate |
| behaviour alone | both minus canon | 179 vs 179: +0 [+0, +0]; tasks 0:0 does not separate | 541 vs 541: +0 [+0, +0]; tasks 0:0 does not separate | 31 vs 29: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | canon minus global | 179 vs 11: +168 [+48, +313]; tasks 10:0, sign p = 0.002 separates | 541 vs 50: +491 [+127, +927]; tasks 12:3, sign p = 0.035 separates | 29 vs 2: +27 [+17, +38]; tasks 28:1, sign p = 0.000 separates |
| behaviour alone | abs minus global | 179 vs 11: +168 [+48, +313]; tasks 10:0, sign p = 0.002 separates | 541 vs 50: +491 [+127, +927]; tasks 12:3, sign p = 0.035 separates | 24 vs 2: +22 [+13, +32]; tasks 23:1, sign p = 0.000 separates |
| system | canon minus abs | 198 vs 198: +0 [+0, +0]; tasks 0:0 does not separate | 598 vs 598: +0 [+0, +0]; tasks 0:0 does not separate | 136 vs 133: +3 [-2, +8]; tasks 5:2, sign p = 0.453 does not separate |
| system | both minus canon | 198 vs 198: +0 [+0, +0]; tasks 0:0 does not separate | 598 vs 598: +0 [+0, +0]; tasks 0:0 does not separate | 138 vs 136: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | canon minus global | 198 vs 31: +167 [+47, +312]; tasks 10:0, sign p = 0.002 separates | 598 vs 109: +489 [+124, +924]; tasks 12:3, sign p = 0.035 separates | 136 vs 118: +18 [+9, +28]; tasks 20:2, sign p = 0.000 separates |
| system | abs minus global | 198 vs 31: +167 [+47, +312]; tasks 10:0, sign p = 0.002 separates | 598 vs 109: +489 [+124, +924]; tasks 12:3, sign p = 0.035 separates | 133 vs 118: +15 [+7, +24]; tasks 17:2, sign p = 0.001 separates |

**Wrong answers added by `both` over `canon`** (wrong count both minus canon; negative = fewer).

| Level | Rule | Real role | Dev |
|---|---|---|---|
| behaviour alone | evidence >= 0.99 | 6 vs 6: +0 [+0, +0]; tasks 0:0 does not separate | 3 vs 1: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | v5 | 6 vs 6: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 0: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | FA-LOO + (c) | 6 vs 6: +0 [+0, +0]; tasks 0:0 does not separate | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate |
| system | evidence >= 0.99 | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | 4 vs 2: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | v5 | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 1: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate |
| system | FA-LOO + (c) | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate |

Items solved by exactly one of canon / abs, behaviour alone:
- canon only: []
- abs only: []
- global only (vs canon): ['1d_scale_dp/1d_scale_dp_24#0']; canon only (vs global): ['1d_denoising_1c/1d_denoising_1c_26#0', '1d_denoising_1c/1d_denoising_1c_27#0', '1d_denoising_1c/1d_denoising_1c_37#0', '1d_denoising_1c/1d_denoising_1c_38#0', '1d_denoising_1c/1d_denoising_1c_4#0', '1d_denoising_1c/1d_denoising_1c_8#0', '1d_flip/1d_flip_28#0', '1d_flip/1d_flip_33#0', '1d_hollow/1d_hollow_25#0', '1d_hollow/1d_hollow_36#0', '1d_hollow/1d_hollow_43#0', '1d_hollow/1d_hollow_44#0', '1d_move_1p/1d_move_1p_15#0', '1d_move_1p/1d_move_1p_21#0', '1d_move_1p/1d_move_1p_23#0', '1d_move_1p/1d_move_1p_34#0', '1d_move_1p/1d_move_1p_39#0', '1d_move_1p/1d_move_1p_7#0', '1d_move_2p/1d_move_2p_15#0', '1d_move_2p/1d_move_2p_21#0', '1d_move_2p/1d_move_2p_23#0', '1d_move_2p/1d_move_2p_34#0', '1d_move_2p/1d_move_2p_39#0', '1d_move_2p/1d_move_2p_7#0', '1d_move_2p_dp/1d_move_2p_dp_15#0', '1d_move_2p_dp/1d_move_2p_dp_23#0', '1d_move_2p_dp/1d_move_2p_dp_34#0', '1d_move_2p_dp/1d_move_2p_dp_39#0', '1d_move_2p_dp/1d_move_2p_dp_7#0', '1d_move_3p/1d_move_3p_15#0', '1d_move_3p/1d_move_3p_21#0', '1d_move_3p/1d_move_3p_23#0', '1d_move_3p/1d_move_3p_34#0', '1d_move_3p/1d_move_3p_39#0', '1d_move_3p/1d_move_3p_7#0', '1d_pcopy_1c/1d_pcopy_1c_0#0', '1d_pcopy_1c/1d_pcopy_1c_1#0', '1d_pcopy_1c/1d_pcopy_1c_10#0', '1d_pcopy_1c/1d_pcopy_1c_11#0', '1d_pcopy_1c/1d_pcopy_1c_12#0', '1d_pcopy_1c/1d_pcopy_1c_13#0', '1d_pcopy_1c/1d_pcopy_1c_14#0', '1d_pcopy_1c/1d_pcopy_1c_15#0', '1d_pcopy_1c/1d_pcopy_1c_16#0', '1d_pcopy_1c/1d_pcopy_1c_18#0', '1d_pcopy_1c/1d_pcopy_1c_19#0', '1d_pcopy_1c/1d_pcopy_1c_2#0', '1d_pcopy_1c/1d_pcopy_1c_20#0', '1d_pcopy_1c/1d_pcopy_1c_21#0', '1d_pcopy_1c/1d_pcopy_1c_22#0', '1d_pcopy_1c/1d_pcopy_1c_23#0', '1d_pcopy_1c/1d_pcopy_1c_24#0', '1d_pcopy_1c/1d_pcopy_1c_25#0', '1d_pcopy_1c/1d_pcopy_1c_26#0', '1d_pcopy_1c/1d_pcopy_1c_27#0', '1d_pcopy_1c/1d_pcopy_1c_28#0', '1d_pcopy_1c/1d_pcopy_1c_29#0', '1d_pcopy_1c/1d_pcopy_1c_3#0', '1d_pcopy_1c/1d_pcopy_1c_30#0', '1d_pcopy_1c/1d_pcopy_1c_31#0', '1d_pcopy_1c/1d_pcopy_1c_32#0', '1d_pcopy_1c/1d_pcopy_1c_33#0', '1d_pcopy_1c/1d_pcopy_1c_34#0', '1d_pcopy_1c/1d_pcopy_1c_35#0', '1d_pcopy_1c/1d_pcopy_1c_37#0', '1d_pcopy_1c/1d_pcopy_1c_38#0', '1d_pcopy_1c/1d_pcopy_1c_39#0', '1d_pcopy_1c/1d_pcopy_1c_4#0', '1d_pcopy_1c/1d_pcopy_1c_40#0', '1d_pcopy_1c/1d_pcopy_1c_41#0', '1d_pcopy_1c/1d_pcopy_1c_42#0', '1d_pcopy_1c/1d_pcopy_1c_43#0', '1d_pcopy_1c/1d_pcopy_1c_44#0', '1d_pcopy_1c/1d_pcopy_1c_45#0', '1d_pcopy_1c/1d_pcopy_1c_46#0', '1d_pcopy_1c/1d_pcopy_1c_47#0', '1d_pcopy_1c/1d_pcopy_1c_48#0', '1d_pcopy_1c/1d_pcopy_1c_49#0', '1d_pcopy_1c/1d_pcopy_1c_5#0', '1d_pcopy_1c/1d_pcopy_1c_6#0', '1d_pcopy_1c/1d_pcopy_1c_7#0', '1d_pcopy_1c/1d_pcopy_1c_8#0', '1d_pcopy_mc/1d_pcopy_mc_0#0', '1d_pcopy_mc/1d_pcopy_mc_1#0', '1d_pcopy_mc/1d_pcopy_mc_10#0', '1d_pcopy_mc/1d_pcopy_mc_11#0', '1d_pcopy_mc/1d_pcopy_mc_12#0', '1d_pcopy_mc/1d_pcopy_mc_13#0', '1d_pcopy_mc/1d_pcopy_mc_14#0', '1d_pcopy_mc/1d_pcopy_mc_15#0', '1d_pcopy_mc/1d_pcopy_mc_16#0', '1d_pcopy_mc/1d_pcopy_mc_17#0', '1d_pcopy_mc/1d_pcopy_mc_18#0', '1d_pcopy_mc/1d_pcopy_mc_19#0', '1d_pcopy_mc/1d_pcopy_mc_2#0', '1d_pcopy_mc/1d_pcopy_mc_20#0', '1d_pcopy_mc/1d_pcopy_mc_21#0', '1d_pcopy_mc/1d_pcopy_mc_22#0', '1d_pcopy_mc/1d_pcopy_mc_23#0', '1d_pcopy_mc/1d_pcopy_mc_24#0', '1d_pcopy_mc/1d_pcopy_mc_25#0', '1d_pcopy_mc/1d_pcopy_mc_26#0', '1d_pcopy_mc/1d_pcopy_mc_27#0', '1d_pcopy_mc/1d_pcopy_mc_28#0', '1d_pcopy_mc/1d_pcopy_mc_29#0', '1d_pcopy_mc/1d_pcopy_mc_3#0', '1d_pcopy_mc/1d_pcopy_mc_30#0', '1d_pcopy_mc/1d_pcopy_mc_31#0', '1d_pcopy_mc/1d_pcopy_mc_32#0', '1d_pcopy_mc/1d_pcopy_mc_33#0', '1d_pcopy_mc/1d_pcopy_mc_34#0', '1d_pcopy_mc/1d_pcopy_mc_35#0', '1d_pcopy_mc/1d_pcopy_mc_36#0', '1d_pcopy_mc/1d_pcopy_mc_37#0', '1d_pcopy_mc/1d_pcopy_mc_38#0', '1d_pcopy_mc/1d_pcopy_mc_39#0', '1d_pcopy_mc/1d_pcopy_mc_4#0', '1d_pcopy_mc/1d_pcopy_mc_40#0', '1d_pcopy_mc/1d_pcopy_mc_41#0', '1d_pcopy_mc/1d_pcopy_mc_42#0', '1d_pcopy_mc/1d_pcopy_mc_43#0', '1d_pcopy_mc/1d_pcopy_mc_44#0', '1d_pcopy_mc/1d_pcopy_mc_45#0', '1d_pcopy_mc/1d_pcopy_mc_46#0', '1d_pcopy_mc/1d_pcopy_mc_47#0', '1d_pcopy_mc/1d_pcopy_mc_48#0', '1d_pcopy_mc/1d_pcopy_mc_49#0', '1d_pcopy_mc/1d_pcopy_mc_5#0', '1d_pcopy_mc/1d_pcopy_mc_6#0', '1d_pcopy_mc/1d_pcopy_mc_7#0', '1d_recolor_cnt/1d_recolor_cnt_1#0', '1d_recolor_cnt/1d_recolor_cnt_10#0', '1d_recolor_cnt/1d_recolor_cnt_11#0', '1d_recolor_cnt/1d_recolor_cnt_12#0', '1d_recolor_cnt/1d_recolor_cnt_13#0', '1d_recolor_cnt/1d_recolor_cnt_14#0', '1d_recolor_cnt/1d_recolor_cnt_15#0', '1d_recolor_cnt/1d_recolor_cnt_16#0', '1d_recolor_cnt/1d_recolor_cnt_17#0', '1d_recolor_cnt/1d_recolor_cnt_18#0', '1d_recolor_cnt/1d_recolor_cnt_19#0', '1d_recolor_cnt/1d_recolor_cnt_21#0', '1d_recolor_cnt/1d_recolor_cnt_22#0', '1d_recolor_cnt/1d_recolor_cnt_23#0', '1d_recolor_cnt/1d_recolor_cnt_24#0', '1d_recolor_cnt/1d_recolor_cnt_25#0', '1d_recolor_cnt/1d_recolor_cnt_26#0', '1d_recolor_cnt/1d_recolor_cnt_29#0', '1d_recolor_cnt/1d_recolor_cnt_3#0', '1d_recolor_cnt/1d_recolor_cnt_30#0', '1d_recolor_cnt/1d_recolor_cnt_31#0', '1d_recolor_cnt/1d_recolor_cnt_35#0', '1d_recolor_cnt/1d_recolor_cnt_36#0', '1d_recolor_cnt/1d_recolor_cnt_38#0', '1d_recolor_cnt/1d_recolor_cnt_39#0', '1d_recolor_cnt/1d_recolor_cnt_4#0', '1d_recolor_cnt/1d_recolor_cnt_40#0', '1d_recolor_cnt/1d_recolor_cnt_41#0', '1d_recolor_cnt/1d_recolor_cnt_43#0', '1d_recolor_cnt/1d_recolor_cnt_44#0', '1d_recolor_cnt/1d_recolor_cnt_45#0', '1d_recolor_cnt/1d_recolor_cnt_46#0', '1d_recolor_cnt/1d_recolor_cnt_47#0', '1d_recolor_cnt/1d_recolor_cnt_48#0', '1d_recolor_cnt/1d_recolor_cnt_49#0', '1d_recolor_cnt/1d_recolor_cnt_5#0', '1d_recolor_cnt/1d_recolor_cnt_8#0', '1d_recolor_cnt/1d_recolor_cnt_9#0', '1d_scale_dp/1d_scale_dp_39#0']

## Test 2. Prediction

**Precision of the top answer by evidence bucket** (buckets fixed on development data).

| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |
|---|---|---|---|---|
| full system, real | 170/181 = 93.9% [82.9, 98.3] | 9/17 = 52.9% [25.0, 72.2] | 0/1 = 0.0% [0.0, 0.0] | 19/128 = 14.8% [10.1, 21.3] |
| full system, demo | 504/549 = 91.8% [72.0, 96.8] | 30/57 = 52.6% [35.4, 63.9] | 0/5 = 0.0% [0.0, 0.0] | 58/309 = 18.8% [13.9, 23.8] |
| full system, dev | 100/104 = 96.2% [92.0, 99.1] | 25/34 = 73.5% [57.6, 88.0] | 0/4 = 0.0% [0.0, 0.0] | 9/97 = 9.3% [3.8, 15.4] |
| self-model, real | 0/0 | 0/0 | 0/0 | 0/0 |
| periodic, real | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior, real | 154/160 = 96.2% [88.1, 100.0] | 5/11 = 45.5% [0.0, 75.0] | 0/0 | 20/130 = 15.4% [10.1, 23.2] |
| dynamics, real | 16/21 = 76.2% [66.7, 100.0] | 1/2 = 50.0% [50.0, 50.0] | 0/0 | 0/0 |
| composition, real | 0/0 | 0/0 | 0/0 | 0/0 |
| association, real | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, real | 0/0 | 3/4 = 75.0% [75.0, 75.0] | 0/1 = 0.0% [0.0, 0.0] | 0/4 = 0.0% [0.0, 0.0] |
| field, real | 0/0 | 0/0 | 0/1 = 0.0% [0.0, 0.0] | 0/0 |
| self-model, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| periodic, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| behavior, demo | 464/483 = 96.1% [81.6, 98.6] | 15/34 = 44.1% [15.8, 60.0] | 0/6 = 0.0% [0.0, 0.0] | 58/308 = 18.8% [14.1, 23.9] |
| dynamics, demo | 39/62 = 62.9% [28.3, 73.8] | 10/13 = 76.9% [72.7, 100.0] | 0/0 | 0/0 |
| composition, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| association, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, demo | 2/7 = 28.6% [28.6, 28.6] | 5/12 = 41.7% [0.0, 45.5] | 0/0 | 2/11 = 18.2% [0.0, 100.0] |
| field, demo | 0/2 = 0.0% [0.0, 0.0] | 0/1 = 0.0% [0.0, 0.0] | 0/0 | 0/0 |
| behavior raw, real | 148/154 = 96.1% [85.7, 100.0] | 11/17 = 64.7% [41.7, 85.7] | 0/0 | 20/130 = 15.4% [10.1, 23.2] |
| pattern raw, real | 0/0 | 3/4 = 75.0% [75.0, 75.0] | 0/1 = 0.0% [0.0, 0.0] | 0/4 = 0.0% [0.0, 0.0] |
| composition raw, real | 0/0 | 0/0 | 0/0 | 0/0 |

**T2a. Evidence >= 0.99 minus below 0.99 (top answer, full system).**

- real: 170/181 = 93.9% [82.9, 98.3] vs 28/146 = 19.2% [12.7, 27.6]: +74.7 pts [+61.2, +82.9] separates. >=0.99 vs [0.5,0.99): +41.0 pts [+19.7, +70.6] separates. [0.5,0.99) vs below 0.5: +38.2 pts [+9.5, +58.2] separates. AUROC of evidence 0.913 [0.807, 0.954], n = 327.
- demo: 504/549 = 91.8% [72.0, 96.8] vs 88/371 = 23.7% [17.6, 30.4]: +68.1 pts [+48.0, +76.8] separates. >=0.99 vs [0.5,0.99): +39.2 pts [+18.4, +57.9] separates. [0.5,0.99) vs below 0.5: +34.2 pts [+17.2, +45.3] separates. AUROC of evidence 0.907 [0.756, 0.946], n = 920.
- dev: 100/104 = 96.2% [92.0, 99.1] vs 34/135 = 25.2% [18.0, 32.6]: +71.0 pts [+62.7, +79.2] separates. >=0.99 vs [0.5,0.99): +22.6 pts [+7.6, +39.3] separates. [0.5,0.99) vs below 0.5: +64.6 pts [+47.7, +80.2] separates. AUROC of evidence 0.922 [0.881, 0.957], n = 239.

**T2b. Paired precision differences, real role (demo roles in brackets where measured).**

- v5 minus fit: real +28.2 pts [+13.4, +47.0] separates; demo +25.1 pts [+12.8, +37.8] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus fit: real +28.0 pts [+13.4, +45.7] separates; demo +25.2 pts [+12.8, +38.0] separates; dev +28.3 pts [+21.5, +35.5] separates
- a minus fit: real +28.0 pts [+13.4, +45.7] separates; demo +25.0 pts [+12.7, +37.4] separates; dev +27.4 pts [+20.2, +34.9] separates
- fc minus v5: real -0.2 pts [-4.2, +0.1] does not separate; demo +0.2 pts [-3.5, +1.7] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- fc minus a: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.2 pts [+0.0, +1.0] does not separate; dev +0.9 pts [-0.0, +3.1] does not separate
- v5t minus fitt: real +28.2 pts [+13.4, +47.0] separates; demo +25.1 pts [+12.8, +37.8] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus v5t: real -0.2 pts [-4.2, +0.1] does not separate; demo +0.2 pts [-3.5, +1.7] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- p4 minus v5: real -0.2 pts [-2.3, +0.0] does not separate; demo +0.5 pts [-1.2, +1.6] does not separate; dev +1.0 pts [+0.0, +3.3] does not separate

**T2c. Demo roles minus real role, by rule.**

- FA-LOO + (c): -0.6 pts [-8.5, +2.7] does not separate
- (a) only: -0.8 pts [-9.0, +2.5] does not separate
- v5: -1.0 pts [-9.3, +2.5] does not separate
- v5 top only: -1.0 pts [-9.3, +2.5] does not separate
- fit-only: +2.2 pts [-2.0, +5.2] does not separate

**FA-LOO + (c) by concept group, and the gap with each group left out.**

| Group | Real role | Demo roles | v5 real | Gap (demo - real) with this group left out |
|---|---|---|---|---|
| 1d_denoising_1c | 1/1 | 1/1 | 4/4 | -0.6 pts [-8.2, +2.8] does not separate |
| 1d_denoising_mc | 0/0 | 0/0 | 0/0 | -0.6 pts [-8.5, +2.7] does not separate |
| 1d_fill | 0/0 | 0/3 | 0/0 | -0.0 pts [-6.7, +3.3] does not separate |
| 1d_flip | 0/0 | 0/0 | 0/0 | -0.6 pts [-8.5, +2.7] does not separate |
| 1d_hollow | 0/0 | 0/1 | 2/2 | -0.4 pts [-7.9, +3.0] does not separate |
| 1d_mirror | 0/1 | 0/0 | 0/1 | -1.1 pts [-10.1, +1.9] does not separate |
| 1d_move_1p | 3/3 | 9/10 | 4/4 | -0.4 pts [-8.4, +3.1] does not separate |
| 1d_move_2p | 3/3 | 9/10 | 3/3 | -0.4 pts [-8.4, +3.1] does not separate |
| 1d_move_2p_dp | 5/6 | 17/23 | 5/6 | -0.1 pts [-8.3, +3.4] does not separate |
| 1d_move_3p | 3/3 | 9/10 | 3/3 | -0.4 pts [-8.4, +3.0] does not separate |
| 1d_move_dp | 4/5 | 14/20 | 5/6 | -0.1 pts [-8.2, +3.4] does not separate |
| 1d_padded_fill | 0/0 | 0/0 | 0/0 | -0.6 pts [-8.5, +2.7] does not separate |
| 1d_pcopy_1c | 50/50 | 150/150 | 48/48 | -0.8 pts [-13.3, +3.4] does not separate |
| 1d_pcopy_mc | 50/50 | 150/150 | 50/50 | -0.8 pts [-13.2, +3.5] does not separate |
| 1d_recolor_cmp | 0/0 | 0/4 | 0/0 | +0.1 pts [-5.9, +3.5] does not separate |
| 1d_recolor_cnt | 38/42 | 114/120 | 37/41 | -2.2 pts [-12.6, +1.4] does not separate |
| 1d_recolor_oe | 0/1 | 0/0 | 0/1 | -1.1 pts [-10.2, +1.9] does not separate |
| 1d_scale_dp | 4/7 | 6/13 | 6/9 | -0.9 pts [-9.9, +2.6] does not separate |

**Answer sets, real role.**

- v5 vs fc: both 169 (158 right under v5); v5 only 9 (9 right): ['1d_denoising_1c/1d_denoising_1c_4#0', '1d_denoising_1c/1d_denoising_1c_44#0', '1d_denoising_1c/1d_denoising_1c_8#0', '1d_hollow/1d_hollow_25#0', '1d_hollow/1d_hollow_44#0', '1d_move_1p/1d_move_1p_15#0', '1d_move_dp/1d_move_dp_7#0', '1d_scale_dp/1d_scale_dp_44#0', '1d_scale_dp/1d_scale_dp_7#0']; fc only 3 (3 right): ['1d_pcopy_1c/1d_pcopy_1c_35#0', '1d_pcopy_1c/1d_pcopy_1c_5#0', '1d_recolor_cnt/1d_recolor_cnt_8#0']
- v5 vs a: both 169 (158 right under v5); v5 only 9 (9 right): ['1d_denoising_1c/1d_denoising_1c_4#0', '1d_denoising_1c/1d_denoising_1c_44#0', '1d_denoising_1c/1d_denoising_1c_8#0', '1d_hollow/1d_hollow_25#0', '1d_hollow/1d_hollow_44#0', '1d_move_1p/1d_move_1p_15#0', '1d_move_dp/1d_move_dp_7#0', '1d_scale_dp/1d_scale_dp_44#0', '1d_scale_dp/1d_scale_dp_7#0']; a only 3 (3 right): ['1d_pcopy_1c/1d_pcopy_1c_35#0', '1d_pcopy_1c/1d_pcopy_1c_5#0', '1d_recolor_cnt/1d_recolor_cnt_8#0']
- fc vs fit: both 163 (152 right under fc); fc only 9 (9 right): ['1d_move_2p_dp/1d_move_2p_dp_40#0', '1d_move_dp/1d_move_dp_40#0', '1d_pcopy_1c/1d_pcopy_1c_13#0', '1d_pcopy_1c/1d_pcopy_1c_35#0', '1d_pcopy_1c/1d_pcopy_1c_5#0', '1d_pcopy_mc/1d_pcopy_mc_11#0', '1d_pcopy_mc/1d_pcopy_mc_26#0', '1d_pcopy_mc/1d_pcopy_mc_6#0', '1d_recolor_cnt/1d_recolor_cnt_8#0']; fit only 122 (35 right): ['1d_denoising_1c/1d_denoising_1c_13#0', '1d_denoising_1c/1d_denoising_1c_18#0', '1d_denoising_1c/1d_denoising_1c_26#0', '1d_denoising_1c/1d_denoising_1c_27#0', '1d_denoising_1c/1d_denoising_1c_38#0', '1d_denoising_1c/1d_denoising_1c_4#0', '1d_denoising_1c/1d_denoising_1c_44#0', '1d_denoising_1c/1d_denoising_1c_45#0', '1d_denoising_1c/1d_denoising_1c_8#0', '1d_denoising_mc/1d_denoising_mc_12#0', '1d_denoising_mc/1d_denoising_mc_19#0', '1d_denoising_mc/1d_denoising_mc_22#0', '1d_denoising_mc/1d_denoising_mc_47#0', '1d_denoising_mc/1d_denoising_mc_6#0', '1d_flip/1d_flip_12#0', '1d_flip/1d_flip_14#0', '1d_flip/1d_flip_15#0', '1d_flip/1d_flip_2#0', '1d_flip/1d_flip_24#0', '1d_flip/1d_flip_31#0', '1d_flip/1d_flip_40#0', '1d_flip/1d_flip_41#0', '1d_hollow/1d_hollow_1#0', '1d_hollow/1d_hollow_11#0', '1d_hollow/1d_hollow_12#0', '1d_hollow/1d_hollow_25#0', '1d_hollow/1d_hollow_26#0', '1d_hollow/1d_hollow_31#0', '1d_hollow/1d_hollow_36#0', '1d_hollow/1d_hollow_37#0', '1d_hollow/1d_hollow_39#0', '1d_hollow/1d_hollow_42#0', '1d_hollow/1d_hollow_43#0', '1d_hollow/1d_hollow_44#0', '1d_hollow/1d_hollow_45#0', '1d_move_1p/1d_move_1p_1#0', '1d_move_1p/1d_move_1p_11#0', '1d_move_1p/1d_move_1p_13#0', '1d_move_1p/1d_move_1p_15#0', '1d_move_1p/1d_move_1p_16#0', '1d_move_1p/1d_move_1p_19#0', '1d_move_1p/1d_move_1p_21#0', '1d_move_1p/1d_move_1p_22#0', '1d_move_1p/1d_move_1p_24#0', '1d_move_1p/1d_move_1p_25#0', '1d_move_1p/1d_move_1p_27#0', '1d_move_1p/1d_move_1p_28#0', '1d_move_1p/1d_move_1p_34#0', '1d_move_1p/1d_move_1p_39#0', '1d_move_1p/1d_move_1p_40#0', '1d_move_1p/1d_move_1p_41#0', '1d_move_1p/1d_move_1p_6#0', '1d_move_1p/1d_move_1p_8#0', '1d_move_2p/1d_move_2p_1#0', '1d_move_2p/1d_move_2p_11#0', '1d_move_2p/1d_move_2p_13#0', '1d_move_2p/1d_move_2p_15#0', '1d_move_2p/1d_move_2p_16#0', '1d_move_2p/1d_move_2p_19#0', '1d_move_2p/1d_move_2p_21#0', '1d_move_2p/1d_move_2p_22#0', '1d_move_2p/1d_move_2p_24#0', '1d_move_2p/1d_move_2p_25#0', '1d_move_2p/1d_move_2p_27#0', '1d_move_2p/1d_move_2p_28#0', '1d_move_2p/1d_move_2p_34#0', '1d_move_2p/1d_move_2p_39#0', '1d_move_2p/1d_move_2p_40#0', '1d_move_2p/1d_move_2p_41#0', '1d_move_2p/1d_move_2p_6#0', '1d_move_2p/1d_move_2p_8#0', '1d_move_2p_dp/1d_move_2p_dp_1#0', '1d_move_2p_dp/1d_move_2p_dp_15#0', '1d_move_2p_dp/1d_move_2p_dp_16#0', '1d_move_2p_dp/1d_move_2p_dp_17#0', '1d_move_2p_dp/1d_move_2p_dp_2#0', '1d_move_2p_dp/1d_move_2p_dp_22#0', '1d_move_2p_dp/1d_move_2p_dp_23#0', '1d_move_2p_dp/1d_move_2p_dp_24#0', '1d_move_2p_dp/1d_move_2p_dp_26#0', '1d_move_2p_dp/1d_move_2p_dp_34#0', '1d_move_2p_dp/1d_move_2p_dp_39#0', '1d_move_2p_dp/1d_move_2p_dp_41#0', '1d_move_2p_dp/1d_move_2p_dp_48#0', '1d_move_2p_dp/1d_move_2p_dp_5#0', '1d_move_2p_dp/1d_move_2p_dp_7#0', '1d_move_2p_dp/1d_move_2p_dp_9#0', '1d_move_3p/1d_move_3p_1#0', '1d_move_3p/1d_move_3p_11#0', '1d_move_3p/1d_move_3p_13#0', '1d_move_3p/1d_move_3p_15#0', '1d_move_3p/1d_move_3p_16#0', '1d_move_3p/1d_move_3p_19#0', '1d_move_3p/1d_move_3p_21#0', '1d_move_3p/1d_move_3p_22#0', '1d_move_3p/1d_move_3p_24#0', '1d_move_3p/1d_move_3p_25#0', '1d_move_3p/1d_move_3p_27#0', '1d_move_3p/1d_move_3p_28#0', '1d_move_3p/1d_move_3p_34#0', '1d_move_3p/1d_move_3p_39#0', '1d_move_3p/1d_move_3p_40#0', '1d_move_3p/1d_move_3p_41#0', '1d_move_3p/1d_move_3p_6#0', '1d_move_3p/1d_move_3p_8#0', '1d_move_dp/1d_move_dp_17#0', '1d_move_dp/1d_move_dp_7#0', '1d_recolor_cmp/1d_recolor_cmp_10#0', '1d_recolor_cmp/1d_recolor_cmp_36#0', '1d_recolor_cmp/1d_recolor_cmp_48#0', '1d_recolor_cmp/1d_recolor_cmp_49#0', '1d_scale_dp/1d_scale_dp_22#0', '1d_scale_dp/1d_scale_dp_23#0', '1d_scale_dp/1d_scale_dp_24#0', '1d_scale_dp/1d_scale_dp_29#0', '1d_scale_dp/1d_scale_dp_35#0', '1d_scale_dp/1d_scale_dp_39#0', '1d_scale_dp/1d_scale_dp_40#0', '1d_scale_dp/1d_scale_dp_44#0', '1d_scale_dp/1d_scale_dp_50#0', '1d_scale_dp/1d_scale_dp_7#0', '1d_scale_dp/1d_scale_dp_8#0']
- v5 vs fit: both 172 (161 right under v5); v5 only 6 (6 right): ['1d_move_2p_dp/1d_move_2p_dp_40#0', '1d_move_dp/1d_move_dp_40#0', '1d_pcopy_1c/1d_pcopy_1c_13#0', '1d_pcopy_mc/1d_pcopy_mc_11#0', '1d_pcopy_mc/1d_pcopy_mc_26#0', '1d_pcopy_mc/1d_pcopy_mc_6#0']; fit only 113 (26 right): ['1d_denoising_1c/1d_denoising_1c_13#0', '1d_denoising_1c/1d_denoising_1c_18#0', '1d_denoising_1c/1d_denoising_1c_26#0', '1d_denoising_1c/1d_denoising_1c_27#0', '1d_denoising_1c/1d_denoising_1c_38#0', '1d_denoising_1c/1d_denoising_1c_45#0', '1d_denoising_mc/1d_denoising_mc_12#0', '1d_denoising_mc/1d_denoising_mc_19#0', '1d_denoising_mc/1d_denoising_mc_22#0', '1d_denoising_mc/1d_denoising_mc_47#0', '1d_denoising_mc/1d_denoising_mc_6#0', '1d_flip/1d_flip_12#0', '1d_flip/1d_flip_14#0', '1d_flip/1d_flip_15#0', '1d_flip/1d_flip_2#0', '1d_flip/1d_flip_24#0', '1d_flip/1d_flip_31#0', '1d_flip/1d_flip_40#0', '1d_flip/1d_flip_41#0', '1d_hollow/1d_hollow_1#0', '1d_hollow/1d_hollow_11#0', '1d_hollow/1d_hollow_12#0', '1d_hollow/1d_hollow_26#0', '1d_hollow/1d_hollow_31#0', '1d_hollow/1d_hollow_36#0', '1d_hollow/1d_hollow_37#0', '1d_hollow/1d_hollow_39#0', '1d_hollow/1d_hollow_42#0', '1d_hollow/1d_hollow_43#0', '1d_hollow/1d_hollow_45#0', '1d_move_1p/1d_move_1p_1#0', '1d_move_1p/1d_move_1p_11#0', '1d_move_1p/1d_move_1p_13#0', '1d_move_1p/1d_move_1p_16#0', '1d_move_1p/1d_move_1p_19#0', '1d_move_1p/1d_move_1p_21#0', '1d_move_1p/1d_move_1p_22#0', '1d_move_1p/1d_move_1p_24#0', '1d_move_1p/1d_move_1p_25#0', '1d_move_1p/1d_move_1p_27#0', '1d_move_1p/1d_move_1p_28#0', '1d_move_1p/1d_move_1p_34#0', '1d_move_1p/1d_move_1p_39#0', '1d_move_1p/1d_move_1p_40#0', '1d_move_1p/1d_move_1p_41#0', '1d_move_1p/1d_move_1p_6#0', '1d_move_1p/1d_move_1p_8#0', '1d_move_2p/1d_move_2p_1#0', '1d_move_2p/1d_move_2p_11#0', '1d_move_2p/1d_move_2p_13#0', '1d_move_2p/1d_move_2p_15#0', '1d_move_2p/1d_move_2p_16#0', '1d_move_2p/1d_move_2p_19#0', '1d_move_2p/1d_move_2p_21#0', '1d_move_2p/1d_move_2p_22#0', '1d_move_2p/1d_move_2p_24#0', '1d_move_2p/1d_move_2p_25#0', '1d_move_2p/1d_move_2p_27#0', '1d_move_2p/1d_move_2p_28#0', '1d_move_2p/1d_move_2p_34#0', '1d_move_2p/1d_move_2p_39#0', '1d_move_2p/1d_move_2p_40#0', '1d_move_2p/1d_move_2p_41#0', '1d_move_2p/1d_move_2p_6#0', '1d_move_2p/1d_move_2p_8#0', '1d_move_2p_dp/1d_move_2p_dp_1#0', '1d_move_2p_dp/1d_move_2p_dp_15#0', '1d_move_2p_dp/1d_move_2p_dp_16#0', '1d_move_2p_dp/1d_move_2p_dp_17#0', '1d_move_2p_dp/1d_move_2p_dp_2#0', '1d_move_2p_dp/1d_move_2p_dp_22#0', '1d_move_2p_dp/1d_move_2p_dp_23#0', '1d_move_2p_dp/1d_move_2p_dp_24#0', '1d_move_2p_dp/1d_move_2p_dp_26#0', '1d_move_2p_dp/1d_move_2p_dp_34#0', '1d_move_2p_dp/1d_move_2p_dp_39#0', '1d_move_2p_dp/1d_move_2p_dp_41#0', '1d_move_2p_dp/1d_move_2p_dp_48#0', '1d_move_2p_dp/1d_move_2p_dp_5#0', '1d_move_2p_dp/1d_move_2p_dp_7#0', '1d_move_2p_dp/1d_move_2p_dp_9#0', '1d_move_3p/1d_move_3p_1#0', '1d_move_3p/1d_move_3p_11#0', '1d_move_3p/1d_move_3p_13#0', '1d_move_3p/1d_move_3p_15#0', '1d_move_3p/1d_move_3p_16#0', '1d_move_3p/1d_move_3p_19#0', '1d_move_3p/1d_move_3p_21#0', '1d_move_3p/1d_move_3p_22#0', '1d_move_3p/1d_move_3p_24#0', '1d_move_3p/1d_move_3p_25#0', '1d_move_3p/1d_move_3p_27#0', '1d_move_3p/1d_move_3p_28#0', '1d_move_3p/1d_move_3p_34#0', '1d_move_3p/1d_move_3p_39#0', '1d_move_3p/1d_move_3p_40#0', '1d_move_3p/1d_move_3p_41#0', '1d_move_3p/1d_move_3p_6#0', '1d_move_3p/1d_move_3p_8#0', '1d_move_dp/1d_move_dp_17#0', '1d_recolor_cmp/1d_recolor_cmp_10#0', '1d_recolor_cmp/1d_recolor_cmp_36#0', '1d_recolor_cmp/1d_recolor_cmp_48#0', '1d_recolor_cmp/1d_recolor_cmp_49#0', '1d_scale_dp/1d_scale_dp_22#0', '1d_scale_dp/1d_scale_dp_23#0', '1d_scale_dp/1d_scale_dp_24#0', '1d_scale_dp/1d_scale_dp_29#0', '1d_scale_dp/1d_scale_dp_35#0', '1d_scale_dp/1d_scale_dp_39#0', '1d_scale_dp/1d_scale_dp_40#0', '1d_scale_dp/1d_scale_dp_50#0', '1d_scale_dp/1d_scale_dp_8#0']

Wrong, v5: ['1d_mirror/1d_mirror_37#0', '1d_move_2p_dp/1d_move_2p_dp_20#0', '1d_move_dp/1d_move_dp_20#0', '1d_recolor_cnt/1d_recolor_cnt_0#0', '1d_recolor_cnt/1d_recolor_cnt_2#0', '1d_recolor_cnt/1d_recolor_cnt_34#0', '1d_recolor_cnt/1d_recolor_cnt_42#0', '1d_recolor_oe/1d_recolor_oe_49#0', '1d_scale_dp/1d_scale_dp_3#0', '1d_scale_dp/1d_scale_dp_30#0', '1d_scale_dp/1d_scale_dp_49#0']

Wrong, FA-LOO + (c): ['1d_mirror/1d_mirror_37#0', '1d_move_2p_dp/1d_move_2p_dp_20#0', '1d_move_dp/1d_move_dp_20#0', '1d_recolor_cnt/1d_recolor_cnt_0#0', '1d_recolor_cnt/1d_recolor_cnt_2#0', '1d_recolor_cnt/1d_recolor_cnt_34#0', '1d_recolor_cnt/1d_recolor_cnt_42#0', '1d_recolor_oe/1d_recolor_oe_49#0', '1d_scale_dp/1d_scale_dp_3#0', '1d_scale_dp/1d_scale_dp_30#0', '1d_scale_dp/1d_scale_dp_49#0']

Wrong in both: ['1d_mirror/1d_mirror_37#0', '1d_move_2p_dp/1d_move_2p_dp_20#0', '1d_move_dp/1d_move_dp_20#0', '1d_recolor_cnt/1d_recolor_cnt_0#0', '1d_recolor_cnt/1d_recolor_cnt_2#0', '1d_recolor_cnt/1d_recolor_cnt_34#0', '1d_recolor_cnt/1d_recolor_cnt_42#0', '1d_recolor_oe/1d_recolor_oe_49#0', '1d_scale_dp/1d_scale_dp_3#0', '1d_scale_dp/1d_scale_dp_30#0', '1d_scale_dp/1d_scale_dp_49#0']

Wrong, v5 only: []

Wrong, FA-LOO + (c) only: []

Why FA-LOO abstains on items that have a candidate: {'fold abstains': 127, 'answer': 172, '(a)': 28}

## Test 3. Voting

**T3a. Module contributions, real role.**

| Module | Any candidate | Solves alone (tasks) | Lost when removed | Unique solves (tasks) | Alone, evidence >= 0.99 | Alone, FA-LOO + (c) | Demo: alone / unique | Dev: alone / lost / unique |
|---|---|---|---|---|---|---|---|---|
| self-model | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 9 / 9 / 9 |
| periodic | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 10 / 10 / 10 |
| behavior | 301 | 179 (11) | 178 | 178 (11) | 154/160 = 96.2% [88.1, 100.0] | 148/154 = 96.1% [85.7, 100.0] | 541 / 539 | 31 / 23 / 23 |
| dynamics | 23 | 17 (4) | 16 | 16 (3) | 16/21 = 76.2% [66.7, 100.0] | 15/20 = 75.0% [62.5, 100.0] | 50 / 50 | 10 / 8 / 8 |
| composition | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 59 / 59 / 59 |
| association | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 3 / 3 / 3 |
| pattern | 9 | 3 (1) | 3 | 3 (1) | 0/0 | 0/0 | 9 / 7 | 25 / 16 / 17 |
| field | 1 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 1 / 1 / 1 |

real: full 198, union of modules alone 198; solved by exactly one module 197, two 1, three or more 0 (share exactly one 99.5%). Lost by the vote: 0 []; gained by the vote: 0 [].

demo: full 598, union of modules alone 598; solved by exactly one module 596, two 2, three or more 0 (share exactly one 99.7%). Lost by the vote: 0 []; gained by the vote: 0 [].

dev: full 138, union of modules alone 139; solved by exactly one module 130, two 9, three or more 0 (share exactly one 93.5%). Lost by the vote: 1 ["('54d9e175', 0)"]; gained by the vote: 0 [].

**T3b. Is it a vote? Agreement between modules, and a no-vote baseline.**

| Population | Top answer backed by 2+ modules | Top answer from 1 module | Difference | No-vote: pass@2 vs pool | No-vote vs pool, top answer at evidence >= 0.99 |
|---|---|---|---|---|---|
| real | 1/2 = 50.0% [0.0, 100.0] | 197/325 = 60.6% [34.5, 79.5] | -10.6 pts [-73.9, +56.9] does not separate | pool minus no-vote: 198 vs 198: +0 [+0, +0]; tasks 0:0 does not separate | pool 170/181 = 93.9% [82.9, 98.3]; no-vote 164/175 = 93.7% [80.8, 98.3]; +0.2 pts [+0.0, +2.3] does not separate |
| demo | 2/5 = 40.0% [0.0, 100.0] | 590/915 = 64.5% [37.7, 81.4] | -24.5 pts [-78.5, +41.4] does not separate | pool minus no-vote: 598 vs 598: +0 [+0, +0]; tasks 0:0 does not separate | pool 504/549 = 91.8% [72.0, 96.8]; no-vote 487/527 = 92.4% [70.0, 97.2]; -0.6 pts [-1.7, +1.0] does not separate |
| dev | 9/9 = 100.0% [100.0, 100.0] | 125/230 = 54.3% [48.0, 60.7] | +45.7 pts [+39.3, +52.0] separates | pool minus no-vote: 138 vs 137: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | pool 100/104 = 96.2% [92.0, 99.1]; no-vote 100/103 = 97.1% [93.4, 100.0]; -0.9 pts [-4.4, +2.1] does not separate |

- real, top evidence >= 0.99 only: 2+ modules 1/2 = 50.0% [0.0, 100.0]; 1 module 169/179 = 94.4% [84.2, 98.8]; -44.4 pts [-97.4, +10.9] does not separate
- demo, top evidence >= 0.99 only: 2+ modules 2/4 = 50.0% [0.0, 100.0]; 1 module 502/545 = 92.1% [72.8, 96.9]; -42.1 pts [-95.8, +9.0] does not separate
- dev, top evidence >= 0.99 only: 2+ modules 8/8 = 100.0% [100.0, 100.0]; 1 module 92/96 = 95.8% [91.3, 99.1]; +4.2 pts [+0.9, +8.7] separates

**T3c. 8 D8 views vs 1 view** (901 of 901 items).

| Rule | 1 view, real | 8 views, real | Wrong 8 minus 1 | Precision 8 minus 1 | 1 view, demo | 8 views, demo |
|---|---|---|---|---|---|---|
| v5 rule | 167/178 = 93.8% [82.9, 98.3] | 173/189 = 91.5% [77.6, 96.4] | 16 vs 11: +5 [+2, +9]; tasks 5:0, sign p = 0.062 separates | -2.3 pts [-7.5, -0.4] separates | 493/531 = 92.8% [75.2, 97.2] | 511/563 = 90.8% [71.6, 95.8] |
| v5 rule, top answer only | 167/178 = 93.8% [82.9, 98.3] | 173/189 = 91.5% [77.6, 96.4] | 16 vs 11: +5 [+2, +9]; tasks 5:0, sign p = 0.062 separates | -2.3 pts [-7.5, -0.4] separates | 493/531 = 92.8% [75.2, 97.2] | 511/563 = 90.8% [71.6, 95.8] |
| P4 | 161/172 = 93.6% [80.6, 98.2] | 161/172 = 93.6% [80.6, 98.2] | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 475/509 = 93.3% [73.3, 97.6] | 477/509 = 93.7% [75.4, 97.7] |
| FA-LOO (v5 vote) + (c) | 161/172 = 93.6% [79.1, 98.3] | 161/172 = 93.6% [79.1, 98.3] | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 479/515 = 93.0% [70.5, 97.5] | 478/517 = 92.5% [68.1, 97.2] |
| FA-LOO (P4 vote) + (c) | 162/173 = 93.6% [79.8, 98.3] | 162/173 = 93.6% [79.8, 98.3] | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 480/517 = 92.8% [69.9, 97.4] | 479/518 = 92.5% [68.2, 97.1] |
| FA-LOO (v5 vote) | 161/172 = 93.6% [79.1, 98.3] | 161/172 = 93.6% [79.1, 98.3] | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 479/522 = 91.8% [67.0, 97.1] | 478/524 = 91.2% [64.8, 96.8] |
| (a) only | 161/172 = 93.6% [79.1, 98.3] | 161/172 = 93.6% [79.1, 98.3] | 11 vs 11: +0 [+0, +0]; tasks 0:0 does not separate | +0.0 pts [+0.0, +0.0] does not separate | 479/516 = 92.8% [69.6, 97.4] | 479/519 = 92.3% [67.7, 97.1] |

- 8-view v5 minus 8-view P4: real -2.1 pts [-6.0, -0.2] separates; demo -2.9 pts [-6.8, -0.9] separates
- 8-view v5 minus 8-view FA-LOO + (c): real -2.1 pts [-5.8, +0.2] does not separate; demo -1.7 pts [-5.0, +2.8] does not separate
- 8-view P4 minus 8-view FA-LOO + (c): real +0.0 pts [-0.2, +1.5] does not separate; demo +1.3 pts [-0.2, +6.3] does not separate
- pass@2, 8 views minus 1 view: 200 vs 198: +2 [+0, +6]; tasks 1:0, sign p = 1.000 does not separate
- New wrong under 8-view v5: ['1d_denoising_1c/1d_denoising_1c_45#0', '1d_flip/1d_flip_8#0', '1d_hollow/1d_hollow_37#0', '1d_move_1p/1d_move_1p_16#0', '1d_move_2p/1d_move_2p_16#0']
- Wrong at 1-view v5 no longer wrong at 8 views: []
- Wrong under 8-view P4: ['1d_mirror/1d_mirror_37#0', '1d_move_2p_dp/1d_move_2p_dp_20#0', '1d_move_dp/1d_move_dp_20#0', '1d_recolor_cnt/1d_recolor_cnt_0#0', '1d_recolor_cnt/1d_recolor_cnt_2#0', '1d_recolor_cnt/1d_recolor_cnt_34#0', '1d_recolor_cnt/1d_recolor_cnt_42#0', '1d_recolor_oe/1d_recolor_oe_49#0', '1d_scale_dp/1d_scale_dp_3#0', '1d_scale_dp/1d_scale_dp_30#0', '1d_scale_dp/1d_scale_dp_49#0']
- Wrong under 8-view FA-LOO + (c): ['1d_mirror/1d_mirror_37#0', '1d_move_2p_dp/1d_move_2p_dp_20#0', '1d_move_dp/1d_move_dp_20#0', '1d_recolor_cnt/1d_recolor_cnt_0#0', '1d_recolor_cnt/1d_recolor_cnt_2#0', '1d_recolor_cnt/1d_recolor_cnt_34#0', '1d_recolor_cnt/1d_recolor_cnt_42#0', '1d_recolor_oe/1d_recolor_oe_49#0', '1d_scale_dp/1d_scale_dp_3#0', '1d_scale_dp/1d_scale_dp_30#0', '1d_scale_dp/1d_scale_dp_49#0']
- 1-view v5 answers not answered at 8-view FA-LOO + (c): 9
