"""Pass 2 of the Kansas 2026* reverse analysis.
Independent of pass 1: regex HTML parse, openpyxl registration, csv population,
Fraction OLS (normal equations) and integer/Fraction arithmetic throughout.
"""
from __future__ import annotations

import csv
import json
import os
import re
from fractions import Fraction as F

import openpyxl

ENT = "/workspace/kansas-wiki/verification/ent_refetch_20261119/"
RAW = "/workspace/kansas/raw/"
OUT = "/workspace/kansas-reverse/verification/pass2.json"

HTML_TITLE = {
    "sen": "United States Senate",
    "gov": "Governor / Lt. Governor",
    "sos": "Secretary of State",
    "ag": "Attorney General",
    "treas": "State Treasurer",
    "ins": "Commissioner of Insurance",
}
RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
LOCKED = {"gov": (F(676004, 10000), F(63014, 10000)), "ag": (F(675582, 10000), F(64993, 10000))}
DISPLAY = {
    "sen": "United States Senate",
    "gov": "Governor",
    "sos": "Secretary of State",
    "ag": "Attorney General",
    "treas": "State Treasurer",
    "ins": "Commissioner of Insurance",
}


def canon(s: str) -> str:
    s = str(s).strip().lower()
    return "McPherson" if s == "mcpherson" else " ".join(w.capitalize() for w in s.split())


