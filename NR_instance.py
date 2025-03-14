import transformer
import numpy as np
import random as rd
from joblib import Parallel, delayed 
import copy
import time
import math

from E_master import *
from E_sub import *
from NR_ILP import ILP




class Instance(object):
    
    def __init__(self, inst, solve_minutes, solve_choice, flow_control, branching_rule, node_selection):
        p, employees, shifts, days_off, requirements, shifts_on, shifts_off = transformer.prepare_data(inst)

        self.p = p
        self.P = [i for i in range(p)]
        self.P1 = [i for i in range(p - 1)]
        self.W = [i for i in range(int(p / 7))]

        self.employees = employees
        self.E = {e: i for i, e in enumerate(employees.keys())}

        self.shifts = shifts
        self.S = {s: i for i, s in enumerate(shifts.keys())}
        
        self.days_off = days_off
        self.requirements = requirements
        self.shifts_on = shifts_on
        self.shifts_off = shifts_off

        # creates a flow control graph for an additional representation for sequence constraints
        if flow_control:
            self.flow_graph = {}
            for e in self.E:
                self.flow_graph[e] = {}

                # source and sink nodes
                self.flow_graph[e]["source"] = ["on_0", "off_0"]
                for i in range(1, employees[e][3]):
                    self.flow_graph[e]["source"].append("off_" + str(i))
                for i in range(1, employees[e][4]):
                    self.flow_graph[e]["source"].append("on_" + str(i))
                self.flow_graph[e]["sink"] = []

                # one on and off node for each day
                # arcs represent a switch from on to off or vice versa, all days in between are counted as the same activity as the origin
                for i in self.P:
                    on = "on_" + str(i)
                    self.flow_graph[e][on] = []
                    for j in range(i + employees[e][3], i + employees[e][2] + 1):
                        if (j < self.p):
                            self.flow_graph[e][on].append("off_" + str(j))
                        else:
                            self.flow_graph[e][on].append("sink")
                            break

                    off = "off_" + str(i) 
                    self.flow_graph[e][off] = ["sink"]
                    for j in range(i + employees[e][4], self.p):
                        self.flow_graph[e][off].append("on_" + str(j))


        # global parameters
        self.solve_time = 60 * solve_minutes
        self.flow_control = flow_control
        self.solve_choice = solve_choice
        if (self.solve_choice == 'E'):
            self.solve_choice_list = self.E
        elif (self.solve_choice == 'P'):
            self.solve_choice_list = self.P
        self.epsilon = 10e-6
        self.infeasible_penalty = 1000000
        self.branching_rule = branching_rule[0]
        self.branch_perecentage = branching_rule[1]
        self.node_selection = node_selection


        self.start_time = None



        self.current_node = None

        # best found solution for the problem instance
        self.best_solution = None
        self.best_objective = float('inf')




    def solve_instance(self):
        self.start_time = time.time()

        # obtain an initial feaible solution by solving the ILP as a feasibility problem
        feasible_ILP = ILP(self, self.solve_time, False, True, self.flow_control, -1)
        feasible_ILP.optimize()
        end_time_ILP = time.time()

        # return if no feasible solution is found in the given time period
        if(feasible_ILP.Status != 2):
            return self.best_objective, end_time_ILP - self.start_time, 0, 0, 0, []

        # parse the solution
        assignments = np.zeros((self.p, len(self.S), len(self.E)))
        for v in feasible_ILP.getVars():
            data = v.VarName[:-1].split('[')
            if (data[0] == "x"):
                indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]
                assignments[indices[0], self.S[indices[1]], self.E[indices[2]]] = v.X

        self.best_solution = assignments
        self.best_objective = feasible_ILP.getVarByName("sol").X


        # create the root node of the branch and bound tree
        columns = {}
        branches = {}

        if (self.solve_choice == 'E'):
            for e in self.E:
                columns[e] = [self.check_column_E(e, assignments[:, :, self.E[e]])]
                branches[e] = {}
        elif (self.solve_choice == 'P'):
            for i in self.P:
                columns[i] = [self.check_column_P(i, assignments[i, :, :])]
                branches[i] = {}


        # start the branch and bound process
        # if (self.node_selection == 3):
        #     remaining_nodes = [[(columns, branches, 0, 0)]]
        #     current_collection = 0
        # else:
        remaining_nodes = [(columns, branches, 0, 0)]
        # remaining_node_lenght = 1

        total_cycles = []
        fractional_vars = []

        while (len(remaining_nodes) > 0):
            end_time = time.time()
            if (end_time - self.start_time > self.solve_time):
                break


            # select the next node to be explored
            # breadth first search
            if (self.node_selection == 0):
                self.current_node = remaining_nodes.pop(0)

            # depth first search
            elif(self.node_selection == 1):
                self.current_node = remaining_nodes.pop(-1)

            # best first search
            elif(self.node_selection == 2):
                remaining_nodes.sort(key=lambda x: x[2])
                self.current_node = remaining_nodes.pop(-1)

            # cyclic best fisrt search
            # elif(self.node_selection == 3):
            #     remaining_nodes[current_collection].sort(key=lambda x: x[2])
            #     self.current_node = remaining_nodes[current_collection].pop(-1)


            # fathoming by bound
            if (self.current_node[2] >= self.best_objective - self.epsilon):
                # remaining_node_lenght -= 1

                # if (self.node_selection == 3):
                #     current_collection = self.update_cycle(remaining_nodes, current_collection)
                continue

            # solve the current node
            objective, assignments, cycles = self.column_generation()

            # find all fractional variables in the returned solution
            fractionals = []
            for i in self.P:
                for s in self.S:
                    for e in self.E:
                        v = assignments[i, self.S[s], self.E[e]]
                        if (v > self.epsilon and v < 1 - self.epsilon):
                            fractionals.append((i, s, e, v))
            fractionals = sorted(fractionals, key=lambda tup: abs(tup[3] - 0.5))

            total_cycles.append(cycles)
            fractional_vars.append(len(fractionals))

            # prune by bound
            if (objective >= self.best_objective - self.epsilon):
                # remaining_node_lenght -= 1

                # if (self.node_selection == 3):
                #     current_collection = self.update_cycle(remaining_nodes, current_collection)
                continue

            # prune by integrality
            if (len(fractionals) == 0):
                if (objective < self.best_objective):
                    self.best_objective = objective
                    self.best_solution = assignments

                # remaining_node_lenght -= 1
                # if (self.node_selection == 3):
                #     current_collection = self.update_cycle(remaining_nodes, current_collection)
                continue


            # choose whichh variables to check for potential branching
            # most fractional variable
            if (self.branching_rule == 1):
                chosen_var = fractionals[0]

            # random variable
            elif (self.branching_rule == -1):
                chosen_var = rd.choice(fractionals)

            # strong branching (0 => full strong branching;
            #                    x > 1 => x most fractional variables are tested;
            #                    branch_percentage = True => x% of fractional variables are tested)
            else:
                if (self.branching_rule > 1 and self.branch_perecentage):
                    values = math.ceil(len(fractionals) * self.branching_rule / 100)
                    fractionals = fractionals[:values]
                elif (self.branching_rule > 1):
                    fractionals = fractionals[:self.branching_rule]

                # calculate the objectives of all picked variables and choose the best one
                strong_branching_results = {}
                for fractional in fractionals:
                    strong_branching_results[fractional] = []
                    for c in range(2):
                        strong_branching_RMP = RMP_E(self, fractional, c)
                        strong_branching_RMP.optimize()
                        strong_branching_results[fractional].append(strong_branching_RMP.objVal - objective)

                chosen_var = max(strong_branching_results, key=lambda k: max(strong_branching_results[k][0], self.epsilon) * max(strong_branching_results[k][1], self.epsilon))
            

            # create branches
            left_branch, right_branch = self.branch(assignments, objective, chosen_var)

            # if (self.node_selection == 3):
            #     if (len(remaining_nodes) == left_branch[3]):
            #         remaining_nodes.append([])
            #     remaining_nodes[left_branch[3]].append(left_branch)
            #     remaining_nodes[left_branch[3]].append(right_branch)
            #     current_collection = self.update_cycle(remaining_nodes, current_collection)
            # else:
            remaining_nodes.append(left_branch)
            remaining_nodes.append(right_branch)

            # remaining_node_lenght += 1         


        end_time = time.time()
        max_cycles = max(total_cycles)
        average_cycles = sum(total_cycles) / len(total_cycles)
        return self.best_objective, end_time - self.start_time, len(total_cycles), average_cycles, max_cycles, fractional_vars
    

    # def update_cycle(self, remaining, i):
    #     res = i + 1
    #     if (res == len(remaining)):
    #         res = 0
    #     while (len(remaining[res]) == 0):
    #         res = (res + 1) % len(remaining)
    #     return res


    def column_generation(self):
        cycles = 0
        while True:
            cycles += 1


            # solve the restricted master problem
            if (self.solve_choice == 'E'):
                restricted_master_problem = RMP_E(self, None, 0)
            elif (self.solve_choice == 'P'):
                restricted_master_problem = RMP_P(self, None, 0)
            restricted_master_problem.optimize()

            # return if no feasible solution is found
            if (restricted_master_problem.Status == 3):
                return self.best_objective, None, False, 0

            # extract dual variables
            duals = {}
            names = []
            for c in restricted_master_problem.getConstrs():
                data = c.ConstrName[:-1].split('[')
                indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

                if (data[0] not in names):
                    names.append(data[0])
                    duals[data[0]] = {}

                if (len(indices) > 1):
                    duals[data[0]][tuple(indices)] = c.Pi
                else:
                    duals[data[0]][indices[0]] = c.Pi


            # run the sub_problems and extract found columns
            sub_problem_columns = Parallel(n_jobs=-1)(delayed(self.solve_sub_problem)(a, duals) for a in self.solve_choice_list)

            counter = 0
            for column in sub_problem_columns:
                if (column is None):
                    counter += 1
                else:
                    self.current_node[0][column[0]].append(column[1])
            if (counter == len(self.solve_choice_list)):
                break


        # retrieve all lambda variable values from the restricted master problem and check for integrality
        objective = restricted_master_problem.ObjVal
        assignments = np.zeros((self.p, len(self.S), len(self.E)))

        for v in restricted_master_problem.getVars():
            data = v.VarName[:-1].split('[')
            indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

            if (data[0] == "lambda"):
                if (self.solve_choice == 'E'):
                    assignments[:, :, self.E[indices[0]]] += self.current_node[0][indices[0]][indices[1]][0] * v.X
                elif (self.solve_choice == 'P'):
                    assignments[indices[0], :, :] += self.current_node[0][indices[0]][indices[1]][0] * v.X

        return objective, assignments, cycles




    def solve_sub_problem(self, variable_pick, duals):

        end_time = time.time()
        if (end_time - self.start_time > self.solve_time):
            return None

        # solve the sub-problem
        if (self.solve_choice == 'E'):
            sub_problem = SP_E(self, variable_pick, duals, self.current_node[1][variable_pick], self.flow_control)
        elif(self.solve_choice == 'P'):
            sub_problem = SP_P(self, variable_pick, duals, self.current_node[1][variable_pick], self.flow_control)
        sub_problem.optimize()

        # if a negative reduced cost is found, extract all variable values and return the column
        if (sub_problem.Status == 2  and sub_problem.ObjVal < -self.epsilon):
            if (self.solve_choice == 'E'):
                x = np.zeros((self.p, len(self.S)))
            elif(self.solve_choice == 'P'):
                x = np.zeros((len(self.S), len(self.E)))

            for v in sub_problem.getVars():
                data = v.VarName[:-1].split('[')
                indices = [int(a) if a.isdigit() else a for a in data[1].split(',')]

                if (data[0] == "x"):
                    if (self.solve_choice == 'E'):
                        x[indices[0], self.S[indices[1]]] = v.X
                    elif(self.solve_choice == 'P'):
                        x[self.S[indices[0]], self.E[indices[1]]] = v.X
                    
            return (variable_pick, (x, 0))
        
        return None




    def branch(self, x, lower_bound, chosen_var):

        left_columns = copy.deepcopy(self.current_node[0])
        left_branches = copy.deepcopy(self.current_node[1])
        right_columns = copy.deepcopy(self.current_node[0])
        right_branches = copy.deepcopy(self.current_node[1])

        if (self.solve_choice == 'E'):
            left_columns[chosen_var[2]] = [c for c in left_columns[chosen_var[2]] if c[0][chosen_var[0], self.S[chosen_var[1]]] == 0]
            left_branches[chosen_var[2]][(chosen_var[0], chosen_var[1])] = 0

            right_columns[chosen_var[2]] = [c for c in right_columns[chosen_var[2]] if c[0][chosen_var[0], self.S[chosen_var[1]]] == 1]
            right_branches[chosen_var[2]][(chosen_var[0], chosen_var[1])] = 1

        elif (self.solve_choice == 'P'):
            left_columns[chosen_var[0]] = [c for c in left_columns[chosen_var[2]] if c[0][self.S[chosen_var[1]], self.E[chosen_var[2]]] == 0]
            left_branches[chosen_var[0]][(chosen_var[1], chosen_var[2])] = 0

            right_columns[chosen_var[0]] = [c for c in right_columns[chosen_var[2]] if c[0][self.S[chosen_var[1]], self.E[chosen_var[2]]] == 1]
            right_branches[chosen_var[0]][(chosen_var[1], chosen_var[2])] = 1

        return (left_columns, left_branches, lower_bound, self.current_node[3] + 1), (right_columns, right_branches, lower_bound, self.current_node[3] + 1)


    # creates an initial (not necessarily feasible) solution
    def generate_initial(self):

        # initialize assignment variables
        x = np.zeros((self.p, len(self.S), len(self.E)))


        # create schedules for each employee individually
        for e in self.E:

            # initialize all tracking variables
            i = 0                         # day
            on_counter = 0                # number of consecutive days on
            shift_sequence = []           # list of consecutive shifts
            off_counter = 0               # number of consecutive days off
            work_time = 0                 # total workload

            shift_counter = {}            # counts of each shift type
            for s in self.S:
                shift_counter[s] = 0

            weekends = self.employees[e][5]    # amount of weekends left
            weekend_flag = False          # flag to track if a weekend is worked

            forbidden = []                # list of forbidden shifts for the current day due to later scheduling conflicts
            

            while (i < self.p):

                # update the amount of available weekends at the end of a week
                if (weekend_flag and i % 7 == 0):
                    weekends -= 1
                    weekend_flag = False

                # when a free day must occur
                if (i in self.days_off[e]                                        # pre-fixed off day
                    or (off_counter > 0 and off_counter < self.employees[e][4])  # min_off not met
                    or on_counter == self.employees[e][2]                        # max_on met
                    or (weekends == 0 and (i % 7 == 5 or i % 7 == 6))       # max_weekends met
                    ):

                    # callback if a shift should occur instead
                    if (on_counter > 0 and on_counter < self.employees[e][3]):
                        forbidden.append(shift_sequence[0])
                        for j in range(on_counter):
                            x[j + i - on_counter, self.S[shift_sequence[j]], self.E[e]] = 0
                        for s in shift_sequence:
                            shift_counter[s] -= 1
                        weekends += i // 7 - (i - on_counter) // 7

                        i -= on_counter
                        on_counter = 0
                        shift_sequence = []
                        off_counter = 0
                        weekend_flag = False
                        

                    # assign no shift
                    else:
                        i += 1
                        on_counter = 0
                        shift_sequence = []
                        off_counter += 1


                # when a shift must occur
                elif (on_counter > 0 and on_counter < self.employees[e][3] # min_on not met
                    ):

                    # get all possible shifts
                    options = [s for s in self.shifts
                            if shift_counter[s] < self.employees[e][6][s]          # max_shift met
                            and s not in self.shifts[shift_sequence[-1]][1]        # forbidden sequence
                            and (work_time + self.shifts[s][0] <= self.employees[e][0]) # max_worktime met
                            and s not in forbidden
                            ]
                    
                    # callback if no possible shift is found
                    if (len(options) == 0):
                        forbidden.append(shift_sequence[0])
                        for j in range(on_counter):
                            x[j + i - on_counter, self.S[shift_sequence[j]], self.E[e]] = 0
                        for s in shift_sequence:
                            shift_counter[s] -= 1
                        weekends += i // 7 - (i - on_counter) // 7

                        i -= on_counter
                        on_counter = 0
                        shift_sequence = []
                        off_counter = 0
                        weekend_flag = False

                    else:

                        # remove all shift-off preferences if possible
                        for (j, s) in self.shifts_off[e]:
                            if (i == j and len(options) > 1 and s in options):
                                options.remove(s)

                        # pick one possible shift and assign it
                        s = rd.choice(options)
                        x[i, self.S[s], self.E[e]] = 1

                        on_counter += 1
                        shift_sequence.append(s)
                        off_counter = 0
                        work_time += self.shifts[s][0]
                        shift_counter[s] += 1
                        if (i % 7 == 5 or i % 7 == 6):
                            weekend_flag = True
                        i += 1
                        


                # choose to either assign a shift or give a free day
                else:

                    # get all possible shifts
                    options = [s for s in self.shifts
                            if shift_counter[s] < self.employees[e][6][s]                         # max_shift met
                            and (on_counter == 0 or s not in self.shifts[shift_sequence[-1]][1])  # forbidden sequence
                            and (work_time + self.shifts[s][0] <= self.employees[e][0])           # max_worktime met
                            and (i, s) not in self.shifts_off[e]                                  # remove shift off requests
                            and s not in forbidden
                            ]
                    
                    # off day if no shifts are left
                    if (len(options) == 0):
                        i += 1
                        on_counter = 0
                        shift_sequence = []
                        off_counter += 1
                        forbidden = []

                    else:

                        # grant shift on request if possible
                        assigned = False
                        for s in options:
                            if ((i, s) in self.shifts_on[e]):
                                x[i, self.S[s], self.E[e]] = 1

                                on_counter += 1
                                shift_sequence.append(s)
                                off_counter = 0
                                work_time += self.shifts[s][0]
                                shift_counter[s] += 1
                                if (i % 7 == 5 or i % 7 == 6):
                                    weekend_flag = True
                                i += 1
                                assigned = True
                                break

                        # pick one possible shift and assign it   
                        if not assigned:
                            s = rd.choice(options)
                            x[i, self.S[s], self.E[e]] = 1

                            on_counter += 1
                            shift_sequence.append(s)
                            off_counter = 0
                            work_time += self.shifts[s][0]
                            shift_counter[s] += 1
                            if (i % 7 == 5 or i % 7 == 6):
                                weekend_flag = True       
                            i += 1

        return x

    # checks if a column in feasible and calculates relevant values
    # parameters: 
    #   e                   = the employee of this sub-problem
    #   x                   = assignment variable values for the employee
    # returns:
    #   (x, (v_on, v_off), w) = a column for the restricted master problem
    def check_column_E(self, e, x):

        # max one shift per day
        for i in self.P:
            if (np.sum(x[i, :]) > 1):
                return (x, 1000000)

        # pre-fixed days off
        for i in self.days_off[e]:
            if (np.sum(x[i, :]) > 0):
                return (x, 1000000)

        # min/max workload constraints
        workload = 0
        for i in self.P:
            for s in self.S:
                workload += x[i, self.S[s]] * self.shifts[s][0]
        if (workload < self.employees[e][1] or workload > self.employees[e][0]):
            return (x, 1000000)

        # max shifts constraint
        for s in self.employees[e][6]:
            if (np.sum(x[:, self.S[s]]) > self.employees[e][6][s]):
                return (x, 1000000)

        # min and max counters for on and off days
        on_counter = 0
        off_counter = 0
        off_had = False
        on_had = False
        for i in self.P:
            if (np.sum(x[i, :]) == 0):
                if (on_counter > 0 and on_counter < self.employees[e][3] and off_had and on_had):
                    return (x, 1000000)
                on_counter = 0
                off_counter += 1
                off_had = True

            else:
                if (off_counter > 0 and off_counter < self.employees[e][4] and off_had and on_had):
                    return (x, 1000000)
                on_counter += 1
                off_counter = 0
                on_had = True

                if (on_counter > self.employees[e][2]):
                    return (x, 1000000)
        
        # max weekends not met
        weekends = 0
        for w in self.W:
            if (np.sum(x[w * 7 + 5, :]) > 0 or np.sum(x[w * 7 + 6, :]) > 0):
                weekends += 1
        if (weekends > self.employees[e][5]):
            return (x, 1000000)

        # forbidden sequences
        forbidden = {-1: []}
        for s in self.S:
            forbidden[self.S[s]] = [self.S[s2] for s2 in self.shifts[s][1]]

        last = -1
        for i in self.P:
            if (sum(x[i, :]) == 0):
                last = -1
                continue
            for s in self.S:
                if (x[i, self.S[s]] == 1):
                    if (self.S[s] in forbidden[last]):
                        return (x, 1000000)
                    last = self.S[s]
                    
        return(x, 0)


    # checks if a column in feasible and calculates relevant values
    # parameters: 
    #   i                   = the day of this sub-problem
    #   x                   = assignment variable values for the day
    # returns:
    #   (x, (v_under, v_over), 0) = a column for the restricted master problem
    def check_column_P(self, i, x):
        v_over = 0
        v_under = 0

        for s in self.S:
            assigned = self.requirements[i, s][0] - sum(x[self.S[s]])

            if (assigned > 0):
                v_under += assigned * self.requirements[i, s][1]
            elif(assigned < 0):
                v_over -= assigned * self.requirements[i, s][2]

        return(x, (v_under, v_over), 0)
