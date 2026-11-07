**By number of demos, real role (post hoc).**

| n demos | Items | Tasks | FA-LOO + (c) | v5 | fit-only | pass@2 | Bound 1/(n+1) |
|---|---|---|---|---|---|---|---|
| 2 | 5 | 5 | 0/0 | 0/0 | 0/1 | 0 | 0.333 |
| 3 | 82 | 82 | 5/6 | 6/6 | 10/16 | 14 | 0.250 |
| 4 | 46 | 46 | 3/3 | 4/4 | 4/9 | 5 | 0.200 |
| 5 | 11 | 11 | 0/0 | 0/0 | 0/2 | 0 | 0.167 |
| 6 | 3 | 3 | 0/0 | 0/0 | 0/0 | 0 | 0.143 |
| 7 | 1 | 1 | 0/0 | 0/0 | 0/0 | 0 | 0.125 |
| 8 | 1 | 1 | 0/0 | 1/1 | 1/1 | 1 | 0.111 |

**v5 answers that FA-LOO + (c) does not give (real role), with the reason.**

- WhereToGo_l6abpi9x72c95wdvtgp#0: (a), v5 right, n = 3, top from ['field']
- chess_pawn_l6bkp4xqvn1t6b1566f#0: (a), v5 right, n = 8, top from ['behavior', 'pattern']
- stretch_vertically_l6acwqhltn3k0zhgzjo#0: (a), v5 right, n = 4, top from ['dynamics']

**FA-LOO + (c) answers that v5 declines (real role), with the number of fully evidenced distinct answers.**

- Expansion_and_Interpolation_l6acqdnnv8tlnxpx19#0: FA-LOO wrong, fully evidenced answers 2, top evidence 1.23, from ['behavior'], n = 3

Both rules answer: 8 items, FA-LOO right 8, v5 right 8.

**Module alone: FA-LOO + (c) answers vs top answers at evidence >= 0.99 (real role).**

- self-model: 0 and 0, shared 0
- periodic: 1 and 1, shared 1
- behavior: 6 and 6, shared 6
- dynamics: 2 and 2, shared 2
- composition: 0 and 0, shared 0
- association: 0 and 0, shared 0
- pattern: 3 and 3, shared 3
- field: 1 and 1, shared 1

Sum of the modules' answers at evidence >= 0.99 vs the system's (a portfolio has them equal):
12/13 summed over modules; 11/12 = 91.7% [72.7, 100.0] system.

**Frames: paired precision differences at system level (secondary in the plan).**

- v5, canon minus abs: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev +1.0 pts [+0.0, +3.4] does not separate
- v5, both minus canon: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.3 pts [+0.0, +2.0] does not separate; dev -1.0 pts [-3.3, +0.0] does not separate
- v5, canon minus global: real +0.0 pts [+0.0, +0.0] does not separate; demo +3.7 pts [+0.0, +11.8] does not separate; dev +2.2 pts [+0.0, +5.6] does not separate
- v5, both minus no behaviour: real +0.0 pts [+0.0, +0.0] does not separate; demo +1.8 pts [+0.0, +8.2] does not separate; dev +0.2 pts [-2.8, +3.3] does not separate
- FA-LOO + (c), canon minus abs: real -11.1 pts [-36.4, +0.0] does not separate; demo -0.5 pts [-2.7, +0.0] does not separate; dev +0.0 pts [+0.0, +0.1] does not separate
- FA-LOO + (c), both minus canon: real +0.0 pts [+0.0, +0.0] does not separate; demo +0.0 pts [+0.0, +0.0] does not separate; dev -0.0 pts [-0.1, +0.0] does not separate
- FA-LOO + (c), canon minus global: real -11.1 pts [-36.4, +0.0] does not separate; demo -1.7 pts [-10.3, +4.9] does not separate; dev +0.1 pts [+0.0, +0.4] does not separate
- FA-LOO + (c), both minus no behaviour: real -11.1 pts [-36.4, +0.0] does not separate; demo -0.4 pts [-11.1, +10.7] does not separate; dev +1.1 pts [+0.0, +3.6] does not separate

**Evidence of the items solved by behaviour alone, per arm (real role).**

