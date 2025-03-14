import gurobipy as gp
from gurobipy import GRB

# creates the model for a sub-problem for the employee split
# parameters: 
#   inst  = the specific instance information
#   e     = the employee of this sub-problem
#   duals = dual variable values from the master problem
# returns:
#   m     = the model for the restricted master problem

def SP_E(inst, e, duals, branches, flow_control):
    _, duration, follows = gp.multidict(inst.shifts)
    employee = inst.employees[e]

    env = gp.Env(empty=True)
    env.setParam("OutputFlag",0)
    env.start()
    m = gp.Model("sub_problem_employees_" + e, env=env)




    x = m.addVars(inst.P, inst.S, vtype=GRB.BINARY, name="x")

    y_w = m.addVars(inst.W, vtype=GRB.BINARY, name="y_w")
    # y_min_on = m.addVars(inst.P1, vtype=GRB.BINARY, name="y_min_on")
    # y_min_off = m.addVars(inst.P1, vtype=GRB.BINARY, name="y_min_off")

    v_on = m.addVars(inst.shifts_on[e], vtype=GRB.BINARY, name="v_on")
    v_off = m.addVars(inst.shifts_off[e], vtype=GRB.BINARY, name="v_off")




    m.addConstrs((x[i, s] == branches[i, s] for (i, s) in branches), "branch choices")
    m.addConstrs((x.sum(i, '*') <= 1 for i in inst.P), "max_one_shift")
    m.addConstrs((x[i, s] == 0 for i in inst.days_off[e] for s in inst.S), "pre_fixed_days_off")
    m.addConstr(employee[1] <= sum(x[i, s] * duration[s] for i in inst.P for s in inst.S), "min_workload")
    m.addConstr(sum(x[i, s] * duration[s] for i in inst.P for s in inst.S) <= employee[0], "max_workload")
    m.addConstrs((x.sum('*', s) <= employee[6][s] for s in inst.S), "max_shifts")
    m.addConstrs((x[i, s] + x[i + 1, s2] <= 1 for i in range(inst.p - 1) for s in inst.S for s2 in follows[s]), "forbidden_sequences")

    m.addConstrs((y_w[w] >= x.sum(7 * w + i, '*') for w in inst.W for i in [5, 6]), "y_w_1")
    m.addConstrs((y_w[w] <= sum(x[7 * w + i, s] for s in inst.S for i in [5, 6]) for w in inst.W), "y_w_2")
    m.addConstr(y_w.sum() <= employee[5], "max_weekends")

    m.addConstrs((v_on[i, s] == 1 - x[i, s] for (i, s) in inst.shifts_on[e]), "slack_on")
    m.addConstrs((v_off[i, s] == x[i, s] for (i, s) in inst.shifts_off[e]), "slack_off")

    if flow_control:
        w = m.addVars(((a, b) for a in inst.flow_graph[e] for b in inst.flow_graph[e][a]), vtype=GRB.BINARY , name="w")

        m.addConstr(w.sum("source", '*') == 1, "source_flow")
        m.addConstr(w.sum('*', "sink") == 1, "sink_flow")
        m.addConstrs((w.sum(a, '*') == w.sum('*', a) for a in inst.flow_graph[e] if a != "source" and a != "sink"), "conserve_flow")

        m.addConstrs((x.sum(i, '*') == sum(w[j, k] 
                        for j in inst.flow_graph[e] if j == "source"  or (j.split('_')[0] == "on" and int(j.split('_')[1]) <= i and int(j.split('_')[1]) >= i - inst.employees[e][2])
                        for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "off" and int(k.split('_')[1]) > i))
                        for i in inst.P), "days_on")
        m.addConstrs((x.sum(i, '*') == 1 - sum(w[j, k] 
                        for j in inst.flow_graph[e] if j == "source" or (j.split('_')[0] == "off" and int(j.split('_')[1]) <= i)
                        for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "on" and int(k.split('_')[1]) > i))
                        for i in inst.P), "days_off")
        
    else:
        m.addConstrs((x.sum((j for j in range(i, i + employee[2] + 1)), '*') <= employee[2] for i in range(inst.p - employee[2])), "max_consecutive_days_on")

        m.addConstrs((x.sum(i, '*') + (k - x.sum((j for j in range(i + 1, i + k + 1)), '*')) + x.sum(i + k + 1, '*') >= 1
                        for k in range(1, employee[3]) for i in range(inst.p - k - 1)), "min_consecutive_days_on")
        # m.addConstrs((y_min_on[i] <= x.sum(i, '*') for i in inst.P1), "y_min_on_1")
        # m.addConstrs((y_min_on[i] <= 1 - x.sum(i - 1, '*') for i in inst.P1), "y_min_on_2")
        # m.addConstrs((y_min_on[i] >= x.sum(i, '*') - x.sum(i - 1, '*') for i in inst.P1), "y_min_on_3")
        # m.addConstrs((y_min_on[i] * min(employee[3] - 1, inst.p - i - 1) - x.sum((j for j in range(i + 1, min(i + employee[3], inst.p))), '*') <= 0
        #                 for i in inst.P1), "min_consecutive_days_on")


        m.addConstrs(((1 - x.sum(i, '*')) + x.sum((j for j in range(i + 1, i + k + 1)), '*') + (1 - x.sum(i + k + 1, '*')) >= 1
                     for k in range(1, employee[4]) for i in range(inst.p - k - 1)), "min_consecutive_days_off")
        # m.addConstrs((y_min_off[i] <= 1 - x.sum(i, '*') for i in inst.P1), "y_min_off_1")
        # m.addConstrs((y_min_off[i] <= x.sum(i - 1, '*') for i in inst.P1), "y_min_off_2")
        # m.addConstrs((y_min_off[i] >= x.sum(i - 1, '*') - x.sum(i, '*') for i in inst.P1), "y_min_off_3")
        # m.addConstrs((y_min_off[i] * min(employee[4] - 1, inst.p - i - 1) - sum(1 - x.sum(j, '*') for j in range(i + 1, min(i + employee[4], inst.p))) <= 0
        #                 for i in inst.P1), "min_consecutive_days_off")
        



    m.setObjective(sum(v_on[i, s] * inst.shifts_on[e][i, s] for (i, s) in inst.shifts_on[e]) 
                   + sum(v_off[i, s] * inst.shifts_off[e][i, s] for (i, s) in inst.shifts_off[e])
                   - sum(x[i, s] * duals["cover_requirements"][i, s] for i in inst.P for s in inst.S)
                   - duals["convexity"][e]
                   , GRB.MINIMIZE)
    
    m.update()
    return m


