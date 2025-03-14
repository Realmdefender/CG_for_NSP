set E; # set of employees
set S; # set of shift types
param p >= 1;
set P ordered := 1 .. p; # set of days
set W ordered := 1 .. (p / 7); # set of weekends
set C; # set of contracts

param e symbolic in E; # the id of the current employee




# employee-related sets for pre-fixed days off, contracts
set days_off within P;
set contracts within C;

# sets of preferences for shifts and accompanying weights
set shift_on within {P, S};
param on_weight {shift_on[e]};
set shift_off within {P, S};
param off_weight {shift_off[e]};

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
param required {P, S} >= 0;
param over_weight {P, S} >= 0;
param under_weight {P, S} >= 0;



param obj;
param cover_requirement_duals {P, S};
param convexity_constraint_duals {E};




# main assignment variable (starts at 0 for the min_on and min_off constraints)
var X {{0 .. p}, S} binary;

# helper variables for conjunctions
var Yew {w in W} binary;
var Yminon {contracts[e], i in P} binary;
var Yminoff {contracts[e], i in P} binary;

# slack variables for counting violations
var Vover {P, S} integer, >= 0;
var Vunder {P, S} integer, >= 0;
var Von {shift_on[e]} binary;
var Voff {shift_off[e]} binary;




# objective function for to find the minimal reduced cost of any column
minimize reducedd_cost: obj - sum {i in P, s in S} (cover_requirement_duals[i, s] * X[i, s]) - convexity_constraint_duals[e];




# constraints to fix the supporting variables
subject to on_constraint {(i, s) in shift_on[e]}:
    Von[i, s] = 1 - X[i, s];
subject to on_constraint {(i, s) in shift_off[e]}:
    Voff[i, s] = X[i, s];

# constraints setting the value for auxiliary variables Yew
subject to yew1 {w in W, s in S}:
    Yew[w] >= X[7 * w, s];
subject to yew2 {w in W, s in S}:
    Yew[w] >= X[7 * w - 1, s];
subject to yew3 {w in W}:
    Yew[w] <= sum {s in S} (X[7 * w, s] + X[7 * w - 1, s]);

# constraints setting the value for auxiliary variables Yminon
subject to yminon1 {c in contracts[e], i in P}:
    Yminon[c, i] <= 1 - sum {s in S} X[i - 1, s];
subject to yminon2 {c in contracts[e], i in P}:
    Yminon[c, i] <= sum {s in S} X[i, s];
subject to yminon3 {c in contracts[e], i in P}:
    Yminon[c, i] >= sum {s in S} (X[i, s] - X[i - 1, s]);

# constraints setting the value for auxiliary variables Yminoff
subject to yminoff1 {c in contracts[e], i in P}:
    Yminoff[c, i] <= sum {s in S} X[i - 1, s];
subject to yminoff2 {c in contracts[e], i in P}:
    Yminoff[c, i] <= 1 - sum {s in S} X[i, s];
subject to yminoff3 {c in contracts[e], i in P}:
    Yminoff[c, i] >= sum {s in S} (X[i - 1, s] - X[i, s]);

# constraint setting day 0 to be a day off
subject to day_zero {s in S}:
    X[0, s] = 0;

# constraint for at most on shift per day
subject to one_shift_a_day {i in P}:
    sum {s in S} X[i, s] <= 1;

# constraint setting pre-fixed days off
subject to days_off_constraint {i in days_off[e], s in S}:
    X[i, s] = 0;

# constraints limiting the min/max consecutive days on/off
subject to max_on_constraint {c in contracts[e], j in {1 .. (p - max_on[c])}}:
    sum {i in {j .. (j + max_on[c])}, s in S} X[i, s] <= max_on[c];
subject to min_on_constraint {c in contracts[e], j in {1 .. (p - min_on[c])}}:
    Yminon[c, j] * (min_on[c] - 1) - sum {i in {(j + 1) .. (j + min_on[c] - 1)}, s in S} X[i, s] <= 0;
subject to min_off_constraint {c in contracts[e], j in {1 .. (p - min_off[c])}}:
    Yminoff[c, j] * (min_off[c] - 1) - sum {i in {(j + 1) .. (j + min_off[c] - 1)}} (1 - sum {s in S} X[i, s]) <= 0;

# constraint limiting the total workload
subject to workload {c in contracts[e]}:
    min_workload[c] <= sum {i in P, s in S} (X[i, s] * duration[s]) <= max_workload[c];

# constraint capping the total amount of shifts worked
subject to max_shifts_constraint {c in contracts[e], s in S}:
    sum {i in P} X[i, s] <= max_shifts[c, s];

# constraint capping the total amount of weekends worked
subject to max_weekends_constraint {c in contracts[e]}:
    sum {w in W} Yew[w] <= max_weekends[c];

# constraint limiting forbidden consecutive shifts
subject to patterns {i in {1 .. (p - 1)}, s in S, s2 in follows[s]}:
    X[i, s] + X[i + 1, s2] <= 1;
