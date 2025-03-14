set E; # set of employees
set S; # set of shift types
param p >= 1;
set P ordered := 1 .. p; # set of days
set W ordered := 1 .. (p / 7); # set of weekends
set C; # set of contracts




# employee-related sets for pre-fixed days off, contracts
set days_off {E} within P;
set contracts {E} within C;

# sets of preferences for shifts and accompanying weights
set shift_on {E} within {P, S};
param on_weight {e in E, shift_on[e]};
set shift_off {E} within {P, S};
param off_weight {e in E, shift_off[e]};

# starting time and duration of shifts and restricted following shifts
param duration {S};
set follows {S} within S;

# parameters for each contract specifying min/mx consecutive days on/off work 
param max_on {C};
param min_on {C};
param min_off {C};

# parameters for min/max total workload in minutes and upper limits on total shifts and weekends worked
param max_workload {C};
param min_workload {C};
param max_shifts {C, S};
param max_weekends {C};

# demands by the empployer as well as weights for violations
param required {P, S};
param over_weight {P, S};
param under_weight {P, S};




# main assignment variable (starts at 0 for the min_on and min_off constraints)
var X {{0 .. p}, S, E} binary;

# helper variables for conjunctions
var Yew {e in E, w in W} binary;
var Yminon {e in E, contracts[e], P} binary;
var Yminoff {e in E, contracts[e], P} binary;

# slack variables for counting violations
var Vover {P, S} integer, >= 0;
var Vunder {P, S} integer, >= 0;
var Von {e in E, shift_on[e]} binary;
var Voff {e in E, shift_off[e]} binary;




# main objective function counting all violations multiplied by the corresponding weights
minimize satisfaction: sum {e in E, (i, s) in shift_on[e]} (Von[e, i, s] * on_weight[e, i, s])
    + sum {e in E, (i, s) in shift_off[e]} (Voff[e, i, s] * off_weight[e, i, s])
    + sum {i in P, s in S} (Vunder[i, s] * under_weight[i, s] + Vover[i, s] * over_weight[i, s]);




# constraints to fix the supporting variables
subject to on_constraint {e in E, (i, s) in shift_on[e]}:
    Von[e, i, s] = 1 - X[i, s, e];
subject to off_constraint {e in E, (i, s) in shift_off[e]}:
    Voff[e, i, s] = X[i, s, e];

# constraints setting the value for auxiliary variables Yew
subject to yew1 {e in E, w in W, s in S}:
    Yew[e, w] >= X[7 * w, s, e];
subject to yew2 {e in E, w in W, s in S}:
    Yew[e, w] >= X[7 * w - 1, s, e];
subject to yew3 {e in E, w in W}:
    Yew[e, w] <= sum {s in S} (X[7 * w, s, e] + X[7 * w - 1, s, e]);

# constraints setting the value for auxiliary variables Yminon
subject to yminon1 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] <= 1 - sum {s in S} X[i - 1, s, e];
subject to yminon2 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] <= sum {s in S} X[i, s, e];
subject to yminon3 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] >= sum {s in S} (X[i, s, e] - X[i - 1, s, e]);

# constraints setting the value for auxiliary variables Yminoff
subject to yminoff1 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] <= sum {s in S} X[i - 1, s, e];
subject to yminoff2 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] <= 1 - sum {s in S} X[i, s, e];
subject to yminoff3 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] >= sum {s in S} (X[i - 1, s, e] - X[i, s, e]);

# constraint setting day 0 to be a day off
subject to day_zero {s in S, e in E}:
    X[0, s, e] = 0;

# constraint for at most on shift per day
subject to one_shift_a_day {i in P, e in E}:
    sum {s in S} X[i, s, e] <= 1;

# constraint setting pre-fixed days off
subject to days_off_constraint {e in E, i in days_off[e], s in S}:
    X[i, s, e] = 0;

# constraints limiting the min/max consecutive days on/off
subject to max_on_constraint {e in E, c in contracts[e], j in {1 .. (p - max_on[c])}}:
    sum {i in {j .. (j + max_on[c])}, s in S} X[i, s, e] <= max_on[c];
subject to min_on_constraint {e in E, c in contracts[e], j in {1 .. (p - min_on[c] + 1)}}:
    Yminon[e, c, j] * (min_on[c] - 1) - sum {i in {(j + 1) .. (j + min_on[c] - 1)}, s in S} X[i, s, e] <= 0;
subject to min_off_constraint {e in E, c in contracts[e], j in {1 .. (p - min_off[c] + 1)}}:
    Yminoff[e, c, j] * (min_off[c] - 1) - sum {i in {(j + 1) .. (j + min_off[c] - 1)}} (1 - sum {s in S} X[i, s, e]) <= 0;

# constraint limiting the total workload
subject to workload {e in E, c in contracts[e]}:
    min_workload[c] <= sum {i in P, s in S} (X[i, s, e] * duration[s]) <= max_workload[c];

# constraint capping the total amount of shifts worked
subject to max_shifts_constraint {e in E, c in contracts[e], s in S}:
    sum {i in P} X[i, s, e] <= max_shifts[c, s];

# constraint capping the total amount of weekends worked
subject to max_weekends_constraint {e in E, c in contracts[e]}:
    sum {w in W} Yew[e, w] <= max_weekends[c];

# constraint limiting forbidden consecutive shifts
subject to patterns {e in E, i in {1 .. (p - 1)}, s in S, s2 in follows[s]}:
    X[i, s, e] + X[i + 1, s2, e] <= 1;

# constraint for the cover requirements for each shift on each day
subject to cover_requirement {i in P, s in S}:
    sum {e in E} X[i, s, e] - Vover[i, s] + Vunder[i, s] = required[i, s];
