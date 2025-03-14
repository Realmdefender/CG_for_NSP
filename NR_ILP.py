import gurobipy as gp
from gurobipy import GRB

# creates the integer linear programming model for a specific instance
# parameters: 
#   inst         = the specific instance information
#   mins         = upper bound on the available time to solve the instance (in minutes)
#   relaxed      = boolean variable indicating if the relaxed version of the model is returned
#   feasible     = turns the problem from an optimisation to a feasibility problem, to obtain a quick first result
#   flow_control = uses the flow control model for sequence constraints
# returns:
#   m            = the finished ILP model
def ILP(inst, time, relaxed, feasible, flow_control, non):
    _, max_workload, min_workload, max_on, min_on, min_off, max_weekends, max_shifts = gp.multidict(inst.employees)
    _, duration, follows = gp.multidict(inst.shifts)
    _, required, under_weight, over_weight = gp.multidict(inst.requirements)

    # model setup
    m = gp.Model("schedule")
    m.setParam("TimeLimit", time)



    # variables
    x = m.addVars(inst.P, inst.S, inst.E, vtype=GRB.BINARY, name="x")
    y_we = m.addVars(inst.W, inst.E, vtype=GRB.BINARY, name="y_we")

    v_over = m.addVars(inst.P, inst.S, vtype=GRB.INTEGER, name="v_over")
    v_under = m.addVars(inst.P, inst.S, vtype=GRB.INTEGER, name="v_under")
    v_on = m.addVars(((i, s, e) for e in inst.E for (i, s) in inst.shifts_on[e]), vtype=GRB.BINARY, name="v_on")
    v_off = m.addVars(((i, s, e) for e in inst.E for (i, s) in inst.shifts_off[e]), vtype=GRB.BINARY, name="v_off")

    # constraints
    if non != 0:
        m.addConstrs((x.sum(i, '*', e) <= 1 for e in inst.E for i in inst.P), "max_one_shift")
    if non != 1:
        m.addConstrs((x[i, s, e] == 0 for e in inst.E for i in inst.days_off[e] for s in inst.S), "pre_fixed_days_off")
    if non != 2:
        m.addConstrs((min_workload[e] <= sum(x[i, s, e] * duration[s] for i in inst.P for s in inst.S) for e in inst.E), "min_workload")
    if non != 3:
        m.addConstrs((sum(x[i, s, e] * duration[s] for i in inst.P for s in inst.S) <= max_workload[e] for e in inst.E), "max_workload")
    if non != 4:
        m.addConstrs((x.sum('*', s, e) <= max_shifts[e][s] for e in inst.E for s in inst.S), "max_shifts")
    if non != 5:
        m.addConstrs((x[i, s, e] + x[i + 1, s2, e] <= 1 for i in inst.P1 for s in inst.S for s2 in follows[s] for e in inst.E), "forbidden_sequences")

    if non != 6:
        m.addConstrs((y_we[w, e] >= x.sum(7 * w + i, '*', e) for w in inst.W for e in inst.E for i in [5, 6]), "y_we_1")
        m.addConstrs((y_we[w, e] <= sum(x[7 * w + i, s, e] for s in inst.S for i in [5, 6]) for w in inst.W for e in inst.E), "y_we_2")
        m.addConstrs((y_we.sum('*', e) <= max_weekends[e] for e in inst.E), "max_weekends")

    if non != 7:
        m.addConstrs((x.sum(i, s, '*') - v_over[i, s] + v_under[i, s] == required[i, s] for i in inst.P for s in inst.S), "cover_requirements")

    m.addConstrs((v_on[i, s, e] == 1 - x[i, s, e] for e in inst.E for (i, s) in inst.shifts_on[e]), "slack_on")
    m.addConstrs((v_off[i, s, e] == x[i, s, e] for e in inst.E for (i, s) in inst.shifts_off[e]), "slack_off")

    if flow_control:
        g = m.addVars(((e, a, b) for e in inst.E for a in inst.flow_graph[e] for b in inst.flow_graph[e][a]), vtype=GRB.BINARY , name="w")

        m.addConstrs((g.sum(e, "source", '*') == 1 for e in inst.E), "source_flow")
        m.addConstrs((g.sum(e, '*', "sink") == 1 for e in inst.E), "sink_flow")
        m.addConstrs((g.sum(e, a, '*') == g.sum(e, '*', a) for e in inst.E for a in inst.flow_graph[e] if a != "source" and a != "sink"), "conserve_flow")

        m.addConstrs((x.sum(i, '*', e) == sum(g[e, j, k] 
                        for j in inst.flow_graph[e] if j == "source"  or (j.split('_')[0] == "on" and int(j.split('_')[1]) <= i and int(j.split('_')[1]) >= i - inst.employees[e][2])
                        for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "off" and int(k.split('_')[1]) > i))
                        for i in inst.P for e in inst.E), "days_on")
        m.addConstrs((x.sum(i, '*', e) == 1 - sum(g[e, j, k] 
                        for j in inst.flow_graph[e] if j == "source" or (j.split('_')[0] == "off" and int(j.split('_')[1]) <= i)
                        for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "on" and int(k.split('_')[1]) > i))
                        for i in inst.P for e in inst.E), "days_off")
        
    else:
        if non != 8:
            m.addConstrs((x.sum((j for j in range(i, i + max_on[e] + 1)), '*', e) <= max_on[e] for e in inst.E for i in range(inst.p - max_on[e])), "max_consecutive_days_on")
        
        if non != 9:
            m.addConstrs((x.sum(i, '*', e) + (k - x.sum((j for j in range(i + 1, i + k + 1)), '*', e)) + x.sum(i + k + 1, '*', e) >= 1
                     for e in inst.E for k in range(1, min_on[e]) for i in range(inst.p - k - 1)), "min_consecutive_days_on")
        
        if non != 10:
            m.addConstrs(((1 - x.sum(i, '*', e)) + x.sum((j for j in range(i + 1, i + k + 1)), '*', e) + (1 - x.sum(i + k + 1, '*', e)) >= 1
                     for e in inst.E for k in range(1, min_off[e]) for i in range(inst.p - k - 1)), "min_consecutive_days_off")
            



    # feasibility vs optimization problem
    if feasible:
        sol = m.addVar(name="sol")
        m.addConstr(sol == sum(v_on[i, s, e] * inst.shifts_on[e][i, s] for e in inst.E for (i, s) in inst.shifts_on[e]) 
                        + sum(v_off[i, s, e] * inst.shifts_off[e][i, s] for e in inst.E for (i, s) in inst.shifts_off[e])
                        + sum(v_under[i, s] * under_weight[i, s] + v_over[i, s] * over_weight[i, s] for i in inst.P for s in inst.S), "sol_value")

    else:
        m.setObjective(sum(v_on[i, s, e] * inst.shifts_on[e][i, s] for e in inst.E for (i, s) in inst.shifts_on[e]) 
                        + sum(v_off[i, s, e] * inst.shifts_off[e][i, s] for e in inst.E for (i, s) in inst.shifts_off[e]) 
                        + sum(v_under[i, s] * under_weight[i, s] + v_over[i, s] * over_weight[i, s] for i in inst.P for s in inst.S),
                        GRB.MINIMIZE)
    
    m.update()
    if relaxed:
        return m.relax
    return m



