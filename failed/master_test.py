from amplpy import AMPL
import transformer


ampl = AMPL()
ampl.read("S_master.mod")

ampl.set_option("solver", "highs")
ampl.solve()
if ampl.solve_result != "solved":
    raise Exception(f"Failed to solve (solve_result: {ampl.solve_result})")
else:
    testvals = ampl.get_data("{i in P, s in S, e in E} X[i, s, e]")
    print(testvals)
    print(ampl.get_objective("satisfaction").get().value())
