"""Pass 1 of the Kansas 2026* reverse analysis.
BeautifulSoup HTML parse, pandas registration/population, numpy OLS.
Independent of pass 2. Injection = residual + offset = S - m·D/100,
votes = pts/100 × race total, negatives clamped to 0.
"""
from __future__ import annotations

import glob
import json
import os
from fractions import Fraction as F

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

ENT = "/workspace/kansas-wiki/verification/ent_refetch_20261119/"
RAW = "/workspace/kansas/raw/"
OUT = "/workspace/kansas-reverse/verification/pass1.json"

HTML_TITLE = {
    "sen": "United States Senate",
    "gov": "Governor / Lt. Governor",
    "sos": "Secretary of State",
    "ag": "Attorney General",
    "treas": "State Treasurer",
    "ins": "Commissioner of Insurance",
}
RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
LOCKED = {"gov": (F("67.6004"), F("6.3014")), "ag": (F("67.5582"), F("6.4993"))}


def canon(s: str) -> str:
    s = str(s).strip().title().replace("Mcpherson", "McPherson")
    return s


def half_up(q: F) -> int:
    s = -1 if q < 0 else 1
    return int(s * ((abs(q) * 2 + 1) // 2))


def r4(q: F) -> F:
    return F(half_up(q * 10000), 10000)


# ----- 2026 unofficial county results -----
V = {}
CAND = {k: {"D": set(), "R": set()} for k in HTML_TITLE}
for path in sorted(glob.glob(ENT + "*.html")):
    county = canon(os.path.basename(path)[:-5])
    pane = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser").find(id="party-county-all")
    V[county] = {}
    for race in pane.find_all("div", class_="race"):
        title = race.find("h3").get_text(strip=True)
        key = next((k for k, t in HTML_TITLE.items() if t == title), None)
        if not key:
            continue
        rows = {}
        for row in race.find("div", class_="race-candidate-list").find_all("div", class_="row", recursive=False):
            ps = [p.get_text(strip=True) for p in row.find_all("p")]
            if len(ps) == 5:
                rows[ps[0]] = int(ps[1].replace(",", ""))
        d = sum(v for n, v in rows.items() if n.startswith("D-"))
        r = sum(v for n, v in rows.items() if n.startswith("R-"))
        t = sum(rows.values())
        V[county][key] = {"D": d, "R": r, "T": t, "candidates": rows}
        for n in rows:
            if n.startswith("D-"):
                CAND[key]["D"].add(n)
            if n.startswith("R-"):
                CAND[key]["R"].add(n)
assert len(V) == 105
assert all(all(k in V[c] for k in HTML_TITLE) for c in V)

# ----- registration & population -----
r26 = pd.read_excel(RAW + "10-2026-Voter-Registration-Numbers-by-County.xlsx", sheet_name="By County")
r26 = r26[r26.County != "Grand Total"].dropna(subset=["County"])
r26 = r26.assign(c=r26.County.map(canon)).set_index("c")
pop = pd.read_csv(RAW + "co-est2025-alldata.csv", encoding="latin-1")
pop = pop[(pop.STATE == 20) & (pop.COUNTY > 0)]
pop = pop.assign(c=pop.CTYNAME.str.replace(" County", "").map(canon)).set_index("c").POPESTIMATE2025
assert set(V) == set(r26.index) == set(pop.index)
assert (int(r26.Democratic.sum()), int(r26.Total.sum())) == (521669, 2027520)

# 2022 registration + governor (for historical / saturation)
r22 = pd.read_excel(RAW + "11-2022-Voter-Registration-Numbers-by-County.xlsx")
# discover sheet/cols
if "Jurisdiction" in r22.columns:
    ck, dk, tk = "Jurisdiction", "Democratic", "Grand Total"
else:
    # first sheet already
    ck = [c for c in r22.columns if "urisd" in str(c).lower() or str(c) == "County"][0]
    dk, tk = "Democratic", [c for c in r22.columns if "Grand" in str(c) or c == "Total"][0]
r22 = r22[r22[ck].notna() & (r22[ck].astype(str).str.strip() != "Grand Total")]
r22 = r22.assign(c=r22[ck].map(canon)).set_index("c")
assert (int(r22[dk].sum()), int(r22[tk].sum())) == (523317, 1975535)


def parse_2022_governor():
    import openpyxl

    path = RAW + "2022-General-Election-Governor-Results-By-Precinct.xlsx"
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Governor"]
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    ci = {n: i for i, n in enumerate(hdr)}
    out = {}
    for row in rows:
        if row[ci["County"]] is None:
            continue
        c = canon(row[ci["County"]])
        o = out.setdefault(c, {"D": 0, "R": 0, "T": 0})
        v = int(row[ci["Votes"]] or 0)
        o["T"] += v
        party = str(row[ci["Party"]]).strip()
        if party == "Democratic":
            o["D"] += v
        elif party == "Republican":
            o["R"] += v
    # big-4 countywide tabs overwrite
    wb2 = openpyxl.load_workbook(path, read_only=True, data_only=True)
    keys = ("kelly", "schmidt", "cordell", "pyle")
    for sh in ["JOHNSON", "SEDGWICK", "SHAWNEE", "WYANDOTTE"]:
        rows = list(wb2[sh].iter_rows(values_only=True))
        tot = [r for r in rows if r[1] is not None and "COUNTY TOTALS" in str(r[1]).upper()][0]
        hdr = [" ".join(str(rows[i][j]).lower() for i in range(min(3, len(rows)))) for j in range(len(rows[0]))]
        D = R = T = 0
        for j, hh in enumerate(hdr):
            if any(k in hh for k in keys):
                val = int(tot[j])
                T += val
                if "kelly" in hh:
                    D += val
                if "schmidt" in hh:
                    R += val
        out[canon(sh)] = {"D": D, "R": R, "T": T}
    return out


g22 = parse_2022_governor()
assert set(g22) == set(V)
assert sum(v["D"] for v in g22.values()) == 499849

# ----- OLS and per-county injection -----
cs = sorted(V)
D26 = {c: F(100 * int(r26.loc[c, "Democratic"]), int(r26.loc[c, "Total"])) for c in cs}
D22 = {c: F(100 * int(r22.loc[c, dk]), int(r22.loc[c, tk])) for c in cs}


def ols(xs, ys):
    N = len(xs)
    X = np.array([float(x) for x in xs], dtype=float)
    Y = np.array([float(y) for y in ys], dtype=float)
    # S = m * (D/100) + b  ; xs are D/100
    A = np.vstack([X, np.ones(N)]).T
    m, b = np.linalg.lstsq(A, Y, rcond=None)[0]
    yhat = m * X + b
    sse = float(np.sum((Y - yhat) ** 2))
    sst = float(np.sum((Y - Y.mean()) ** 2))
    r2 = 1 - sse / sst if sst else 0.0
    mae = float(np.mean(np.abs(Y - yhat)))
    return float(m), float(b), r2, mae


def fit_race(key):
    xs = [D26[c] / 100 for c in cs]
    ys = [F(100 * V[c][key]["D"], V[c][key]["T"]) - D26[c] for c in cs]
    m_ex, b_ex, r2, mae = ols(xs, ys)
    if key in LOCKED:
        m, b = LOCKED[key]
        # R² of the locked/stated constants
        X = np.array([float(x) for x in xs])
        Y = np.array([float(y) for y in ys])
        yhat = float(m) * X + float(b)
        sse = float(np.sum((Y - yhat) ** 2))
        sst = float(np.sum((Y - Y.mean()) ** 2))
        r2_used = 1 - sse / sst if sst else 0.0
        mae_used = float(np.mean(np.abs(Y - yhat)))
        source = "locked" if key == "gov" else "stated_ag_fit"
        return m, b, r2_used, mae_used, m_ex, b_ex, r2, source
    m, b = r4(F(str(m_ex)) if False else F(m_ex).limit_denominator()), r4(F(b_ex).limit_denominator())
    # Use exact floats rounded half-up via Fraction of the numpy value at high precision
    m = r4(F(int(round(m_ex * 1e12)), 10**12))
    b = r4(F(int(round(b_ex * 1e12)), 10**12))
    # Actually: convert numpy float through decimal-like half-up at 4 places
    def r4f(x):
        return r4(F(int(round(x * 1e12)), 10**12))
    m, b = r4f(m_ex), r4f(b_ex)
    X = np.array([float(x) for x in xs])
    Y = np.array([float(y) for y in ys])
    yhat = float(m) * X + float(b)
    sse = float(np.sum((Y - yhat) ** 2))
    sst = float(np.sum((Y - Y.mean()) ** 2))
    r2_used = 1 - sse / sst if sst else 0.0
    mae_used = float(np.mean(np.abs(Y - yhat)))
    return m, b, r2_used, mae_used, m_ex, b_ex, r2, "fitted_4dp"


constants = {}
for key in RACE_ORDER:
    m, b, r2_used, mae_used, m_ex, b_ex, r2_ex, source = fit_race(key)
    constants[key] = {
        "m": float(m),
        "b": float(b),
        "r2": r2_used,
        "mae": mae_used,
        "m_exact": m_ex,
        "b_exact": b_ex,
        "r2_exact": r2_ex,
        "source": source,
        "name": {
            "sen": "United States Senate",
            "gov": "Governor",
            "sos": "Secretary of State",
            "ag": "Attorney General",
            "treas": "State Treasurer",
            "ins": "Commissioner of Insurance",
        }[key],
        "candidates": {
            "D": sorted(CAND[key]["D"]),
            "R": sorted(CAND[key]["R"]),
        },
    }

counties = {}
for c in cs:
    row = {
        "pop": int(pop[c]),
        "dreg": int(r26.loc[c, "Democratic"]),
        "treg": int(r26.loc[c, "Total"]),
        "D26": float(D26[c]),
        "dreg22": int(r22.loc[c, dk]),
        "treg22": int(r22.loc[c, tk]),
        "D22": float(D22[c]),
        "gov22_D": g22[c]["D"],
        "gov22_R": g22[c]["R"],
        "gov22_T": g22[c]["T"],
    }
    # 2022 governor surplus
    row["gov22_S"] = float(F(100 * g22[c]["D"], g22[c]["T"]) - D22[c])
    row["gov22_V"] = float(F(100 * g22[c]["D"], g22[c]["T"]))
    for key in RACE_ORDER:
        d, r, t = V[c][key]["D"], V[c][key]["R"], V[c][key]["T"]
        S = F(100 * d, t) - D26[c]
        m = F(str(constants[key]["m"])) if key in LOCKED else F(constants[key]["m"]).limit_denominator()
        # use exact 4-decimal fractions
        m = F(int(round(constants[key]["m"] * 10000)), 10000)
        b = F(int(round(constants[key]["b"] * 10000)), 10000)
        fit = m * D26[c] / 100 + b
        resid = S - fit
        pts = resid + b  # = S - m*D/100
        exact = pts * t / 100
        raw = half_up(exact)
        I = max(0, min(raw, d))
        Da, Ra = d - I, r + I
        # subtract-only (D-I, T-I, R unchanged)
        T2 = t - I
        mb = F(100 * (d - r), t)
        ma_tr = F(100 * (Da - Ra), t)
        ma_sub = F(100 * ((d - I) - r), T2) if T2 else F(0)
        row[key] = {
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
            "mb": float(mb),
            "ma": float(ma_tr),
            "ma_sub": float(ma_sub),
            "mbv": d - r,
            "mav": Da - Ra,
            "mav_sub": (d - I) - r,
            "T_sub": T2,
        }
    counties[c] = row


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
    # subtract-only statewide
    D2, T2 = D - I, T - I
    stay_d = [c for c in cs if counties[c][key]["win_b"] == "D" and counties[c][key]["win_a"] == "D"]
    stay_r = [c for c in cs if counties[c][key]["win_b"] == "R" and counties[c][key]["win_a"] == "R"]
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


summary = {k: summarize(k) for k in RACE_ORDER}

# ----- 2022 governor historical fit -----
xs22 = [D22[c] / 100 for c in cs]
ys22 = [F(100 * g22[c]["D"], g22[c]["T"]) - D22[c] for c in cs]
m22, b22, r2_22, mae22 = ols(xs22, ys22)
m22r, b22r = r4(F(int(round(m22 * 1e12)), 10**12)), r4(F(int(round(b22 * 1e12)), 10**12))
historical = {
    "gov_2022": {
        "m_exact": m22,
        "b_exact": b22,
        "r2": r2_22,
        "mae": mae22,
        "m_4dp": float(m22r),
        "b_4dp": float(b22r),
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
# per-baseline-county detail
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
    "constants": constants,
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

# sanity vs KEA-12
assert summary["gov"]["I"] == 71703, summary["gov"]["I"]
assert summary["ag"]["I"] == 74243, summary["ag"]["I"]

json.dump(out, open(OUT, "w"), indent=1)
print("wrote", OUT)
for k in RACE_ORDER:
    s = summary[k]
    print(
        k,
        "m",
        constants[k]["m"],
        "b",
        constants[k]["b"],
        "R2",
        round(constants[k]["r2"], 4),
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
print("sat baseline", sat["baseline_four"])
print("sat other", {k: sat["other_101"][k] for k in sat["other_101"] if k != "members"})
print("sat per county", sat["per_county"])
