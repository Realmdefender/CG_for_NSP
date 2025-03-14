from amplpy import AMPL
import transformer

f = open("res1.txt", "a")
for i in range(2, 3):
    ampl = AMPL()
    ampl.read("nurse_rostering.mod")
    p, E, S, C, follows, contracts, days_off, max_shifts, required, shift_on, shift_off = transformer.prepare_data(i)


    ampl.param["p"] = p
    ampl.set["E"] = E
    ampl.set["S"] = list(S.keys())
    ampl.set["C"] = list(C.keys())

    on_weight = {}
    for e in E:
        ampl.set["days_off"][e] = days_off[e]
        ampl.set["contracts"][e] = contracts[e]
    
        if (e in shift_on.keys()):
            ampl.set["shift_on"][e] = list((i, s) for (i, s, _) in shift_on[e])
            on_weight
        else:
            ampl.set["shift_on"][e] = []

        if (e in shift_off.keys()):
            ampl.set["shift_off"][e] = list((i, s) for (i, s, _) in shift_off[e])
        else:
            ampl.set["shift_off"][e] = []

    ampl.param["on_weight"] = {(e, i, s): w for e in shift_on.keys() for (i, s, w) in shift_on[e]}
    ampl.param["off_weight"] = {(e, i, s): w for e in shift_off.keys() for (i, s, w) in shift_off[e]}

    ampl.param["duration"] = {s: duration for s, duration in S.items()}
    for s in S:
        ampl.set["follows"][s] = follows[s]

    ampl.param["max_on"] = {e: max_on for e, (_, _, max_on, _, _, _) in C.items()}
    ampl.param["min_on"] = {e: min_on for e, (_, _, _, min_on, _, _) in C.items()}
    ampl.param["min_off"] = {e: min_off for e, (_, _, _, _, min_off, _) in C.items()}

    ampl.param["max_workload"] = {e: max_workload for e, (max_workload, _, _, _, _, _) in C.items()}
    ampl.param["min_workload"] = {e: min_workload for e, (_, min_workload, _, _, _, _) in C.items()}
    ampl.param["max_shifts"] = {(c, s): shifts[i] for c, shifts in max_shifts.items() for i, s in enumerate(list(S.keys()))}
    ampl.param["max_weekends"] = {e: max_weekends for e, (_, _, _, _, _, max_weekends) in C.items()}

    ampl.param["required"] = {(i, s): req for (i, s), (req, _, _) in required.items()}
    ampl.param["under_weight"] = {(i, s): under for (i, s), (_, under, _) in required.items()}
    ampl.param["over_weight"] = {(i, s): over for (i, s), (_, _, over) in required.items()}


    ampl.set_option("solver", "highs")
    ampl.set_option("time", 10)
    ampl.solve()

    if ampl.solve_result == "solved":
        # f.write(str(i) + ": " + str(ampl.get_objective("satisfaction").value()) + "\n")
        print(ampl.get_data("{e in E, s in S} X[1, s, e]"))
    else:
        f.write(str(i) + ": timed out after 15 minutes\n")

    # if ampl.solve_result != "solved":
    #     raise Exception(f"Failed to solve (solve_result: {ampl.solve_result})")
    # else:
    #     continue
        # testvals = ampl.get_data("{i in P, s in S, e in E} X[i, s, e]")
        # print(testvals)
        
        # print(ampl.get_constraint("cover_requirement"))
        # duals = []
        # for a in ampl.get_constraint("cover_requirement"):
        #     duals.append(a[1].dual())
        # print(duals)
f.close()
