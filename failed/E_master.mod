set E; # set of employees
set S; # set of shift types
param p >= 1;
set P ordered := 1 .. p; # set of days

# sets of preferences for shifts and accompanying weights
set shift_on {E} within {P, S};
param on_weight {e in E, shift_on[e]};
set shift_off {E} within {P, S};
param off_weight {e in E, shift_off[e]};

# demands by the empployer as well as weights for violations
param required {P, S} >= 0;
param over_weight {P, S} >= 0;
param under_weight {P, S} >= 0;




set columns {E}; # set of columns for each employee

# assignment values selected for each column
param X {e in E, columns[e], {0 .. p}, S} binary;
param Von {e in E, columns[e], shift_on[e]} binary;
param Voff {e in E, columns[e], shift_off[e]} binary;




# main variable for column selection
var lambda {e in E, columns[e]} >= 0;

# slack variables for counting violations
var Vover {P, S} integer, >= 0;
var Vunder {P, S} integer, >= 0;




# main objective function counting all violations multiplied by the corresponding weights
minimize satisfaction: sum {e in E, k in columns[e], (i, s) in shift_on[e]} (lambda[e, k] * Von[e, k, i, s] * on_weight[e, i, s])
    + sum {e in E, k in columns[e], (i, s) in shift_off[e]} (lambda[e, k] * Voff[e, k, i, s] * off_weight[e, i, s])
    + sum {i in P, s in S} (Vunder[i, s] * under_weight[i, s] + Vover[i, s] * over_weight[i, s]);




# convexity constraint for the columns of each employee
subject to convexity_constraint {e in E}:
    sum {k in columns[e]} lambda[e, k] = 1;

# constraint for the cover requirements for each shift on each day
subject to cover_requirement {i in P, s in S}:
    sum {e in E, k in columns[e]} (lambda[e, k] * X[e, k, i, s]) - Vover[i, s] + Vunder[i, s] = required[i, s];
