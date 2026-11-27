"""Field-by-field compare of pass1 vs pass2. 0 mismatches required."""
import json
from math import isclose

P1 = json.load(open("/workspace/kansas-reverse/verification/pass1.json"))
P2 = json.load(open("/workspace/kansas-reverse/verification/pass2.json"))
n = 0
mm = []

def chk(path, a, b, tol=0):
    global n
    n += 1
    if isinstance(a, float) or isinstance(b, float) or tol:
        ok = isclose(float(a), float(b), rel_tol=0, abs_tol=tol or 1e-9)
    else:
        ok = a == b
    if not ok:
        mm.append((path, a, b))

chk("pad", P1["pad_definition"], P2["pad_definition"])
chk("kansas_m", P1["kansas_constant"]["m"], P2["kansas_constant"]["m"])
chk("kansas_b", P1["kansas_constant"]["b"], P2["kansas_constant"]["b"])
chk("n_counties", len(P1["counties"]), len(P2["counties"]))
chk("county_set", sorted(P1["counties"]), sorted(P2["counties"]))

for race in P1["constants"]:
    for k in ("m", "b", "source", "name"):
        chk(f"const.{race}.{k}", P1["constants"][race][k], P2["constants"][race][k],
            tol=1e-10 if k in ("m", "b") else 0)
    for k in ("r2", "mae", "m_exact", "b_exact", "r2_exact"):
        chk(f"const.{race}.{k}", P1["constants"][race][k], P2["constants"][race][k], tol=1e-8)
    chk(f"const.{race}.candD", P1["constants"][race]["candidates"]["D"], P2["constants"][race]["candidates"]["D"])
    chk(f"const.{race}.candR", P1["constants"][race]["candidates"]["R"], P2["constants"][race]["candidates"]["R"])

INT_SUM = ("D", "R", "T", "I", "unclamped", "n_pos", "n_clamp", "n_zero", "n_capped",
           "margin_before_votes", "margin_after_votes", "win_b", "win_a",
           "sub_D", "sub_R", "sub_T", "sub_margin_votes", "sub_win",
           "n_before_d", "n_after_d")
FLT_SUM = ("unclamped_exact", "margin_before_pts", "margin_after_pts", "sub_margin_pts")
for race in P1["summary"]:
    s1, s2 = P1["summary"][race], P2["summary"][race]
    for k in INT_SUM:
        chk(f"sum.{race}.{k}", s1[k], s2[k])
    for k in FLT_SUM:
        chk(f"sum.{race}.{k}", s1[k], s2[k], tol=1e-8)
    chk(f"sum.{race}.flips", s1["flips"], s2["flips"])
    chk(f"sum.{race}.stay_d", s1["stay_d"], s2["stay_d"])
    chk(f"sum.{race}.top10", s1["top10"], s2["top10"])

INT_C = ("pop", "dreg", "treg", "dreg22", "treg22", "gov22_D", "gov22_R", "gov22_T")
FLT_C = ("D26", "D22", "gov22_S", "gov22_V")
INT_R = ("D", "R", "T", "raw", "I", "win_b", "win_a", "mbv", "mav", "mav_sub", "T_sub")
FLT_R = ("S", "fit", "resid", "pts", "exact", "mb", "ma", "ma_sub")
for c in sorted(P1["counties"]):
    a, b = P1["counties"][c], P2["counties"][c]
    for k in INT_C:
        chk(f"{c}.{k}", a[k], b[k])
    for k in FLT_C:
        chk(f"{c}.{k}", a[k], b[k], tol=1e-10)
    for race in P1["summary"]:
        x, y = a[race], b[race]
        for k in INT_R:
            chk(f"{c}.{race}.{k}", x[k], y[k])
        for k in FLT_R:
            chk(f"{c}.{race}.{k}", x[k], y[k], tol=1e-9)

# historical / saturation
h1, h2 = P1["historical"]["gov_2022"], P2["historical"]["gov_2022"]
for k in ("m_exact", "b_exact", "r2", "mae", "m_4dp", "b_4dp"):
    chk(f"hist.{k}", h1[k], h2[k], tol=1e-8)
chk("hist.2018.status", P1["historical"]["gov_2018"]["status"], P2["historical"]["gov_2018"]["status"])
for label in P1["saturation"]:
    if label == "per_county":
        for c, v in P1["saturation"]["per_county"].items():
            for k, val in v.items():
                chk(f"sat.pc.{c}.{k}", val, P2["saturation"]["per_county"][c][k],
                    tol=1e-9 if isinstance(val, float) else 0)
    else:
        for k, val in P1["saturation"][label].items():
            if k == "members":
                chk(f"sat.{label}.{k}", val, P2["saturation"][label][k])
            elif isinstance(val, float):
                chk(f"sat.{label}.{k}", val, P2["saturation"][label][k], tol=1e-9)
            else:
                chk(f"sat.{label}.{k}", val, P2["saturation"][label][k])

# KEA-12 reproduction
chk("kea12.gov", P2["summary"]["gov"]["I"], 71703)
chk("kea12.ag", P2["summary"]["ag"]["I"], 74243)

print(json.dumps({"checks": n, "mismatches": len(mm), "sample": mm[:15]}, indent=1))
if mm:
    raise SystemExit(1)
