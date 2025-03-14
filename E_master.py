import gurobipy as gp
from gurobipy import GRB

# creates the model for the restricted master problem for the employee split
# parameters: 
#   inst    = the specific instance information
#   columns = list of columns for each employee in a dictionary
#       column: (x[i, s], v_on, v_off, infeasible_weight)
# returns:
#   m       = the model for the restricted master problem
def RMP_E(inst, strong_branch, choice):
    columns = inst.current_node[0]
    _, required, under_weight, over_weight = gp.multidict(inst.requirements)

    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()
    m = gp.Model("restricted_master_problem_employees", env=env)

    

    
    lam = m.addVars(((e, k) for e in columns for k in range(len(columns[e]))), ub=1, name="lambda")

    v_over = m.addVars(inst.P, inst.S, name="v_over")
    v_under = m.addVars(inst.P, inst.S, name="v_under")




    m.addConstrs((sum(lam[e, k] * columns[e][k][0][i, inst.S[s]] for e in columns for k in range(len(columns[e]))) - v_over[i, s] + v_under[i, s] == required[i, s] 
                  for i in inst.P for s in inst.S), "cover_requirements")
    m.addConstrs((lam.sum(e, '*') == 1 for e in columns), "convexity")

    if (strong_branch is not None):
        m.addConstrs(lam[strong_branch[2], k] == 0 
                     for k in range(len(columns[strong_branch[2]])) if columns[strong_branch[2]][k][0][strong_branch[0], inst.S[strong_branch[1]]] != choice)




    m.setObjective(sum(lam[e, k] * (sum((1 - columns[e][k][0][i, inst.S[s]]) * inst.shifts_on[e][i, s] for (i, s) in inst.shifts_on[e])
                                    + sum((columns[e][k][0][i, inst.S[s]]) * inst.shifts_off[e][i, s] for (i, s) in inst.shifts_off[e])
                                    + inst.infeasible_penalty * columns[e][k][1]) for e in columns for k in range(len(columns[e]))) 
                   + sum(v_under[i, s] * under_weight[i, s] + v_over[i, s] * over_weight[i, s] for i in inst.P for s in inst.S),
                   GRB.MINIMIZE)

    m.update()
    return m


# creates the model for the restricted master problem for the planning period split
# parameters: 
#   inst    = the specific instance information
#   columns = list of columns for each day in a dictionary
#       column: (x[s, e], infeasible_weight)
# returns:
#   m       = the model for the restricted master problem
def RMP_P(inst, strong_branch, choice):
    columns = inst.current_node[0]
    _, max_workload, min_workload, max_on, min_on, min_off, max_weekends, max_shifts = gp.multidict(inst.employees)
    _, duration, follows = gp.multidict(inst.shifts)

    env = gp.Env(empty=True)
    env.setParam("OutputFlag",0)
    env.start()
    m = gp.Model("restricted_master_problem_planning_horizon")

    
    
    
    lam = m.addVars(((i, k) for i in columns for k in range(len(columns[i]))), ub=1, name="lambda")

    y_we = m.addVars(inst.W, inst.E, ub=1, name="y_we")




    m.addConstrs((min_workload[e] <= sum(duration[s] * sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for i in columns for k in range(len(columns[i]))) for s in inst.S) 
                  for e in inst.E), "min_workload")
    m.addConstrs((sum(duration[s] * sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for i in columns for k in range(len(columns[i]))) for s in inst.S) <= max_workload[e] 
                  for e in inst.E), "max_workload")
    m.addConstrs((sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for i in columns for k in range(len(columns[i]))) <= max_shifts[e][s] 
                  for s in inst.S for e in inst.E), "max_shifts")
    m.addConstrs((sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i]))) + 
                  sum(lam[i + 1, k] * columns[i + 1][k][0][inst.S[s2], inst.E[e]] for k in range(len(columns[i + 1]))) <= 1 
                  for i in inst.P1 for s in inst.S for s2 in follows[s] for e in inst.E), "forbidden_sequences")
    
    m.addConstrs((y_we[w, e] >= sum(lam[7 * w + i, k] * columns[7 * w + i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[7 * w + i])) for s in inst.S)
                   for w in inst.W for e in inst.E for i in [5, 6]), "y_we_1")
    m.addConstrs((y_we[w, e] <= sum(lam[7 * w + i, k] * columns[7 * w + i][k][0][inst.S[s], inst.E[e]] for i in [5, 6] for k in range(len(columns[7 * w + i])) for s in inst.S)
                   for w in inst.W for e in inst.E), "y_we_2")
    m.addConstrs((y_we.sum('*', e) <= max_weekends[e] for e in inst.E), "max_weekends")


    m.addConstrs((sum(lam[j, k] * columns[j][k][0][inst.S[s], inst.E[e]] for j in range(i, i + max_on[e] + 1) for k in range(len(columns[j])) for s in inst.S) <= max_on[e]
                    for e in inst.E for i in range(inst.p - max_on[e])), "max_consecutive_days_on")
    
    
    m.addConstrs((sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i])) for s in inst.S) + 
                  (a - sum(lam[j, k] * columns[j][k][0][inst.S[s], inst.E[e]] for j in range(i + 1, i + a + 1) for k in range(len(columns[j])) for s in inst.S)) +
                  sum(lam[i + a + 1, k] * columns[i + a + 1][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i + a + 1])) for s in inst.S) >= 1
                  for e in inst.E for a in range(1, min_on[e]) for i in range(inst.p - a - 1)), "min_consecutive_days_on")

    m.addConstrs(((1 - sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i])) for s in inst.S)) +
                 sum(lam[j, k] * columns[j][k][0][inst.S[s], inst.E[e]] for j in range(i + 1, i + a + 1) for k in range(len(columns[j])) for s in inst.S) +
                 (1 - sum(lam[i + a + 1, k] * columns[i + a + 1][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i + a + 1])) for s in inst.S)) >= 1
                 for e in inst.E for a in range(1, min_off[e]) for i in range(inst.p - a - 1)), "min_consecutive_days_off")

    m.addConstrs((lam.sum(i, '*') == 1 for i in columns), "convexity")
    

    

    m.setObjective(sum((1 - sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i])))) * inst.shifts_on[e][i, s] for e in inst.E for (i, s) in inst.shifts_on[e]) 
                        + sum(sum(lam[i, k] * columns[i][k][0][inst.S[s], inst.E[e]] for k in range(len(columns[i]))) * inst.shifts_off[e][i, s] for e in inst.E for (i, s) in inst.shifts_off[e])
                        + sum(lam[i, k] * (columns[i][k][1][0] + columns[i][k][1][0]) for i in columns for k in range(len(columns[i]))),
                        GRB.MINIMIZE)

    m.update()
    return m


