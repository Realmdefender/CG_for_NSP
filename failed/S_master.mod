set E; # set of employees
set S; # set of shift types
param p >= 1;
set P ordered := 1 .. p; # set of days
set W ordered := 1 .. (p / 7); # set of weekends
set C; # set of contracts




# employee-related sets for pre-fixed days off, contracts
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
param max_weekends {C};

# demands by the empployer as well as weights for violations
param over_weight {P, S} >= 0;
param under_weight {P, S} >= 0;




set columns {S}; # set of columns for each shift

# assignment values selected for each column
param X {s in S, columns[s], {0 .. p}, E} binary;
param Vover {P, s in S, columns[s]} integer, >= 0;
param Vunder {P, s in S, columns[s]} integer, >= 0;
param Von {e in E, (i, s) in shift_on[e], columns[s]} binary;
param Voff {e in E, (i, s) in shift_off[e], columns[s]} binary;




var lambda {s in S, columns[s]} >= 0;

# helper variables for conjunctions
var Yew {e in E, w in W} binary;
var Yminon {e in E, contracts[e], i in P} binary;
var Yminoff {e in E, contracts[e], i in P} binary;




# main objective function counting all violations multiplied by the corresponding weights
minimize satisfaction: sum {e in E, (i, s) in shift_on[e], k in columns[s]} (lambda[s, k] * Von[e, i, s, k] * on_weight[e, i, s])
    + sum {e in E, (i, s) in shift_off[e], k in columns[s]} (lambda[s, k] * Voff[e, i, s, k] * off_weight[e, i, s])
    + sum {i in P, s in S, k in columns[s]} (lambda[s, k] * (Vunder[i, s, k] * under_weight[i, s] + Vover[i, s, k] * over_weight[i, s]));




# constraints setting the value for auxiliary variables Yew
subject to yew1 {e in E, w in W, s in S}:
    Yew[e, w] >= sum {k in columns[s]} (lambda[s, k] * X[s, k, 7 * w, e]);
subject to yew2 {e in E, w in W, s in S}:
    Yew[e, w] >= sum {k in columns[s]} (lambda[s, k] * X[s, k, 7 * w - 1, e]);
subject to yew3 {e in E, w in W}:
    Yew[e, w] <= sum {s in S, columns[s]} (lambda[s, k] * (X[s, k, 7 * w, e] + X[s, k, 7 * w - 1, e]));

# constraints setting the value for auxiliary variables Yminon
subject to yminon1 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] <= 1 - sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i - 1, e]);
subject to yminon2 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] <= sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e]);
subject to yminon3 {e in E, c in contracts[e], i in P}:
    Yminon[e, c, i] >= sum {s in S, k in columns[s]} (lambda[s, k] * (X[s, k, i, e] - X[s, k, i - 1, e]));

# constraints setting the value for auxiliary variables Yminoff
subject to yminoff1 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] <= sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i - 1, e]);
subject to yminoff2 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] <= 1 - sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e]);
subject to yminoff3 {e in E, c in contracts[e], i in P}:
    Yminoff[e, c, i] >= sum {s in S, k in columns[s]} (lambda[s, k] * (X[s, k, i - 1] - X[s, k, i, e]));

# constraint for at most on shift per day
subject to one_shift_a_day {i in P, e in E}:
    sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e]) <= 1;

# constraints limiting the min/max consecutive days on/off
subject to max_on_constraint {e in E, c in contracts[e], j in {1 .. (p - max_on[c])}}:
    sum {i in {j .. (j + max_on[c])}, s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e]) <= max_on[c];
subject to min_on_constraint {e in E, c in contracts[e], j in {1 .. (p - min_on[c])}}:
    Yminon[e, c, j] * (min_on[c] - 1) - sum {i in {(j + 1) .. (j + min_on[c] - 1)}, s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e]) <= 0;
subject to min_off_constraint {e in E, c in contracts[e], j in {1 .. (p - min_off[c])}}:
    Yminoff[e, c, j] * (min_off[c] - 1) - sum {i in {(j + 1) .. (j + min_off[c] - 1)}} (1 - sum {s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e])) <= 0;

# constraint limiting the total workload
subject to workload {e in E, c in contracts[e]}:
    min_workload[c] <= sum {i in P, s in S, k in columns[s]} (lambda[s, k] * X[s, k, i, e] * duration[s]) <= max_workload[c];

# constraint capping the total amount of weekends worked
subject to max_weekends_constraint {e in E, c in contracts[e]}:
    sum {w in W} Yew[e, w] <= max_weekends[c];

# constraint limiting forbidden consecutive shifts
subject to patterns {e in E, i in {1 .. (p - 1)}, s in S, s2 in follows[s]}:
    sum {k in columns[s]} (lambda[s, k] * X[s, k, i, e]) + sum {k in columns[s2]} (lambda[s, k] * X[s, k, i + 1, e]) <= 1;