def SP_P(inst, i, duals, branches, flow_control):
    _, max_workload, min_workload, max_on, min_on, min_off, max_weekends, max_shifts = gp.multidict(inst.employees)
    _, duration, follows = gp.multidict(inst.shifts)
    _, required, under_weight, over_weight = gp.multidict(inst.requirements)

    env = gp.Env(empty=True)
    env.setParam("OutputFlag",0)
    env.start()
    m = gp.Model("sub_problem_employees_" + str(i), env=env)




    x = m.addVars(inst.S, inst.E, vtype=GRB.BINARY, name="x")

    v_over = m.addVars(inst.S, vtype=GRB.INTEGER, name="v_over")
    v_under = m.addVars(inst.S, vtype=GRB.INTEGER, name="v_under")
    v_on = m.addVars(((s, e) for e in inst.E for (i2, s) in inst.shifts_on[e] if i2 == i), vtype=GRB.BINARY, name="v_on")
    v_off = m.addVars(((s, e) for e in inst.E for (i2, s) in inst.shifts_off[e] if i2 == i), vtype=GRB.BINARY, name="v_off")




    m.addConstrs((x.sum('*', e) <= 1 for e in inst.E), "max_one_shift")
    m.addConstrs((x[s, e] == 0 for e in inst.E if i in inst.days_off[e] for s in inst.S), "pre_fixed_days_off")

    m.addConstrs((x.sum(s, '*') - v_over[s] + v_under[s] == required[i, s] for s in inst.S), "cover_requirements")

    m.addConstrs((v_on[s, e] == 1 - x[s, e] for e in inst.E for (i2, s) in inst.shifts_on[e] if i2 == i), "slack_on")
    m.addConstrs((v_off[s, e] == x[s, e] for e in inst.E for (i2, s) in inst.shifts_off[e] if i2 == i), "slack_off")

    # if flow_control:
    #     w = m.addVars(((e, a, b) for e in inst.E for a in inst.flow_graph[e] for b in inst.flow_graph[e][a]), vtype=GRB.BINARY , name="w")

    #     m.addConstrs((w.sum(e, "source", '*') == 1 for e in inst.E), "source_flow")
    #     m.addConstrs((w.sum(e, '*', "sink") == 1 for e in inst.E), "sink_flow")
    #     m.addConstrs((w.sum(e, a, '*') == w.sum(e, '*', a) for e in inst.E for a in inst.flow_graph[e] if a != "source" and a != "sink"), "conserve_flow")

    #     m.addConstrs((x.sum('*', e) == sum(w[e, j, k] 
    #                     for j in inst.flow_graph[e] if j == "source"  or (j.split('_')[0] == "on" and int(j.split('_')[1]) <= i and int(j.split('_')[1]) >= i - inst.employees[e][2])
    #                     for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "off" and int(k.split('_')[1]) > i))
    #                     for e in inst.E), "days_on")
    #     m.addConstrs((x.sum('*', e) == 1 - sum(w[e, j, k] 
    #                     for j in inst.flow_graph[e] if j == "source" or (j.split('_')[0] == "off" and int(j.split('_')[1]) <= i)
    #                     for k in inst.flow_graph[e][j] if k == "sink" or (k.split('_')[0] == "on" and int(k.split('_')[1]) > i))
    #                     for e in inst.E), "days_off")




    m.setObjective(sum(v_on[s, e] * inst.shifts_on[e][i, s] for e in inst.E for (i2, s) in inst.shifts_on[e] if i2 == i) 
                   + sum(v_off[s, e] * inst.shifts_off[e][i, s] for e in inst.E for (i2, s) in inst.shifts_off[e] if i2 == i)
                #    - sum(duals["min_workload"][e] * sum(x[s, e] * duration[s]  for s in inst.S) for e in inst.E)
                #    - sum(duals["max_workload"][e] * sum(x[s, e] * duration[s]  for s in inst.S) for e in inst.E)
                #    - sum(duals["max_shifts"][s, e] * x[s, e] for s in inst.S for e in inst.E)
                #    - sum(duals["forbidden_sequences"][i, s, s2, e] * (x[s, e] + x[s2, e]) for s in inst.S for s2 in follows[s] for e in inst.E)
                #    - sum(duals["y_we_1"][w, e, i2] * sum(x[s, e] for s in inst.S) for w in inst.W for e in inst.E for i2 in [5, 6] if 7 * w + i2 == i)
                #    - sum(duals["y_we_2"][w, e] * sum(x[s, e] for s in inst.S) for w in inst.W for e in inst.E if i % 7 == 5 or i % 7 == 6)
                #    - sum(duals["max_consecutive_days_on"][e, i2] * sum(x[s, e] for s in inst.S) for e in inst.E for i2 in range(inst.p - max_on[e]) if i in [j for j in range(i2, i2 + max_on[e] + 1)])
                #    - sum(duals["min_consecutive_days_on"][e, i2] * sum(x[s, e] for s in inst.S) for e in inst.E for i2 in inst.P1 if i in [j for j in range(i2 + 1, min(i2 + min_on[e], inst.p))])
                #    - sum(duals["min_consecutive_days_off"][e. i2] * sum(x[s, e] for s in inst.S) for e in inst.E for ie in inst.P1 if i in [j for j in range(i + 1, min(i + min_off[e], inst.p))]) 
                #    - duality"][i]
                   , GRB.MINIMIZE)
    
    m.update()
    return m
