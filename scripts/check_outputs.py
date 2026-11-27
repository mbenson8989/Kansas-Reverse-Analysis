"""Check CSVs, chart manifest, and report figures against pass1 and pass2."""
import csv, json, re
from math import isclose
from pathlib import Path
from PIL import Image

P1 = json.load(open("/workspace/kansas-reverse/verification/pass1.json"))
P2 = json.load(open("/workspace/kansas-reverse/verification/pass2.json"))
M = json.load(open("/workspace/kansas-reverse/verification/chart_manifest.json"))
DATA = Path("/workspace/kansas-reverse/data")
REP = Path("/workspace/kansas-reverse/report/Kansas-Reverse-Analysis.md").read_text()
n = 0
mm = []
RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
SLUG = {
    "sen": "united_states_senate",
    "gov": "governor",
    "sos": "secretary_of_state",
    "ag": "attorney_general",
    "treas": "state_treasurer",
    "ins": "commissioner_of_insurance",
}

def chk(path, a, b, tol=0):
    global n
    n += 1
    if isinstance(a, float) or isinstance(b, float) or tol:
        ok = isclose(float(a), float(b), rel_tol=0, abs_tol=tol or 1e-9)
    else:
        ok = a == b
    if not ok:
        mm.append((path, a, b))

# KEA-12
chk("kea12.gov.p1", P1["summary"]["gov"]["I"], 71703)
chk("kea12.gov.p2", P2["summary"]["gov"]["I"], 71703)
chk("kea12.ag.p1", P1["summary"]["ag"]["I"], 74243)
chk("kea12.ag.p2", P2["summary"]["ag"]["I"], 74243)

# CSVs vs pass2
master = list(csv.DictReader(open(DATA / "master_all_races.csv")))
chk("master.n", len(master), 105)
pops = [int(r["population_2025"]) for r in master]
chk("master.sorted", pops, sorted(pops, reverse=True))
for r in master:
    c = r["county"]
    v = P2["counties"][c]
    chk(f"{c}.pop", int(r["population_2025"]), v["pop"])
    chk(f"{c}.dreg", int(r["dem_reg_2026"]), v["dreg"])
    chk(f"{c}.treg", int(r["total_reg_2026"]), v["treg"])
    for race in RACE_ORDER:
        x = v[race]
        chk(f"{c}.{race}.I", int(r[f"{race}_injected_votes_I"]), x["I"])
        chk(f"{c}.{race}.raw", int(r[f"{race}_injected_votes_unclamped"]), x["raw"])
        chk(f"{c}.{race}.D", int(r[f"{race}_D"]), x["D"])
        chk(f"{c}.{race}.R", int(r[f"{race}_R"]), x["R"])
        chk(f"{c}.{race}.T", int(r[f"{race}_T"]), x["T"])
        chk(f"{c}.{race}.win_b", r[f"{race}_winner_before"], x["win_b"])
        chk(f"{c}.{race}.win_a", r[f"{race}_winner_after_transfer"], x["win_a"])
        chk(f"{c}.{race}.mbv", int(r[f"{race}_margin_before_votes"]), x["mbv"])
        chk(f"{c}.{race}.mav", int(r[f"{race}_margin_after_transfer_votes"]), x["mav"])
        want = "YES" if x["win_b"] != x["win_a"] else ""
        chk(f"{c}.{race}.flip", r[f"{race}_flips"], want)

for race in RACE_ORDER:
    rows = list(csv.DictReader(open(DATA / f"county_{SLUG[race]}.csv")))
    chk(f"per.{race}.n", len(rows), 105)
    chk(f"per.{race}.Isum", sum(int(r["injected_votes_I"]) for r in rows), P2["summary"][race]["I"])
    top = list(csv.DictReader(open(DATA / f"top10_{SLUG[race]}.csv")))
    chk(f"top.{race}.n", len(top), 10)
    want = P2["summary"][race]["top10"]
    for i, (row, w) in enumerate(zip(top, want)):
        chk(f"top.{race}.{i}.c", row["county"], w["county"])
        chk(f"top.{race}.{i}.I", int(row["injected_votes_I"]), w["I"])

