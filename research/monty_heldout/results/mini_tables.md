Dataset `mini`: 149 items (test pairs) in 149 tasks; 528 demo-role items. Dev comparators: 1147 tasks, unit = task.

## Acceptance rules (real and demo roles)

| Rule | Real role | Coverage | Demo roles | Dev (1,147, by task) |
|---|---|---|---|---|
| FA-LOO + (c) | 8/9 = 88.9% [63.6, 100.0] | 6.0% | 30/33 = 90.9% [76.0, 100.0] | 101/102 = 99.0% [96.7, 100.0] |
| FA-LOO (a)+(b) | 8/9 = 88.9% [63.6, 100.0] | 6.0% | 30/33 = 90.9% [76.0, 100.0] | 101/103 = 98.1% [95.0, 100.0] |
| (a) only, full-data answer | 8/9 = 88.9% [63.6, 100.0] | 6.0% | 30/33 = 90.9% [76.0, 100.0] | 102/104 = 98.1% [94.9, 100.0] |
| v5 heuristic (2 attempts) | 11/11 = 100.0% [100.0, 100.0] | 7.4% | 44/45 = 97.8% [91.7, 100.0] | 96/98 = 98.0% [94.7, 100.0] |
| v5 heuristic, top answer only | 11/11 = 100.0% [100.0, 100.0] | 7.4% | 44/45 = 97.8% [91.7, 100.0] | 96/98 = 98.0% [94.7, 100.0] |
| P4 confident (2 attempts) | 11/11 = 100.0% [100.0, 100.0] | 7.4% | 38/39 = 97.4% [90.5, 100.0] | 97/98 = 99.0% [96.6, 100.0] |
| fit to demos only (2 attempts) | 15/29 = 51.7% [33.3, 70.0] | 19.5% | 50/90 = 55.6% [38.8, 70.1] | 111/157 = 70.7% [63.4, 77.6] |
| fit to demos only, top answer only | 15/29 = 51.7% [33.3, 70.0] | 19.5% | 50/90 = 55.6% [38.8, 70.1] | 111/157 = 70.7% [63.4, 77.6] |

pass@2, real role: 20/149 = 13.4% (count CI [12, 29]); tasks with at least one solve: 20/149. Items with any candidate: 55.
Joint P(answer and wrong), FA-LOO + (c), real role: 1/149 = 0.67%. Task-level: 9 tasks answered, 1 with a wrong answer; mean per-task precision 88.9%.

## Test 1. Frames

