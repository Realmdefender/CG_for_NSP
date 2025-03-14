import pandas as pd

def prepare_data(instance):
    
    # open the relevant file and read all lines
    file_name = "NR_instances/inst" + str(instance) + ".txt"
    file = open(file_name)
    lines = file.readlines()
    file.close()

    # dictionaries for all entities and parameters used in the model
    p = 0
    E = {}
    S = {}

    days_off = {}
    required = {}
    shift_on = {}
    shift_off = {}

    # counters used during parsing
    section = 0

    for line in lines:
        # ignore useless lines and define different sections
        if (line.startswith(('#', '\n'))):
            continue
        elif (line.startswith("SECTION")):
            section += 1
            continue

        else:
            # period length p
            if (section == 1):
                p = int(line.strip())

            # S[s] = ("duration", "forbidden[s]")
            elif (section == 2):
                data = line.strip().split(',')
                S[data[0]] = int(data[1])

                follow = []
                for s in (data[2].split('|')):
                    if (s != ''):
                        follow.append(s.strip())
                S[data[0]] = (int(data[1]), follow)

            # E[e] = ("max_workload", "min_workload", "max_on", "min_on", "min_off", "max_weekends", "max_shifts[s]")
            elif (section == 3):
                data = line.strip().split(',')
                
                max_shift = {}
                for s in (data[1].split('|')):
                    ss = s.split('=')
                    max_shift[ss[0]] = int(ss[1])
                E[data[0]] = (int(data[2]), int(data[3]), int(data[4]), int(data[5]), int(data[6]), int(data[7]), max_shift)
                days_off[data[0]] = []
                shift_on[data[0]] = {}
                shift_off[data[0]] = {}

            # days_off[e] = [i]
            elif (section == 4):
                data = line.strip().split(',')

                day_off = []
                for i in range(1, len(data)):
                    day_off.append(int(data[i]))
                days_off[data[0]] = day_off

            # shift_on[e] = {(i, s): "on_weight"}
            elif (section == 5):
                data = line.strip().split(',')

                shift_on[data[0]][(int(data[1]), data[2])] = int(data[3])

            # shift_off[e] = {(i, s): "off_weight"}
            elif (section == 6):
                data = line.strip().split(',')

                shift_off[data[0]][(int(data[1]), data[2])] = int(data[3])

            # required[(i, s)] = ("required", "under_weight", "over_weight")
            elif (section == 7):
                data = line.strip().split(',')

                required[(int(data[0]), data[1])] = (int(data[2]), int(data[3]), int(data[4]))
   
    return p, E, S, days_off, required, shift_on, shift_off