ss = {r["race_key"]: r for r in csv.DictReader(open(DATA / "statewide_summary.csv"))}
for race in RACE_ORDER:
    s = P2["summary"][race]
    c = P2["constants"][race]
    row = ss[race]
    chk(f"ss.{race}.I", int(row["injected_votes_I"]), s["I"])
    chk(f"ss.{race}.m", float(row["m"]), c["m"])
    chk(f"ss.{race}.b", float(row["b"]), c["b"])
    chk(f"ss.{race}.win_b", row["winner_before"], s["win_b"])
    chk(f"ss.{race}.win_a", row["winner_after_transfer"], s["win_a"])
    chk(f"ss.{race}.mbv", int(row["margin_before_votes"]), s["margin_before_votes"])
    chk(f"ss.{race}.mav", int(row["margin_after_transfer_votes"]), s["margin_after_votes"])
    chk(f"ss.{race}.subv", int(row["margin_after_subtract_votes"]), s["sub_margin_votes"])

# charts
for race in RACE_ORDER:
    info = M["races"][race]
    s = P2["summary"][race]
    im = Image.open(info["path"])
    chk(f"img.{race}.size", tuple(im.size), (1920, 1080))
    chk(f"img.{race}.title", info["title"], "When you remove the injection equation / share injection, this is what happens")
    chk(f"img.{race}.I", info["I"], s["I"])
    chk(f"img.{race}.n", info["n_pos"], s["n_pos"])
    chk(f"img.{race}.win_b", info["win_b"], s["win_b"])
    chk(f"img.{race}.win_a", info["win_a"], s["win_a"])
    chk(f"img.{race}.bv", info["before_votes"], s["margin_before_votes"])
    chk(f"img.{race}.av", info["after_votes"], s["margin_after_votes"])
    chk(f"img.{race}.bp", info["before_pts"], s["margin_before_pts"], tol=1e-12)
    chk(f"img.{race}.ap", info["after_pts"], s["margin_after_pts"], tol=1e-12)
    chk(f"img.{race}.bpd", info["before_pts_disp"], round(s["margin_before_pts"], 2), tol=0.005)
    chk(f"img.{race}.apd", info["after_pts_disp"], round(s["margin_after_pts"], 2), tol=0.005)

for k, v in M["totals"]["values"].items():
    chk(f"tot.{k}", v, P2["summary"][k]["I"])
im = Image.open(M["totals"]["path"])
chk("tot.size", tuple(im.size), (1920, 1080))
im = Image.open(M["top10"]["path"])
chk("top10.size", tuple(im.size), (1920, 1080))
for race in RACE_ORDER:
    got = M["top10"]["values"][race]
    want = [[r["county"], r["I"]] for r in P2["summary"][race]["top10"]]
    chk(f"top10m.{race}", got, want)

# report contains exact statewide I and the exact title
for race in RACE_ORDER:
    I = f"{P2['summary'][race]['I']:,}"
    chk(f"rep.has_I.{race}", I in REP, True)
chk("rep.title", "When you remove the injection equation / share injection, this is what happens" in REP, True)
chk("rep.locked_m", "67.6004" in REP, True)
chk("rep.locked_b", "6.3014" in REP, True)
chk("rep.kea12.gov", "71,703" in REP, True)
chk("rep.kea12.ag", "74,243" in REP, True)
chk("rep.hyp", "Hypothesis, not a finding" in REP, True)
chk("rep.cvr", "Cast vote record (CVR) access may be blocked" in REP, True)
chk("rep.unofficial", "unofficial" in REP.lower(), True)
chk("rep.no_add", "must not be added together" in REP, True)
# personal-name scan is done outside this script so the source tree stays clean

# wiki == report
wiki = Path("/workspace/kansas-reverse/wiki/Kansas-Reverse-Analysis.md").read_text()
chk("wiki.eq.report", wiki, REP)

print(json.dumps({"checks": n, "mismatches": len(mm), "sample": mm[:20]}, indent=1))
if mm:
    raise SystemExit(1)