**behaviour alone.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 14 (14) | 5/6 = 83.3% [50.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/6 = 83.3% [50.0, 100.0] | 17/18 = 94.4% [75.0, 100.0] | 29; 13/14; 13/13; 12/12 |
| abs | 10 (10) | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 17/18 = 94.4% [75.0, 100.0] | 24; 11/12; 11/11; 9/9 |
| both | 14 (14) | 5/6 = 83.3% [50.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 5/6 = 83.3% [50.0, 100.0] | 17/18 = 94.4% [75.0, 100.0] | 31; 13/16; 13/15; 11/11 |
| global | 4 (4) | 2/2 = 100.0% [100.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 5/5 = 100.0% [100.0, 100.0] | 2; 1/2; 1/2; 1/1 |

**system.**

| Arm | pass@2 (tasks) | top answer at evidence >= 0.99 | v5 rule | FA-LOO + (c) real | FA-LOO + (c) demo | Dev: pass@2; >=0.99; v5; FA-LOO + (c) |
|---|---|---|---|---|---|---|
| canon | 20 (20) | 11/12 = 91.7% [72.7, 100.0] | 11/11 = 100.0% [100.0, 100.0] | 8/9 = 88.9% [63.6, 100.0] | 30/33 = 90.9% [76.0, 100.0] | 136; 101/103; 97/98; 103/104 |
| abs | 16 (16) | 11/11 = 100.0% [100.0, 100.0] | 11/11 = 100.0% [100.0, 100.0] | 9/9 = 100.0% [100.0, 100.0] | 32/35 = 91.4% [77.3, 100.0] | 133; 99/102; 96/98; 100/101 |
| both | 20 (20) | 11/12 = 91.7% [72.7, 100.0] | 11/11 = 100.0% [100.0, 100.0] | 8/9 = 88.9% [63.6, 100.0] | 30/33 = 90.9% [76.0, 100.0] | 138; 100/104; 96/98; 101/102 |
| global | 15 (15) | 9/9 = 100.0% [100.0, 100.0] | 9/9 = 100.0% [100.0, 100.0] | 7/7 = 100.0% [100.0, 100.0] | 25/27 = 92.6% [76.9, 100.0] | 118; 93/96; 90/93; 93/94 |
| no behaviour | 11 (11) | 7/7 = 100.0% [100.0, 100.0] | 7/7 = 100.0% [100.0, 100.0] | 6/6 = 100.0% [100.0, 100.0] | 21/23 = 91.3% [73.3, 100.0] | 116; 92/94; 89/91; 94/96 |

**Paired comparisons** (pass@2 total, pairs; CI on the paired difference; sign test on discordant tasks).

| Level | Comparison | mini real role | mini demo roles | Dev |
|---|---|---|---|---|
| behaviour alone | canon minus abs | 14 vs 10: +4 [+1, +8]; tasks 4:0, sign p = 0.125 separates | 47 vs 35: +12 [+4, +22]; tasks 8:0, sign p = 0.008 separates | 29 vs 24: +5 [-1, +11]; tasks 7:2, sign p = 0.180 does not separate |
| behaviour alone | both minus canon | 14 vs 14: +0 [+0, +0]; tasks 0:0 does not separate | 45 vs 47: -2 [-5, +0]; tasks 0:2, sign p = 0.500 does not separate | 31 vs 29: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | canon minus global | 14 vs 4: +10 [+3, +18]; tasks 12:2, sign p = 0.013 separates | 47 vs 20: +27 [+4, +53]; tasks 16:4, sign p = 0.012 separates | 29 vs 2: +27 [+17, +38]; tasks 28:1, sign p = 0.000 separates |
| behaviour alone | abs minus global | 10 vs 4: +6 [+0, +13]; tasks 8:2, sign p = 0.109 does not separate | 35 vs 20: +15 [-6, +39]; tasks 10:4, sign p = 0.180 does not separate | 24 vs 2: +22 [+13, +32]; tasks 23:1, sign p = 0.000 separates |
| system | canon minus abs | 20 vs 16: +4 [+1, +8]; tasks 4:0, sign p = 0.125 separates | 69 vs 60: +9 [+2, +19]; tasks 7:1, sign p = 0.070 separates | 136 vs 133: +3 [-2, +8]; tasks 5:2, sign p = 0.453 does not separate |
| system | both minus canon | 20 vs 20: +0 [+0, +0]; tasks 0:0 does not separate | 66 vs 69: -3 [-7, +0]; tasks 0:3, sign p = 0.250 does not separate | 138 vs 136: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | canon minus global | 20 vs 15: +5 [-1, +11]; tasks 7:2, sign p = 0.180 does not separate | 69 vs 55: +14 [-6, +36]; tasks 11:5, sign p = 0.210 does not separate | 136 vs 118: +18 [+9, +28]; tasks 20:2, sign p = 0.000 separates |
| system | abs minus global | 16 vs 15: +1 [-3, +6]; tasks 3:2, sign p = 1.000 does not separate | 60 vs 55: +5 [-12, +24]; tasks 6:4, sign p = 0.754 does not separate | 133 vs 118: +15 [+7, +24]; tasks 17:2, sign p = 0.001 separates |

**Wrong answers added by `both` over `canon`** (wrong count both minus canon; negative = fewer).

| Level | Rule | Real role | Dev |
|---|---|---|---|
| behaviour alone | evidence >= 0.99 | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | 3 vs 1: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | v5 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 0: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| behaviour alone | FA-LOO + (c) | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate |
| system | evidence >= 0.99 | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | 4 vs 2: +2 [+0, +5]; tasks 2:0, sign p = 0.500 does not separate |
| system | v5 | 0 vs 0: +0 [+0, +0]; tasks 0:0 does not separate | 2 vs 1: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate |
| system | FA-LOO + (c) | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate |

Items solved by exactly one of canon / abs, behaviour alone:
- canon only: ['Change_the_order_of_sticks_l6afheel22a49dadhpf#0', 'Color_corners_of_the_rectangle_l6ab1kfb2tyukiwz069#0', 'Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0', 'One_Color_Collect_together_l6bkbzu66anwnd6daa#0']
- abs only: []
- global only (vs canon): ['Rotate_45_degree_l6bleks8igry3eqt4fn#0', 'find_the_color_of_the_gray_pixels_l6afriful4bel4379yo#0']; canon only (vs global): ['Change_the_order_of_sticks_l6afheel22a49dadhpf#0', 'Color_corners_of_the_rectangle_l6ab1kfb2tyukiwz069#0', 'Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0', 'Importance_of_social_distance_l6afc1q0dm28z9i6egn#0', 'One_Color_Collect_together_l6bkbzu66anwnd6daa#0', 'One_Color_Diagonal_Denoising_l6bktxbcgcze41sald4#0', 'One_Color_Simple_Stuff_l6bkg9unb1kgovxkon6#0', 'OrangeToYellow_l6aasjvev63lnj34jm#0', 'Tree_grow_l6abtiup7kl5z4wkkx4#0', 'chess_pawn_l6bkp4xqvn1t6b1566f#0', 'find_single_cells_l6afg6gtkf27jicef4m#0', 'one_plus_four_l6af5dcogqbhk8pvva#0']

## Test 2. Prediction

**Precision of the top answer by evidence bucket** (buckets fixed on development data).

| Column, role | >= 0.99 | [0.5, 0.99) | (0, 0.5) | 0 |
|---|---|---|---|---|
| full system, real | 11/12 = 91.7% [72.7, 100.0] | 5/7 = 71.4% [33.3, 100.0] | 1/1 = 100.0% [100.0, 100.0] | 3/35 = 8.6% [0.0, 19.0] |
| full system, demo | 44/47 = 93.6% [86.8, 100.0] | 9/18 = 50.0% [14.3, 77.8] | 4/14 = 28.6% [0.0, 60.0] | 8/120 = 6.7% [1.8, 13.0] |
| full system, dev | 100/104 = 96.2% [92.0, 99.1] | 25/34 = 73.5% [57.6, 88.0] | 0/4 = 0.0% [0.0, 0.0] | 9/97 = 9.3% [3.8, 15.4] |
| self-model, real | 0/0 | 0/0 | 0/0 | 0/0 |
| periodic, real | 1/1 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| behavior, real | 5/6 = 83.3% [50.0, 100.0] | 4/6 = 66.7% [20.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 3/32 = 9.4% [0.0, 20.8] |
| dynamics, real | 2/2 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| composition, real | 0/0 | 0/0 | 0/0 | 0/0 |
| association, real | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, real | 3/3 = 100.0% [100.0, 100.0] | 4/4 = 100.0% [100.0, 100.0] | 0/0 | 0/4 = 0.0% [0.0, 0.0] |
| field, real | 1/1 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| self-model, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| periodic, demo | 3/4 = 75.0% [0.0, 100.0] | 0/0 | 0/0 | 0/0 |
| behavior, demo | 25/26 = 96.2% [90.3, 100.0] | 7/18 = 38.9% [7.1, 68.2] | 4/13 = 30.8% [0.0, 64.3] | 9/122 = 7.4% [2.4, 13.8] |
| dynamics, demo | 7/8 = 87.5% [0.0, 100.0] | 0/0 | 0/0 | 0/0 |
| composition, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| association, demo | 0/0 | 0/0 | 0/0 | 0/0 |
| pattern, demo | 12/12 = 100.0% [100.0, 100.0] | 6/7 = 85.7% [40.0, 100.0] | 2/3 = 66.7% [0.0, 100.0] | 4/10 = 40.0% [0.0, 80.0] |
| field, demo | 3/3 = 100.0% [100.0, 100.0] | 0/0 | 0/0 | 0/0 |
| behavior raw, real | 5/6 = 83.3% [50.0, 100.0] | 4/6 = 66.7% [20.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 3/32 = 9.4% [0.0, 20.8] |
| pattern raw, real | 3/3 = 100.0% [100.0, 100.0] | 4/4 = 100.0% [100.0, 100.0] | 0/0 | 0/4 = 0.0% [0.0, 0.0] |
| composition raw, real | 0/0 | 0/0 | 0/0 | 0/0 |

**T2a. Evidence >= 0.99 minus below 0.99 (top answer, full system).**

- real: 11/12 = 91.7% [72.7, 100.0] vs 9/43 = 20.9% [9.3, 34.0]: +70.7 pts [+48.0, +87.9] separates. >=0.99 vs [0.5,0.99): +20.2 pts [-16.7, +62.0] does not separate. [0.5,0.99) vs below 0.5: +60.3 pts [+19.4, +93.3] separates. AUROC of evidence 0.894 [0.794, 0.977], n = 55.
- demo: 44/47 = 93.6% [86.8, 100.0] vs 21/152 = 13.8% [7.1, 21.5]: +79.8 pts [+70.2, +89.0] separates. >=0.99 vs [0.5,0.99): +43.6 pts [+15.1, +81.3] separates. [0.5,0.99) vs below 0.5: +41.0 pts [+2.8, +70.3] separates. AUROC of evidence 0.908 [0.830, 0.961], n = 199.
- dev: 100/104 = 96.2% [92.0, 99.1] vs 34/135 = 25.2% [18.0, 32.6]: +71.0 pts [+62.7, +79.2] separates. >=0.99 vs [0.5,0.99): +22.6 pts [+7.6, +39.3] separates. [0.5,0.99) vs below 0.5: +64.6 pts [+47.7, +80.2] separates. AUROC of evidence 0.922 [0.881, 0.957], n = 239.

**T2b. Paired precision differences, real role (demo roles in brackets where measured).**

- v5 minus fit: real +48.3 pts [+30.0, +66.7] separates; demo +42.2 pts [+28.2, +58.2] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus fit: real +37.2 pts [+8.7, +62.5] separates; demo +35.4 pts [+15.6, +55.1] separates; dev +28.3 pts [+21.5, +35.5] separates
- a minus fit: real +37.2 pts [+8.7, +62.5] separates; demo +35.4 pts [+15.6, +55.1] separates; dev +27.4 pts [+20.2, +34.9] separates
- fc minus v5: real -11.1 pts [-36.4, +0.0] does not separate; demo -6.9 pts [-20.2, +0.0] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- fc minus a: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +0.9 pts [-0.0, +3.1] does not separate
- v5t minus fitt: real +48.3 pts [+30.0, +66.7] separates; demo +42.2 pts [+28.2, +58.2] separates; dev +27.3 pts [+20.2, +34.8] separates
- fc minus v5t: real -11.1 pts [-36.4, +0.0] does not separate; demo -6.9 pts [-20.2, +0.0] does not separate; dev +1.1 pts [+0.0, +3.3] does not separate
- p4 minus v5: real +0.0 pts [+0.0, +0.0] does not separate; demo -0.3 pts [-2.0, +0.0] does not separate; dev +1.0 pts [+0.0, +3.3] does not separate

**T2c. Demo roles minus real role, by rule.**

- FA-LOO + (c): +2.0 pts [-19.0, +26.4] does not separate
- (a) only: +2.0 pts [-19.0, +26.4] does not separate
- v5: -2.2 pts [-8.3, +0.0] does not separate
- v5 top only: -2.2 pts [-8.3, +0.0] does not separate
- fit-only: +3.8 pts [-11.1, +16.4] does not separate

**Answer sets, real role.**

- v5 vs fc: both 8 (8 right under v5); v5 only 3 (3 right): ['WhereToGo_l6abpi9x72c95wdvtgp#0', 'chess_pawn_l6bkp4xqvn1t6b1566f#0', 'stretch_vertically_l6acwqhltn3k0zhgzjo#0']; fc only 1 (0 right): ['Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0']
- v5 vs a: both 8 (8 right under v5); v5 only 3 (3 right): ['WhereToGo_l6abpi9x72c95wdvtgp#0', 'chess_pawn_l6bkp4xqvn1t6b1566f#0', 'stretch_vertically_l6acwqhltn3k0zhgzjo#0']; a only 1 (0 right): ['Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0']
- fc vs fit: both 6 (6 right under fc); fc only 3 (2 right): ['Diagonal_expansion__l6abirdahy8nxqq8mrv#0', 'Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0', 'complete_the_grid_l6advlyw26bcclp5nx3#0']; fit only 23 (9 right): ['Bouncing_Ball_l6acvhhkgcbt8hvve8b#0', 'Color_encoding_updated_l6ae1ybpnzgz9mlmk1#0', 'Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0', 'Good_maze_l69na9a94pkojo20vdi#0', 'Gravity_l6ab99rxv8zu9j4t3bl#0', 'Importance_of_social_distance_l6afc1q0dm28z9i6egn#0', 'Most_Common_color_l6ab0lf3xztbyxsu3p#0', 'One_Color_Collect_together_l6bkbzu66anwnd6daa#0', 'One_Color_Sequence_l6bl12mbpu3ide97bfe#0', 'Razer_reflection_l6afnlpp4vzn49nkx93#0', 'Tree_grow_l6abtiup7kl5z4wkkx4#0', 'WhereToGo_l6abpi9x72c95wdvtgp#0', 'changing_color_if_neighbors_have_same_l6blerss5coxn0ig3ou#0', 'chess_pawn_l6bkp4xqvn1t6b1566f#0', 'color_the_outer_edge_of_the_object_l6abl0slggq9g7sdkyv#0', 'define_boundary_l6aeugn2pfna6pvwdt#0', 'find_the_most_frequent_color_then_color_with_it_l6afx63nce23o4amnx#0', 'fractal_l6bklbsimu8fpp62p6i#0', 'mapping_color_to_shape_l6acypud56b4m1z5409#0', 'pull_inner_gadget_towards_the_side_with_different_color_l6aeiaci4szwtcqghvt#0', 'stretch_vertically_l6acwqhltn3k0zhgzjo#0', 'wrap_blue_around_red_l6ae5b5csckyjb7nsj#0', 'xor_l6bk7mn24iz2pdb4lxp#0']
- v5 vs fit: both 9 (9 right under v5); v5 only 2 (2 right): ['Diagonal_expansion__l6abirdahy8nxqq8mrv#0', 'complete_the_grid_l6advlyw26bcclp5nx3#0']; fit only 20 (6 right): ['Bouncing_Ball_l6acvhhkgcbt8hvve8b#0', 'Color_encoding_updated_l6ae1ybpnzgz9mlmk1#0', 'Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0', 'Good_maze_l69na9a94pkojo20vdi#0', 'Gravity_l6ab99rxv8zu9j4t3bl#0', 'Importance_of_social_distance_l6afc1q0dm28z9i6egn#0', 'Most_Common_color_l6ab0lf3xztbyxsu3p#0', 'One_Color_Collect_together_l6bkbzu66anwnd6daa#0', 'One_Color_Sequence_l6bl12mbpu3ide97bfe#0', 'Razer_reflection_l6afnlpp4vzn49nkx93#0', 'Tree_grow_l6abtiup7kl5z4wkkx4#0', 'changing_color_if_neighbors_have_same_l6blerss5coxn0ig3ou#0', 'color_the_outer_edge_of_the_object_l6abl0slggq9g7sdkyv#0', 'define_boundary_l6aeugn2pfna6pvwdt#0', 'find_the_most_frequent_color_then_color_with_it_l6afx63nce23o4amnx#0', 'fractal_l6bklbsimu8fpp62p6i#0', 'mapping_color_to_shape_l6acypud56b4m1z5409#0', 'pull_inner_gadget_towards_the_side_with_different_color_l6aeiaci4szwtcqghvt#0', 'wrap_blue_around_red_l6ae5b5csckyjb7nsj#0', 'xor_l6bk7mn24iz2pdb4lxp#0']

Wrong, v5: []

Wrong, FA-LOO + (c): ['Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0']

Wrong in both: []

Wrong, v5 only: []

Wrong, FA-LOO + (c) only: ['Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0']

Why FA-LOO abstains on items that have a candidate: {'fold abstains': 20, '(a)': 26, 'answer': 9}

## Test 3. Voting

**T3a. Module contributions, real role.**

| Module | Any candidate | Solves alone (tasks) | Lost when removed | Unique solves (tasks) | Alone, evidence >= 0.99 | Alone, FA-LOO + (c) | Demo: alone / unique | Dev: alone / lost / unique |
|---|---|---|---|---|---|---|---|---|
| self-model | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 9 / 9 / 9 |
| periodic | 1 | 1 (1) | 1 | 1 (1) | 1/1 = 100.0% [100.0, 100.0] | 1/1 = 100.0% [100.0, 100.0] | 3 / 3 | 10 / 10 / 10 |
| behavior | 46 | 14 (14) | 9 | 9 (9) | 5/6 = 83.3% [50.0, 100.0] | 5/6 = 83.3% [50.0, 100.0] | 45 / 31 | 31 / 23 / 23 |
| dynamics | 2 | 2 (2) | 2 | 2 (2) | 2/2 = 100.0% [100.0, 100.0] | 2/2 = 100.0% [100.0, 100.0] | 7 / 7 | 10 / 8 / 8 |
| composition | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 59 / 59 / 59 |
| association | 0 | 0 (0) | 0 | 0 (0) | 0/0 | 0/0 | 0 / 0 | 3 / 3 / 3 |
| pattern | 11 | 7 (7) | 2 | 2 (2) | 3/3 = 100.0% [100.0, 100.0] | 3/3 = 100.0% [100.0, 100.0] | 24 / 12 | 25 / 16 / 17 |
| field | 1 | 1 (1) | 1 | 1 (1) | 1/1 = 100.0% [100.0, 100.0] | 1/1 = 100.0% [100.0, 100.0] | 3 / 1 | 1 / 1 / 1 |

real: full 20, union of modules alone 20; solved by exactly one module 15, two 5, three or more 0 (share exactly one 75.0%). Lost by the vote: 0 []; gained by the vote: 0 [].

demo: full 66, union of modules alone 68; solved by exactly one module 54, two 14, three or more 0 (share exactly one 79.4%). Lost by the vote: 2 ["('Importance_of_social_distance_l6afc1q0dm28z9i6egn#0', 1)", "('chess_pawn_l6bkp4xqvn1t6b1566f#0', 3)"]; gained by the vote: 0 [].

dev: full 138, union of modules alone 139; solved by exactly one module 130, two 9, three or more 0 (share exactly one 93.5%). Lost by the vote: 1 ["('54d9e175', 0)"]; gained by the vote: 0 [].

**T3b. Is it a vote? Agreement between modules, and a no-vote baseline.**

| Population | Top answer backed by 2+ modules | Top answer from 1 module | Difference | No-vote: pass@2 vs pool | No-vote vs pool, top answer at evidence >= 0.99 |
|---|---|---|---|---|---|
| real | 5/5 = 100.0% [100.0, 100.0] | 15/50 = 30.0% [17.6, 43.1] | +70.0 pts [+56.9, +82.5] separates | pool minus no-vote: 20 vs 20: +0 [+0, +0]; tasks 0:0 does not separate | pool 11/12 = 91.7% [72.7, 100.0]; no-vote 11/12 = 91.7% [72.7, 100.0]; +0.0 pts [+0.0, +0.0] does not separate |
| demo | 14/17 = 82.4% [50.0, 100.0] | 51/182 = 28.0% [17.7, 38.7] | +54.3 pts [+21.6, +77.2] separates | pool minus no-vote: 66 vs 66: +0 [+0, +0]; tasks 0:0 does not separate | pool 44/47 = 93.6% [86.8, 100.0]; no-vote 38/41 = 92.7% [83.3, 100.0]; +0.9 pts [+0.0, +5.0] does not separate |
| dev | 9/9 = 100.0% [100.0, 100.0] | 125/230 = 54.3% [48.0, 60.7] | +45.7 pts [+39.3, +52.0] separates | pool minus no-vote: 138 vs 137: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | pool 100/104 = 96.2% [92.0, 99.1]; no-vote 100/103 = 97.1% [93.4, 100.0]; -0.9 pts [-4.4, +2.1] does not separate |

- real, top evidence >= 0.99 only: 2+ modules 3/3 = 100.0% [100.0, 100.0]; 1 module 8/9 = 88.9% [62.5, 100.0]; +11.1 pts [+0.0, +37.5] does not separate
- demo, top evidence >= 0.99 only: 2+ modules 11/11 = 100.0% [100.0, 100.0]; 1 module 33/36 = 91.7% [82.6, 100.0]; +8.3 pts [+0.0, +17.4] does not separate
- dev, top evidence >= 0.99 only: 2+ modules 8/8 = 100.0% [100.0, 100.0]; 1 module 92/96 = 95.8% [91.3, 99.1]; +4.2 pts [+0.9, +8.7] separates

**T3c. 8 D8 views vs 1 view** (149 of 149 items).

| Rule | 1 view, real | 8 views, real | Wrong 8 minus 1 | Precision 8 minus 1 | 1 view, demo | 8 views, demo |
|---|---|---|---|---|---|---|
| v5 rule | 11/11 = 100.0% [100.0, 100.0] | 15/16 = 93.8% [78.9, 100.0] | 1 vs 0: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | -6.2 pts [-21.1, +0.0] does not separate | 44/45 = 97.8% [91.7, 100.0] | 49/56 = 87.5% [75.6, 95.6] |
| v5 rule, top answer only | 11/11 = 100.0% [100.0, 100.0] | 15/16 = 93.8% [78.9, 100.0] | 1 vs 0: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | -6.2 pts [-21.1, +0.0] does not separate | 44/45 = 97.8% [91.7, 100.0] | 49/56 = 87.5% [75.6, 95.6] |
| P4 | 11/11 = 100.0% [100.0, 100.0] | 11/12 = 91.7% [71.4, 100.0] | 1 vs 0: +1 [+0, +3]; tasks 1:0, sign p = 1.000 does not separate | -8.3 pts [-28.6, +0.0] does not separate | 38/39 = 97.4% [90.5, 100.0] | 45/47 = 95.7% [87.2, 100.0] |
| FA-LOO (v5 vote) + (c) | 8/9 = 88.9% [63.6, 100.0] | 10/11 = 90.9% [70.0, 100.0] | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | +2.0 pts [+0.0, +10.0] does not separate | 30/33 = 90.9% [76.0, 100.0] | 40/43 = 93.0% [81.2, 100.0] |
| FA-LOO (P4 vote) + (c) | 8/9 = 88.9% [63.6, 100.0] | 9/10 = 90.0% [66.7, 100.0] | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | +1.1 pts [+0.0, +6.7] does not separate | 30/33 = 90.9% [76.0, 100.0] | 38/41 = 92.7% [80.0, 100.0] |
| FA-LOO (v5 vote) | 8/9 = 88.9% [63.6, 100.0] | 10/11 = 90.9% [70.0, 100.0] | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | +2.0 pts [+0.0, +10.0] does not separate | 30/33 = 90.9% [76.0, 100.0] | 40/43 = 93.0% [81.2, 100.0] |
| (a) only | 8/9 = 88.9% [63.6, 100.0] | 10/11 = 90.9% [70.0, 100.0] | 1 vs 1: +0 [+0, +0]; tasks 0:0 does not separate | +2.0 pts [+0.0, +10.0] does not separate | 30/33 = 90.9% [76.0, 100.0] | 40/43 = 93.0% [81.2, 100.0] |

- 8-view v5 minus 8-view P4: real +2.1 pts [+0.0, +8.9] does not separate; demo -8.2 pts [-17.0, -1.8] separates
- 8-view v5 minus 8-view FA-LOO + (c): real +2.8 pts [-16.0, +25.0] does not separate; demo -5.5 pts [-15.6, +4.3] does not separate
- 8-view P4 minus 8-view FA-LOO + (c): real +0.8 pts [-22.2, +25.0] does not separate; demo +2.7 pts [-0.1, +10.2] does not separate
- pass@2, 8 views minus 1 view: 20 vs 20: +0 [+0, +0]; tasks 0:0 does not separate
- New wrong under 8-view v5: ['clock_l6bka8ape8glx94eysi#0']
- Wrong at 1-view v5 no longer wrong at 8 views: []
- Wrong under 8-view P4: ['clock_l6bka8ape8glx94eysi#0']
- Wrong under 8-view FA-LOO + (c): ['Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0']
- 1-view v5 answers not answered at 8-view FA-LOO + (c): 1
