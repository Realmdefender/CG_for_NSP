 # def solve_instance(self, choice, minutes, flow_control):
    #     start = time.time()

    #     # obtain an initial feaible solution by solving the ILP as a feasibility problem
    #     feasible = ILP(self, minutes, False, True, True, -1)
    #     feasible.optimize()

    #     if(feasible.Status != 2):
    #         end = time.time()
    #         return float('inf'), end - start, 0, 0, 0

    #     assignments = np.zeros((self.p, len(self.S), len(self.E)))
    #     for v in feasible.getVars():
    #         data = v.VarName[:-1].split('[')
    #         if (len(data) <= 1):
    #             continue
    #         indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]
    #         if (data[0] == "x"):
    #             assignments[indices[0], self.S[indices[1]], self.E[indices[2]]] = v.X

    #     ub = feasible.getVarByName("sol").X

    #     end = time.time()
    #     if (end - start > 60 * minutes):
    #         return ub, (end - start), 0, 0, 0
        

    #     # create an initial set of columns
    #     # initial_columns = self.generate_initial()
    #     columns = {}
    #     branches = {}

    #     if (choice == 'E'):
    #         for e in self.E:
    #             assignment = assignments[:, :, self.E[e]]
    #             columns[e] = [self.check_column_E(e, assignment)]
    #             branches[e] = {}

    #     elif(choice == 'P'):
    #         for i in self.P:
    #             assignment = assignments[i, :, :]
    #             columns[i] = [self.check_column_P(i, assignment)]
    #             branches[i] = {}


    #     # ub = float('inf')
    #     nodes_to_explore = [(columns, branches, 0)]
    #     total_nodes = 0
    #     cycles = []

    #     # go over all nodes using a set selection strategy
    #     while (len(nodes_to_explore) > 0):
    #         end = time.time()
    #         if (end - start > minutes * 60):
    #             break

    #         # solve the current node
    #         node = nodes_to_explore.pop(0)
    #         total_nodes += 1

    #         if(node[2] > ub):
    #             continue
    #         elif (choice == 'E'):
    #             bound, new_nodes, integral, cycle = self.solve_node_E(node[0], node[1], ub, flow_control)
    #         elif (choice == 'P'):
    #             bound, new_nodes, integral = self.solve_node_P(node[0], node[1], ub, flow_control)

    #         if (integral and bound < ub):
    #             ub = bound

    #         nodes_to_explore  = new_nodes + nodes_to_explore
    #         cycles.append(cycle)
    #         # nodes_to_explore.sort(key=lambda tup: tup[2])

    #     cycle_res = 0
    #     max_cycles = 0
    #     if (len(cycles) > 0):
    #         cycle_res = sum(cycles) / len(cycles)
    #         max_cycles = max(cycles)          
    #     return ub, (end - start), total_nodes, cycle_res, max_cycles









    # def solve_node_E(self, columns, branches, ub, flow_control):

    #     epsilon = 0.00001
    #     sub_not_used = {}
    #     for e in self.E:
    #         sub_not_used[e] = 0

    #     optimal = False
    #     cycles = 0
    #     while (not optimal):
    #         cycles += 1

    #         # create and run the restricted master problem
    #         restricted_master_problem = RMP_E(self, columns)
    #         restricted_master_problem.optimize()

    #         # extract dual variable values from the master problem
    #         duals = {}
    #         name = ""
            
    #         for c in restricted_master_problem.getConstrs():
    #             data = c.ConstrName[:-1].split('[')
    #             indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

    #             if (data[0] != name):
    #                 name = data[0]
    #                 duals[name] = {}

    #             if (len(indices) > 1):
    #                 duals[name][tuple(indices)] = c.Pi
    #             else:
    #                 duals[name][indices[0]] = c.Pi


    #         # create sub-problems for each employee and add columns if necessary
    #         sub_results = Parallel(n_jobs=-1)(
    #             delayed(self.solve_sub_E)(e, duals, branches[e], epsilon, flow_control) for e in self.E
    #         )

    #         counter = 0
    #         for sub_result in sub_results:
    #             if (sub_result is None):
    #                 counter += 1
    #             else:
    #                 columns[sub_result[0]].append(sub_result[1])

    #         if (counter == len(self.E)):
    #             optimal = True

            
    #         # counter = 0
    #         # for e in self.E:
    #         #     sub_problem = SP_E(self, e, duals, branches[e], flow_control)
    #         #     sub_problem.optimize()

    #         #     if (sub_problem.Status == 3):
    #         #         counter += 1
    #         #         continue

    #         #     # add the column if a negative reduced cost has been obtained
    #         #     if (sub_problem.ObjVal < 0 - epsilon):
    #         #         sub_not_used[e] = 0
    #         #         x = np.empty((self.p, len(self.S)))
    #         #         on_val = 0
    #         #         off_val = 0

    #         #         for v in sub_problem.getVars():
    #         #             data = v.VarName[:-1].split('[')
    #         #             indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

    #         #             if (data[0] == "x"):
    #         #                 x[indices[0], self.S[indices[1]]] = v.X

    #         #             elif (data[0] == "v_on"):
    #         #                 on_val += v.X * self.shifts_on[e][indices[0], indices[1]]

    #         #             elif (data[0] == "v_off"):
    #         #                 off_val += v.X * self.shifts_off[e][indices[0], indices[1]]
                            
    #         #         # feasible_weight always set to 0 as any new column is by definition feasible
    #         #         columns[e].append((x, on_val, off_val, 0))
                
    #         #     else:
    #         #         counter += 1
    #         #         sub_not_used[e] += 1

    #         # exit the column generation loop if the optimal solution is found
    #         # if (counter == len(self.E)):
    #         #     optimal = True


    #     # no branching needed if no feasible solution is found
    #     if (restricted_master_problem.Status == 3):
    #         print("Branch pruned due to infeasibility")
    #         return -1, [], False, cycles
        

    #     # retrieve all lambda variable values from the restricted master problem and check for integrality
    #     objective = restricted_master_problem.ObjVal
    #     lambdas = {}
    #     for e in self.E:
    #         lambdas[e] = {}
    #     integral = True

    #     for v in restricted_master_problem.getVars():
    #         data = v.VarName[:-1].split('[')
    #         indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

    #         if (data[0] == "lambda"):
    #             lambdas[indices[0]][indices[1]] = v.X
                
    #             if (v.X > epsilon and v.X < 1 - epsilon):
    #                 integral = False


    #     # if the optimal solution is integer, return it
    #     if (integral):
    #         print("Integer solution found: " + str(objective))
    #         return objective, [], True, cycles
        
    #     # if the optimal solution is orse than the upper bound, prune
    #     if (objective >= ub):
    #         return objective, [], False, cycles


    #     # choose an original problem variable to branche upon (0/1, most fractional)
    #     chosen = None
    #     chosen_val = 1
    #     for e in self.E:
    #         for i in self.P:
    #             for s in self.S:
                    
    #                 val = 0
    #                 for l in lambdas[e]:
    #                     val += lambdas[e][l] * columns[e][l][0][i, self.S[s]]
    #                 val = abs(0.5 - val)

    #                 if (val < chosen_val):
    #                     chosen_val = val
    #                     chosen = ((i, s), e)


    #     # create new nodes based on the chosen variable
    #     nodes = []

    #     for b in range(2):
    #         branches_b = copy.deepcopy(branches)
    #         branches_b[chosen[1]][chosen[0]] = b

    #         columns_b = copy.deepcopy(columns)
    #         columns_b[chosen[1]] = [c for c in columns_b[chosen[1]] if c[0][chosen[0][0], self.S[chosen[0][1]]] == branches_b[chosen[1]][chosen[0]]]
    #         if (len(columns_b[chosen[1]]) == 0):
    #             x = np.zeros((self.p, len(self.S)))
    #             for (i, s) in branches_b[chosen[1]]:
    #                 x[i][self.S[s]] = branches_b[chosen[1]][i, s]
    #             columns_b[chosen[1]].append(self.check_column_E(chosen[1], x))

    #         nodes.append((columns_b, branches_b, objective))
    #     return objective, nodes, False, cycles









    # def solve_sub_E(self, e, duals, branches, epsilon, flow_control):

    #     sub_problem = SP_E(self, e, duals, branches, flow_control)
    #     sub_problem.optimize()

    #     if (sub_problem.Status == 3 or sub_problem.ObjVal >= 0 - epsilon):
    #         return None
        
    #     else:
    #         x = np.empty((self.p, len(self.S)))
    #         on_val = 0
    #         off_val = 0

    #         for v in sub_problem.getVars():
    #             data = v.VarName[:-1].split('[')
    #             indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

    #             if (data[0] == "x"):
    #                 x[indices[0], self.S[indices[1]]] = v.X

    #             elif (data[0] == "v_on"):
    #                 on_val += v.X * self.shifts_on[e][indices[0], indices[1]]

    #             elif (data[0] == "v_off"):
    #                 off_val += v.X * self.shifts_off[e][indices[0], indices[1]]
    #         return (e, (x, on_val, off_val, 0))
        











    # def solve_sub_E(self, e, duals, branches, epsilon, flow_control):

    #     sub_problem = SP_E(self, e, duals, branches, flow_control)
    #     sub_problem.optimize()

    #     if (sub_problem.Status == 3 or sub_problem.ObjVal >= 0 - epsilon):
    #         return None
        
    #     else:
    #         x = np.empty((self.p, len(self.S)))
    #         on_val = 0
    #         off_val = 0

    #         for v in sub_problem.getVars():
    #             data = v.VarName[:-1].split('[')
    #             indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

    #             if (data[0] == "x"):
    #                 x[indices[0], self.S[indices[1]]] = v.X

    #             elif (data[0] == "v_on"):
    #                 on_val += v.X * self.shifts_on[e][indices[0], indices[1]]

    #             elif (data[0] == "v_off"):
    #                 off_val += v.X * self.shifts_off[e][indices[0], indices[1]]
    #         return (e, (x, on_val, off_val, 0))
        

    # def solve_node_P(self, columns, branches, ub, flow_control):
        # value set to avoid rounding errors
        # epsilon = 0.00001

        # optimal = False
        # cycles = 0
        # while (not optimal):


        #     # create and run the restricted master problem
        #     restricted_master_problem = RMP_P(self, columns)
        #     restricted_master_problem.optimize()


        #     # extract dual variable values from the master problem
        #     duals = {}
        #     name = ""
            
        #     for c in restricted_master_problem.getConstrs():
        #         data = c.ConstrName[:-1].split('[')
        #         indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #         if (data[0] != name):
        #             name = data[0]
        #             duals[name] = {}

        #         if (len(indices) > 1):
        #             duals[name][tuple(indices)] = c.Pi
        #         else:
        #             duals[name][indices[0]] = c.Pi


        #     # create sub-problems for each day and add columns if necessary
        #     counter = 0
        #     for i in self.P:
        #         sub_problem = SP_P(self, i, duals, branches[i], flow_control)
        #         sub_problem.optimize()

        #         if (sub_problem.Status == 3):
        #             counter += 1
        #             continue

        #         # add the column if a negative reduced cost has been obtained
        #         if (sub_problem.ObjVal < 0 - epsilon):
        #             x = np.empty((len(self.S), len(self.E)))
        #             over_val = 0
        #             under_val = 0

        #             for v in sub_problem.getVars():
        #                 data = v.VarName[:-1].split('[')
        #                 indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #                 if (data[0] == "x"):
        #                     x[self.S[indices[0]], self.E[indices[1]]] = v.X

        #                 elif (data[0] == "v_over"):
        #                     over_val += v.X * self.requirements[i, indices[0]][2]

        #                 elif (data[0] == "v_under"):
        #                     under_val += v.X * self.requirements[i, indices[0]][1]
                            
        #             # feasible_weight always set to 0 as any new column is by definition feasible
        #             columns[i].append((x, under_val, over_val, 0))
                
        #         else:
        #             counter += 1
        #         print(sub_problem.ObjVal)

        #     print(counter, self.P)
        #     # exit the column generation loop if the optimal solution is found
        #     if (counter == self.p):
        #         optimal = True
        # return


        # # no branching needed if no feasible solution is found
        # if (restricted_master_problem.Status == 3):
        #     print("Branch pruned due to infeasibility")
        #     return -1, [], False
        

        # # retrieve all lambda variable values from the restricted master problem and check for integrality
        # objective = restricted_master_problem.ObjVal
        # lambdas = {}
        # for e in self.E:
        #     lambdas[e] = {}
        # integral = True

        # for v in restricted_master_problem.getVars():
        #     data = v.VarName[:-1].split('[')
        #     indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #     if (data[0] == "lambda"):
        #         lambdas[indices[0]][indices[1]] = v.X
                
        #         if (v.X > epsilon and v.X < 1 - epsilon):
        #             integral = False

        # # if the optimal solution is integer, return it
        # if (integral):
        #     print("Integer solution found: " + str(objective))
        #     return objective, [], True
        
        # # if the optimal solution is orse than the upper bound, prune
        # if (objective >= ub):
        #     return objective, [], False

        # # choose an original problem variable to branche upon (0/1, most fractional)
        # chosen = None
        # chosen_val = 1
        # for e in self.E:
        #     for i in self.P:
        #         for s in self.S:
                    
        #             val = 0
        #             for l in lambdas[e]:
        #                 val += lambdas[e][l] * columns[e][l][0][i, self.S[s]]
        #             val = abs(0.5 - val)

        #             if (val < chosen_val):
        #                 chosen_val = val
        #                 chosen = ((i, s), e)

        # # create new nodes based on the chosen variable
        # nodes = []

        # for b in range(2):
        #     branches_b = copy.deepcopy(branches)
        #     branches_b[chosen[1]][chosen[0]] = b

        #     columns_b = copy.deepcopy(columns)
        #     columns_b[chosen[1]] = [c for c in columns_b[chosen[1]] if c[0][chosen[0][0], self.S[chosen[0][1]]] == branches_b[chosen[1]][chosen[0]]]
        #     if (len(columns_b[chosen[1]]) == 0):
        #         x = np.zeros((self.p, len(self.S)))
        #         for (i, s) in branches_b[chosen[1]]:
        #             x[i][self.S[s]] = branches_b[chosen[1]][i, s]
        #         columns_b[chosen[1]].append(self.check_column_E(chosen[1], x))

        #     nodes.append((columns_b, branches_b, objective))
        
        # return objective, nodes, False
    
    # def solve_node_P(self, columns, branches, ub, flow_control):
        # value set to avoid rounding errors
        # epsilon = 0.00001

        # optimal = False
        # cycles = 0
        # while (not optimal):


        #     # create and run the restricted master problem
        #     restricted_master_problem = RMP_P(self, columns)
        #     restricted_master_problem.optimize()


        #     # extract dual variable values from the master problem
        #     duals = {}
        #     name = ""
            
        #     for c in restricted_master_problem.getConstrs():
        #         data = c.ConstrName[:-1].split('[')
        #         indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #         if (data[0] != name):
        #             name = data[0]
        #             duals[name] = {}

        #         if (len(indices) > 1):
        #             duals[name][tuple(indices)] = c.Pi
        #         else:
        #             duals[name][indices[0]] = c.Pi


        #     # create sub-problems for each day and add columns if necessary
        #     counter = 0
        #     for i in self.P:
        #         sub_problem = SP_P(self, i, duals, branches[i], flow_control)
        #         sub_problem.optimize()

        #         if (sub_problem.Status == 3):
        #             counter += 1
        #             continue

        #         # add the column if a negative reduced cost has been obtained
        #         if (sub_problem.ObjVal < 0 - epsilon):
        #             x = np.empty((len(self.S), len(self.E)))
        #             over_val = 0
        #             under_val = 0

        #             for v in sub_problem.getVars():
        #                 data = v.VarName[:-1].split('[')
        #                 indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #                 if (data[0] == "x"):
        #                     x[self.S[indices[0]], self.E[indices[1]]] = v.X

        #                 elif (data[0] == "v_over"):
        #                     over_val += v.X * self.requirements[i, indices[0]][2]

        #                 elif (data[0] == "v_under"):
        #                     under_val += v.X * self.requirements[i, indices[0]][1]
                            
        #             # feasible_weight always set to 0 as any new column is by definition feasible
        #             columns[i].append((x, under_val, over_val, 0))
                
        #         else:
        #             counter += 1
        #         print(sub_problem.ObjVal)

        #     print(counter, self.P)
        #     # exit the column generation loop if the optimal solution is found
        #     if (counter == self.p):
        #         optimal = True
        # return


        # # no branching needed if no feasible solution is found
        # if (restricted_master_problem.Status == 3):
        #     print("Branch pruned due to infeasibility")
        #     return -1, [], False
        

        # # retrieve all lambda variable values from the restricted master problem and check for integrality
        # objective = restricted_master_problem.ObjVal
        # lambdas = {}
        # for e in self.E:
        #     lambdas[e] = {}
        # integral = True

        # for v in restricted_master_problem.getVars():
        #     data = v.VarName[:-1].split('[')
        #     indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

        #     if (data[0] == "lambda"):
        #         lambdas[indices[0]][indices[1]] = v.X
                
        #         if (v.X > epsilon and v.X < 1 - epsilon):
        #             integral = False

        # # if the optimal solution is integer, return it
        # if (integral):
        #     print("Integer solution found: " + str(objective))
        #     return objective, [], True
        
        # # if the optimal solution is orse than the upper bound, prune
        # if (objective >= ub):
        #     return objective, [], False

        # # choose an original problem variable to branche upon (0/1, most fractional)
        # chosen = None
        # chosen_val = 1
        # for e in self.E:
        #     for i in self.P:
        #         for s in self.S:
                    
        #             val = 0
        #             for l in lambdas[e]:
        #                 val += lambdas[e][l] * columns[e][l][0][i, self.S[s]]
        #             val = abs(0.5 - val)

        #             if (val < chosen_val):
        #                 chosen_val = val
        #                 chosen = ((i, s), e)

        # # create new nodes based on the chosen variable
        # nodes = []

        # for b in range(2):
        #     branches_b = copy.deepcopy(branches)
        #     branches_b[chosen[1]][chosen[0]] = b

        #     columns_b = copy.deepcopy(columns)
        #     columns_b[chosen[1]] = [c for c in columns_b[chosen[1]] if c[0][chosen[0][0], self.S[chosen[0][1]]] == branches_b[chosen[1]][chosen[0]]]
        #     if (len(columns_b[chosen[1]]) == 0):
        #         x = np.zeros((self.p, len(self.S)))
        #         for (i, s) in branches_b[chosen[1]]:
        #             x[i][self.S[s]] = branches_b[chosen[1]][i, s]
        #         columns_b[chosen[1]].append(self.check_column_E(chosen[1], x))

        #     nodes.append((columns_b, branches_b, objective))
        
        # return objective, nodes, False
    