def half_up(q: F) -> int:
    s = -1 if q < 0 else 1
    return int(s * ((abs(q) * 2 + 1) // 2))


def r4(q: F) -> F:
    return F(half_up(q * 10000), 10000)


def parse_ent(fn: str) -> dict:
    h = open(ENT + fn, encoding="utf-8").read()
    h = h[h.index('id="party-county-all"'):]
    out = {}
    cand = {k: {"D": set(), "R": set()} for k in HTML_TITLE}
    for bl in re.split(r'<div class="race">', h)[1:]:
        t = re.search(r"<h3>(.*?)</h3>", bl).group(1).strip()
        key = next((k for k, title in HTML_TITLE.items() if title == t), None)
        if not key:
            continue
        lst = bl[bl.index("race-candidate-list"):]
        lst = lst[: lst.index("Candidate")] if "Candidate" in lst else lst
        cells = re.findall(
            r'<div class="col-4">\s*<p>(.*?)</p>\s*</div>\s*<div class="col-2">\s*<p>([\d,]+)</p>',
            lst,
        )
        dmap = {a: int(b.replace(",", "")) for a, b in cells}
        out[key] = {
            "D": sum(v for a, v in dmap.items() if a[:2] == "D-"),
            "R": sum(v for a, v in dmap.items() if a[:2] == "R-"),
            "T": sum(dmap.values()),
            "candidates": dmap,
        }
        for a in dmap:
            if a[:2] == "D-":
                cand[key]["D"].add(a)
            if a[:2] == "R-":
                cand[key]["R"].add(a)
    return out, cand


V = {}
CAND = {k: {"D": set(), "R": set()} for k in HTML_TITLE}
for fn in os.listdir(ENT):
    if not fn.endswith(".html"):
        continue
    c = canon(fn[:-5])
    parsed, cand = parse_ent(fn)
    V[c] = parsed
    for k in cand:
        CAND[k]["D"] |= cand[k]["D"]
        CAND[k]["R"] |= cand[k]["R"]
assert len(V) == 105
assert all(all(k in V[c] for k in HTML_TITLE) for c in V)


def load_reg(path, sheet, ck, dk, tk):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    rows = list(ws.iter_rows(values_only=True))
    hdr = list(rows[0])
    out = {}
    for r in rows[1:]:
        if r[hdr.index(ck)] and str(r[hdr.index(ck)]).strip() != "Grand Total":
            out[canon(r[hdr.index(ck)])] = (int(r[hdr.index(dk)]), int(r[hdr.index(tk)]))
    return out


reg26 = load_reg(
    RAW + "10-2026-Voter-Registration-Numbers-by-County.xlsx",
    "By County",
    "County",
    "Democratic",
    "Total",
)
reg22 = load_reg(
    RAW + "11-2022-Voter-Registration-Numbers-by-County.xlsx",
    "Nov. 2022",
    "Jurisdiction",
    "Democratic",
    "Grand Total",
)
assert sum(a for a, _ in reg26.values()) == 521669
assert sum(b for _, b in reg26.values()) == 2027520
assert sum(a for a, _ in reg22.values()) == 523317
assert sum(b for _, b in reg22.values()) == 1975535

pop = {}
with open(RAW + "co-est2025-alldata.csv", encoding="latin-1") as f:
    for row in csv.DictReader(f):
        if row["STATE"] == "20" and row["COUNTY"] != "000":
            pop[canon(row["CTYNAME"][:-7])] = int(row["POPESTIMATE2025"])
assert set(V) == set(reg26) == set(reg22) == set(pop)


def precinct_governor(path, sheet):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[sheet]
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    ci = {n: i for i, n in enumerate(hdr)}
    out = {}
    for r in rows:
        if r[ci["County"]] is None:
            continue
        c = canon(r[ci["County"]])
        o = out.setdefault(c, {"D": 0, "R": 0, "T": 0})
        v = int(r[ci["Votes"]] or 0)
        o["T"] += v
        party = str(r[ci["Party"]]).strip()
        if party == "Democratic":
            o["D"] += v
        elif party == "Republican":
            o["R"] += v
    return out


def big4_governor(path, dkey, rkey, allkeys):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    res = {}
    for sh in ["JOHNSON", "SEDGWICK", "SHAWNEE", "WYANDOTTE"]:
        rows = list(wb[sh].iter_rows(values_only=True))
        tot = [r for r in rows if r[1] is not None and "COUNTY TOTALS" in str(r[1]).upper()][0]
        hdr = [" ".join(str(rows[i][j]).lower() for i in range(3)) for j in range(len(rows[0]))]
        D = R = T = 0
        for j, hh in enumerate(hdr):
            if any(k in hh for k in allkeys):
                val = int(tot[j])
                T += val
                if dkey in hh:
                    D += val
                if rkey in hh:
                    R += val
        res[canon(sh)] = {"D": D, "R": R, "T": T}
    return res


g22 = precinct_governor(RAW + "2022-General-Election-Governor-Results-By-Precinct.xlsx", "Governor")
g22.update(
    big4_governor(
        RAW + "2022-General-Election-Governor-Results-By-Precinct.xlsx",
        "kelly",
        "schmidt",
        ("kelly", "schmidt", "cordell", "pyle"),
    )
)
assert sum(v["D"] for v in g22.values()) == 499849
assert set(g22) == set(V)

cs = sorted(V)
D26 = {c: F(100 * reg26[c][0], reg26[c][1]) for c in cs}
D22 = {c: F(100 * reg22[c][0], reg22[c][1]) for c in cs}


def ols_fraction(xs, ys):
    N = F(len(xs))
    sx = sum(xs)
    sy = sum(ys)
    sxx = sum(x * x for x in xs)
    sxy = sum(x * y for x, y in zip(xs, ys))
    syy = sum(y * y for y in ys)
    m = (N * sxy - sx * sy) / (N * sxx - sx * sx)
    b = (sy - m * sx) / N
    sse = sum((y - m * x - b) ** 2 for x, y in zip(xs, ys))
    sst = syy - sy * sy / N
    r2 = 1 - sse / sst if sst != 0 else F(0)
    mae = sum(abs(y - m * x - b) for x, y in zip(xs, ys)) / N
    return m, b, r2, mae


def fit_race(key):
    xs = [D26[c] / 100 for c in cs]
    ys = [F(100 * V[c][key]["D"], V[c][key]["T"]) - D26[c] for c in cs]
    m_ex, b_ex, r2_ex, mae_ex = ols_fraction(xs, ys)
    if key in LOCKED:
        m, b = LOCKED[key]
        source = "locked" if key == "gov" else "stated_ag_fit"
    else:
        m, b = r4(m_ex), r4(b_ex)
        source = "fitted_4dp"
    sse = sum((y - m * x - b) ** 2 for x, y in zip(xs, ys))
    sst = sum((y - sum(ys) / F(len(ys))) ** 2 for y in ys)
    r2_used = 1 - sse / sst if sst != 0 else F(0)
    mae_used = sum(abs(y - m * x - b) for x, y in zip(xs, ys)) / F(len(ys))
    return m, b, r2_used, mae_used, m_ex, b_ex, r2_ex, mae_ex, source


constants = {}
for key in RACE_ORDER:
    m, b, r2_used, mae_used, m_ex, b_ex, r2_ex, mae_ex, source = fit_race(key)
    constants[key] = {
        "m": float(m),
        "b": float(b),
        "r2": float(r2_used),
        "mae": float(mae_used),
        "m_exact": float(m_ex),
        "b_exact": float(b_ex),
        "r2_exact": float(r2_ex),
        "source": source,
        "name": DISPLAY[key],
        "candidates": {"D": sorted(CAND[key]["D"]), "R": sorted(CAND[key]["R"])},
        "_m": m,
        "_b": b,
    }

counties = {}
for c in cs:
    mrow = {
        "pop": pop[c],
        "dreg": reg26[c][0],
        "treg": reg26[c][1],
        "D26": float(D26[c]),
        "dreg22": reg22[c][0],
        "treg22": reg22[c][1],
        "D22": float(D22[c]),
        "gov22_D": g22[c]["D"],
        "gov22_R": g22[c]["R"],
        "gov22_T": g22[c]["T"],
        "gov22_S": float(F(100 * g22[c]["D"], g22[c]["T"]) - D22[c]),
        "gov22_V": float(F(100 * g22[c]["D"], g22[c]["T"])),
    }
    for key in RACE_ORDER:
        d, r, t = V[c][key]["D"], V[c][key]["R"], V[c][key]["T"]
        S = F(100 * d, t) - D26[c]
        m, b = constants[key]["_m"], constants[key]["_b"]
        fit = m * D26[c] / 100 + b
        resid = S - fit
        pts = resid + b
        exact = pts * t / 100
        raw = half_up(exact)
        I = max(0, min(raw, d))
        Da, Ra = d - I, r + I
        T2 = t - I
        mrow[key] = {
            "D": d,
            "R": r,
            "T": t,
            "S": float(S),
            "fit": float(fit),
            "resid": float(resid),
            "pts": float(pts),
            "exact": float(exact),
            "raw": int(raw),
            "I": int(I),
            "win_b": "D" if d > r else ("R" if r > d else "TIE"),
            "win_a": "D" if Da > Ra else ("R" if Ra > Da else "TIE"),
            "mb": float(F(100 * (d - r), t)),
            "ma": float(F(100 * (Da - Ra), t)),
            "ma_sub": float(F(100 * ((d - I) - r), T2)) if T2 else 0.0,
            "mbv": d - r,
            "mav": Da - Ra,
            "mav_sub": (d - I) - r,
            "T_sub": T2,
        }
    counties[c] = mrow


def summarize(key):
    L = [counties[c][key] for c in cs]
    D = sum(x["D"] for x in L)
    R = sum(x["R"] for x in L)
    T = sum(x["T"] for x in L)
    I = sum(x["I"] for x in L)
    unclamped = sum(x["raw"] for x in L)
    unclamped_exact = sum(x["exact"] for x in L)
    n_pos = sum(1 for x in L if x["I"] > 0)
    n_clamp = sum(1 for x in L if x["raw"] < 0)
    n_zero = sum(1 for x in L if x["raw"] == 0)
    n_capped = sum(1 for x in L if x["raw"] > x["D"])
    flips = [c for c in cs if counties[c][key]["win_b"] != counties[c][key]["win_a"]]
    D2, T2 = D - I, T - I
    stay_d = [c for c in cs if counties[c][key]["win_b"] == "D" and counties[c][key]["win_a"] == "D"]
    before_d = sum(1 for x in L if x["win_b"] == "D")
    after_d = sum(1 for x in L if x["win_a"] == "D")
    top10 = sorted(cs, key=lambda c: (-counties[c][key]["I"], c))[:10]
    return {
        "D": D,
        "R": R,
        "T": T,
        "I": I,
        "unclamped": unclamped,
        "unclamped_exact": unclamped_exact,
        "n_pos": n_pos,
        "n_clamp": n_clamp,
        "n_zero": n_zero,
        "n_capped": n_capped,
        "margin_before_pts": float(F(100 * (D - R), T)),
        "margin_after_pts": float(F(100 * (D - I - (R + I)), T)),
        "margin_before_votes": D - R,
        "margin_after_votes": D - I - (R + I),
        "win_b": "D" if D > R else ("R" if R > D else "TIE"),
        "win_a": "D" if (D - I) > (R + I) else ("R" if (R + I) > (D - I) else "TIE"),
        "sub_D": D2,
        "sub_R": R,
        "sub_T": T2,
        "sub_margin_pts": float(F(100 * (D2 - R), T2)),
        "sub_margin_votes": D2 - R,
        "sub_win": "D" if D2 > R else ("R" if R > D2 else "TIE"),
        "flips": flips,
        "stay_d": stay_d,
        "n_before_d": before_d,
        "n_after_d": after_d,
        "top10": [{"county": c, "I": counties[c][key]["I"]} for c in top10],
    }


# strip private Fraction keys from constants before save
constants_out = {}
for k, v in constants.items():
    constants_out[k] = {kk: vv for kk, vv in v.items() if not kk.startswith("_")}

summary = {k: summarize(k) for k in RACE_ORDER}

xs22 = [D22[c] / 100 for c in cs]
ys22 = [F(100 * g22[c]["D"], g22[c]["T"]) - D22[c] for c in cs]
m22, b22, r2_22, mae22 = ols_fraction(xs22, ys22)
historical = {
    "gov_2022": {
        "m_exact": float(m22),
        "b_exact": float(b22),
        "r2": float(r2_22),
        "mae": float(mae22),
        "m_4dp": float(r4(m22)),
        "b_4dp": float(r4(b22)),
        "published": {"m": 40.1640, "b": 11.1047, "r2": 0.3044},
    },
    "gov_2018": {
        "status": "unavailable",
        "reason": (
            "A full 2018 surplus-line fit was not computed. Party-registration "
            "by county for 2018 is not among the raw files on this computer, and "
            "the Kansas SOS site returns HTTP 403 to this computer. The 2018 "
            "Governor precinct workbook is on hand, but the Wyandotte tab is a "
            "placeholder directing the reader to contact the SOS, so even the "
            "vote file is incomplete for all 105 counties."
        ),
    },
}

BASELINE = ["Wyandotte", "Douglas", "Johnson", "Shawnee"]


def mean(xs):
    return float(sum(xs) / len(xs))


sat = {}
for label, members in {
    "baseline_four": BASELINE,
    "other_101": [c for c in cs if c not in BASELINE],
    "wyandotte_douglas": ["Wyandotte", "Douglas"],
    "johnson_shawnee": ["Johnson", "Shawnee"],
}.items():
    s22 = [counties[c]["gov22_S"] for c in members]
    s26 = [counties[c]["gov"]["S"] for c in members]
    I = [counties[c]["gov"]["I"] for c in members]
    sat[label] = {
        "n": len(members),
        "members": members if len(members) <= 4 else None,
        "mean_S_2022": mean(s22),
        "mean_S_2026": mean(s26),
        "mean_dS": mean(s26) - mean(s22),
        "sum_I_gov": sum(I),
        "n_I_pos": sum(1 for x in I if x > 0),
        "n_clamped": sum(1 for c in members if counties[c]["gov"]["raw"] < 0),
    }
sat["per_county"] = {
    c: {
        "S_2022": counties[c]["gov22_S"],
        "S_2026": counties[c]["gov"]["S"],
        "dS": counties[c]["gov"]["S"] - counties[c]["gov22_S"],
        "D22": counties[c]["D22"],
        "D26": counties[c]["D26"],
        "V22": counties[c]["gov22_V"],
        "V26": float(F(100 * counties[c]["gov"]["D"], counties[c]["gov"]["T"])),
        "I_gov": counties[c]["gov"]["I"],
        "raw_gov": counties[c]["gov"]["raw"],
        "resid_gov": counties[c]["gov"]["resid"],
    }
    for c in BASELINE
}

out = {
    "pad_definition": (
        "Locked-page offset b in S = m·(D/100) + offset. "
        "residual + pad = actual S − m·(D/100)."
    ),
    "kansas_constant": {"m": 67.6004, "b": 6.3014, "race": "Governor", "year": "2026 unofficial"},
    "constants": constants_out,
    "counties": counties,
    "summary": summary,
    "historical": historical,
    "saturation": sat,
    "notes": {
        "year_2026": "unofficial until December 1, 2026 certification; SOS update 11/08/2026",
        "denominator": "race total votes, never ballots cast",
        "registration": "actual Kansas SOS Democratic registration share",
        "cvr": "Cast vote record (CVR) access may be blocked; this analysis does not use CVRs.",
        "removal_primary": "transfer: move I votes from Democrat to Republican; race total unchanged",
        "removal_secondary": "subtract-only: remove I from Democratic votes and from the race total",
    },
}

assert summary["gov"]["I"] == 71703, summary["gov"]["I"]
assert summary["ag"]["I"] == 74243, summary["ag"]["I"]

json.dump(out, open(OUT, "w"), indent=1)
print("wrote", OUT)
for k in RACE_ORDER:
    s = summary[k]
    print(
        k,
        "m",
        constants_out[k]["m"],
        "b",
        constants_out[k]["b"],
        "R2",
        round(constants_out[k]["r2"], 4),
        "I",
        s["I"],
        "npos",
        s["n_pos"],
        "nclamp",
        s["n_clamp"],
        "before",
        s["win_b"],
        round(s["margin_before_pts"], 2),
        "afterTR",
        s["win_a"],
        round(s["margin_after_pts"], 2),
        "afterSUB",
        s["sub_win"],
        round(s["sub_margin_pts"], 2),
        "flips",
        s["flips"],
    )
print("hist 2022", historical["gov_2022"])
