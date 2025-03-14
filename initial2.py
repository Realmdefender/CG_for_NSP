import transformer
import numpy as np
import random as rd
from NR_instance import Instance


# creates an initial (not necessarily feasible) solution
def generate_initial(inst: Instance):

    # initialize assignment variables
    x = np.zeros((inst.p, len(inst.S), len(inst.E)))


    # create schedules for each employee individually
    for e in inst.E:

        # initialize all tracking variables
        i = 0                         # day
        on_counter = 0                # number of consecutive days on
        shift_sequence = []           # list of consecutive shifts
        off_counter = 0               # number of consecutive days off
        work_time = 0                 # total workload

        shift_counter = {}            # counts of each shift type
        for s in inst.S:
            shift_counter[s] = 0

        weekends = inst.employees[e][5]    # amount of weekends left
        weekend_flag = False          # flag to track if a weekend is worked

        forbidden = []                # list of forbidden shifts for the current day due to later scheduling conflicts
        

        while (i < inst.p):

            # update the amount of available weekends at the end of a week
            if (weekend_flag and i % 7 == 0):
                weekends -= 1
                weekend_flag = False

            # when a free day must occur
            if (i in inst.days_off[e]                                        # pre-fixed off day
                or (off_counter > 0 and off_counter < inst.employees[e][4])  # min_off not met
                or on_counter == inst.employees[e][2]                        # max_on met
                or (weekends == 0 and (i % 7 == 5 or i % 7 == 6))       # max_weekends met
                ):

                # callback if a shift should occur instead
                if (on_counter > 0 and on_counter < inst.employees[e][3]):
                    forbidden.append(shift_sequence[0])
                    for j in range(on_counter):
                        x[j + i - on_counter, inst.S[shift_sequence[j]], inst.E[e]] = 0
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
            elif (on_counter > 0 and on_counter < inst.employees[e][3] # min_on not met
                ):

                # get all possible shifts
                options = [s for s in inst.shifts
                           if shift_counter[s] < inst.employees[e][6][s]          # max_shift met
                           and s not in inst.shifts[shift_sequence[-1]][1]        # forbidden sequence
                           and (work_time + inst.shifts[s][0] <= inst.employees[e][0]) # max_worktime met
                           and s not in forbidden
                           ]
                
                # callback if no possible shift is found
                if (len(options) == 0):
                    forbidden.append(shift_sequence[0])
                    for j in range(on_counter):
                        x[j + i - on_counter, inst.S[shift_sequence[j]], inst.E[e]] = 0
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
                    for (j, s) in inst.shifts_off[e]:
                        if (i == j and len(options) > 1 and s in options):
                            options.remove(s)

                    # pick one possible shift and assign it
                    s = rd.choice(options)
                    x[i, inst.S[s], inst.E[e]] = 1

                    on_counter += 1
                    shift_sequence.append(s)
                    off_counter = 0
                    work_time += inst.shifts[s][0]
                    shift_counter[s] += 1
                    if (i % 7 == 5 or i % 7 == 6):
                        weekend_flag = True
                    i += 1
                    


            # choose to either assign a shift or give a free day
            else:

                # get all possible shifts
                options = [s for s in inst.shifts
                           if shift_counter[s] < inst.employees[e][6][s]                         # max_shift met
                           and (on_counter == 0 or s not in inst.shifts[shift_sequence[-1]][1])  # forbidden sequence
                           and (work_time + inst.shifts[s][0] <= inst.employees[e][0])                # max_worktime met
                           and (i, s) not in inst.shifts_off[e]                                  # remove shift off requests
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
                        if ((i, s) in inst.shifts_on[e]):
                            x[i, inst.S[s], inst.E[e]] = 1

                            on_counter += 1
                            shift_sequence.append(s)
                            off_counter = 0
                            work_time += inst.shifts[s][0]
                            shift_counter[s] += 1
                            if (i % 7 == 5 or i % 7 == 6):
                                weekend_flag = True
                            i += 1
                            assigned = True
                            break

                    # pick one possible shift and assign it   
                    if not assigned:
                        s = rd.choice(options)
                        x[i, inst.S[s], inst.E[e]] = 1

                        on_counter += 1
                        shift_sequence.append(s)
                        off_counter = 0
                        work_time += inst.shifts[s][0]
                        shift_counter[s] += 1
                        if (i % 7 == 5 or i % 7 == 6):
                            weekend_flag = True       
                        i += 1

    return x




def initial2(inst):
    p, employees, shifts, days_off, requirements, shifts_on, shifts_off = transformer.prepare_data(inst)

    E = {e: i for i, e in enumerate(employees.keys())}
    S = {s: i for i, s in enumerate(shifts.keys())}

    # initialize assignment variables
    x = np.zeros((p, len(S), len(E)))

    for i in range(p):

        shift_counts = {}
        for s in S:
            shift_counts[s] = 0

        for e in E:            
            for (j, s) in shifts_on[e]:
                if (i == j):
                    x[i, S[s], E[e]] = 1
                    shift_counts[s] += 1
                    break

        for s in S:
            for e in E:
                if (shift_counts[s] < requirements[i, s][0] and x[i, S[s], E[e]] == 0):
                    x[i, S[s], E[e]] = 1
                    shift_counts[s] += 1

    return x
            



def feasible(inst, x):
    p, employees, shifts, days_off, requirements, shifts_on, shifts_off = transformer.prepare_data(inst)

    E = {e: i for i, e in enumerate(employees.keys())}
    S = {s: i for i, s in enumerate(shifts.keys())}

    # max one shift per day
    for e in E:
        for i in range(p):
            if (np.sum(x[i, :, E[e]]) > 1):
                print("more than one shift: ", e, i)
                return False
            
    # pre-fixed days off
    for e in E:
        for i in days_off[e]:
            if (np.sum(x[i, :, E[e]]) > 0):
                print("free day not given", e, i)
                return False
            
    # min/max workload constraints
    for e in E:
        workload = 0
        for i in range(p):
            for s in S:
                workload += x[i, S[s], E[e]] * shifts[s][0]

        if (workload < employees[e][1] or workload > employees[e][0]):
            print("incorrect workload", e, employees[e][0], employees[e][1], workload)
            return False
        
    # max shifts constraint
    for e in E:
        for s in employees[e][6]:
            if (np.sum(x[:, S[s], E[e]]) > employees[e][6][s]):
                print("too many shifts assigned", e, s, np.sum(x[:, s, e]), employees[e][6][s])
                return False
            
    # min and max counters for on and off days
    for e in E:
        on_counter = 0
        off_counter = 0
        for i in range(p):
            if (np.sum(x[i, :, E[e]]) == 0):
                if (on_counter > 0 and on_counter < employees[e][3]):
                    print("min_on not met", e, on_counter, employees[e][3])
                    return False
                on_counter = 0
                off_counter += 1

            else:
                if (off_counter > 0 and off_counter < employees[e][4]):
                    print("min_off not met", e, off_counter, employees[e][4])
                    return False
                on_counter += 1
                off_counter = 0
                if (on_counter > employees[e][2]):
                    print("max_on not met", e, on_counter, employees[e][2])
                    return False

    # max weekends not met
    for e in E:
        weekends = 0
        for w in range(p // 7):
            if (np.sum(x[w * 7 + 5, :, E[e]]) > 0 or np.sum(x[w * 7 + 6, :, E[e]]) > 0):
                weekends += 1
        if (weekends > employees[e][5]):
            print("too many weekends worked", e, weekends, employees[e])
            return False
    
    # forbidden sequences
    forbidden = {-1: []}
    for s in S:
        forbidden[S[s]] = [S[s2] for s2 in shifts[s][1]]
    for e in E:
        last = -1
        for i in range(p):
            if (sum(x[i, :, E[e]]) == 0):
                last = -1
                continue

            for s in S:
                if (x[i, S[s], E[e]] == 1):
                    if (S[s] in forbidden[last]):
                        print("forbidden sequence", e, i, last, S[s])
                        return False
                    last = S[s]
                    break


    return True

for inst in range(10, 11):
    x = initial2(inst)
    # print(feasible(inst, x))