- canon: Change_the_order_of_sticks_l6afheel22a49dadhpf#0 ev 0.0 top right; Color_corners_of_the_rectangle_l6ab1kfb2tyukiwz069#0 ev 0.0 top right; Diagonal_expansion__l6abirdahy8nxqq8mrv#0 ev 1.39 top right; ExpandnContract_l6ab75bv3lho8o820hg#0 ev 1.03 top right; Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0 ev 0.94 top right; Importance_of_social_distance_l6afc1q0dm28z9i6egn#0 ev 0.8067 top right; One_Color_Collect_together_l6bkbzu66anwnd6daa#0 ev 0.0 top right; One_Color_Diagonal_Denoising_l6bktxbcgcze41sald4#0 ev 0.41 top right; One_Color_Simple_Stuff_l6bkg9unb1kgovxkon6#0 ev 1.13 top right; OrangeToYellow_l6aasjvev63lnj34jm#0 ev 1.12 top right; Tree_grow_l6abtiup7kl5z4wkkx4#0 ev 0.74 top right; chess_pawn_l6bkp4xqvn1t6b1566f#0 ev 0.8025 top right; find_single_cells_l6afg6gtkf27jicef4m#0 ev 0.2975 top right; one_plus_four_l6af5dcogqbhk8pvva#0 ev 1.41 top right
- abs: Diagonal_expansion__l6abirdahy8nxqq8mrv#0 ev 1.39 top right; ExpandnContract_l6ab75bv3lho8o820hg#0 ev 1.03 top right; Importance_of_social_distance_l6afc1q0dm28z9i6egn#0 ev 0.35 top right; One_Color_Diagonal_Denoising_l6bktxbcgcze41sald4#0 ev 0.3833 top right; One_Color_Simple_Stuff_l6bkg9unb1kgovxkon6#0 ev 1.13 top right; OrangeToYellow_l6aasjvev63lnj34jm#0 ev 1.1133 top right; Tree_grow_l6abtiup7kl5z4wkkx4#0 ev 0.82 top right; chess_pawn_l6bkp4xqvn1t6b1566f#0 ev 0.8325 top right; find_single_cells_l6afg6gtkf27jicef4m#0 ev 0.2625 top right; one_plus_four_l6af5dcogqbhk8pvva#0 ev 1.41 top right
- both: Change_the_order_of_sticks_l6afheel22a49dadhpf#0 ev 0.0 top right; Color_corners_of_the_rectangle_l6ab1kfb2tyukiwz069#0 ev 0.0 top right; Diagonal_expansion__l6abirdahy8nxqq8mrv#0 ev 1.79 top right; ExpandnContract_l6ab75bv3lho8o820hg#0 ev 1.07 top right; Filling_Corner_Corrected_l6bhlma1gimq40v7dyb#0 ev 0.94 top right; Importance_of_social_distance_l6afc1q0dm28z9i6egn#0 ev 0.8267 top right; One_Color_Collect_together_l6bkbzu66anwnd6daa#0 ev 0.0 top right; One_Color_Diagonal_Denoising_l6bktxbcgcze41sald4#0 ev 0.4633 top right; One_Color_Simple_Stuff_l6bkg9unb1kgovxkon6#0 ev 1.27 top right; OrangeToYellow_l6aasjvev63lnj34jm#0 ev 1.2433 top right; Tree_grow_l6abtiup7kl5z4wkkx4#0 ev 0.9 top right; chess_pawn_l6bkp4xqvn1t6b1566f#0 ev 0.8925 top right; find_single_cells_l6afg6gtkf27jicef4m#0 ev 0.3125 top right; one_plus_four_l6af5dcogqbhk8pvva#0 ev 1.83 top right
- global: Diagonal_expansion__l6abirdahy8nxqq8mrv#0 ev 1.29 top right; ExpandnContract_l6ab75bv3lho8o820hg#0 ev 1.07 top right; Rotate_45_degree_l6bleks8igry3eqt4fn#0 ev 0.3367 top right; find_the_color_of_the_gray_pixels_l6afriful4bel4379yo#0 ev 0.366 top right

**Evidence of the arms' solves on development data (behaviour alone).**

- canon: 29 solves, evidence >= 0.99 in 13, zero in 7
- abs: 24 solves, evidence >= 0.99 in 11, zero in 5
- global: 2 solves, evidence >= 0.99 in 1, zero in 0

**Task-level recount, real role (a task counts once; right = every answered pair right).**

| Rule | Tasks answered | Tasks with a wrong answer | Tasks all right | Mean per-task precision |
|---|---|---|---|---|
| FA-LOO + (c) | 9 | 1 | 8 (CP [52, 100]%) | 88.9% |
| (a) only | 9 | 1 | 8 (CP [52, 100]%) | 88.9% |
| v5 | 11 | 0 | 11 (CP [72, 100]%) | 100.0% |
| fit-only | 29 | 14 | 15 (CP [33, 71]%) | 51.7% |
