import transformer
import numpy as np
import random as rd


# creates an initial (not necessarily feasible) solution
def initial(inst):
    p, employees, shifts, days_off, requirements, shifts_on, shifts_off = transformer.prepare_data(inst)


    E = {e: i for i, e in enumerate(employees.keys())}
    S = {s: i for i, s in enumerate(shifts.keys())}

    # initialize assignment variables
    x = np.zeros((p, len(S), len(E)))
    worktime = np.zeros(len(E))
    shift_counts = np.zeros((len(E), len(S)))


    on_counts = [employees[e][3] for e in E]
    off_counts = [employees[e][4] for e in E]


    for i in range(1):

        # assign all shift on requests
        for e in E:
            for s in S:
                if ((i, s) in shifts_on[e]):
                    x[i, S[s], E[e]] = 1
                    worktime[E[e]] += shifts[s][0]
                    shift_counts[E[e], S[s]] += 1

        missing = {}
        for s in S:
            missing[s] = requirements[(i, s)][0] - np.sum(x[i, S[s]])


            rest = [E[e] for e in E if np.sum(x[i, :, E[e]]) == 0 
                    and i not in days_off[e] 
                    and (i, s) not in shifts_off[e].keys()
                    and worktime[E[e]] + shifts[s][0] <= employees[e][0]
                    and shift_counts[E[e], S[s]] < employees[e][6][s]
                    and on_counts[E[e]] < employees[e][2]
                    and (off_counts[E[e]] == 0 or off_counts[E[e]] >= employees[e][4])]
            
            probs = np.ones(len(rest))


            while (missing[s] > 0 and len(rest) > 0):
                pick = rd.choice(rest)
                x[i, S[s], pick] = 1

                worktime[E[e]] += shifts[s][0]
                shift_counts[pick, S[s]] += 1
                missing[s] -= 1
                rest.remove(pick)


        for e in E:
            works = np.sum(x[i, :, E[e]])
            if (works > 0):
                on_counts[E[e]] += works
                off_counts[E[e]] = 0
            else:
                on_counts[E[e]] = 0
                off_counts[E[e]] += 1
        
initial(1)
