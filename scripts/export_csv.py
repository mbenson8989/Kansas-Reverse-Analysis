"""Export population-sorted county CSVs, a combined master, summaries, and top-10 tables."""
import csv
import json
from pathlib import Path

P = json.load(open("/workspace/kansas-reverse/verification/pass2.json"))
OUT = Path("/workspace/kansas-reverse/data")
OUT.mkdir(parents=True, exist_ok=True)

RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
SLUG = {
    "sen": "united_states_senate",
    "gov": "governor",
    "sos": "secretary_of_state",
    "ag": "attorney_general",
    "treas": "state_treasurer",
    "ins": "commissioner_of_insurance",
}

counties = P["counties"]
rows_by_county = []
for c, v in counties.items():
    rec = {
        "county": c,
        "population_2025": v["pop"],
        "dem_reg_2026": v["dreg"],
        "total_reg_2026": v["treg"],
        "dem_reg_share_pct": round(v["D26"], 4),
    }
    for race in RACE_ORDER:
        x = v[race]
        rec.update({
            f"{race}_D": x["D"],
            f"{race}_R": x["R"],
            f"{race}_T": x["T"],
            f"{race}_surplus_S": round(x["S"], 4),
            f"{race}_fitted_S": round(x["fit"], 4),
            f"{race}_residual": round(x["resid"], 4),
            f"{race}_injection_pts": round(x["pts"], 4),
            f"{race}_injected_votes_unclamped": x["raw"],
            f"{race}_injected_votes_I": x["I"],
            f"{race}_winner_before": x["win_b"],
            f"{race}_margin_before_pts": round(x["mb"], 2),
            f"{race}_margin_before_votes": x["mbv"],
            f"{race}_winner_after_transfer": x["win_a"],
            f"{race}_margin_after_transfer_pts": round(x["ma"], 2),
            f"{race}_margin_after_transfer_votes": x["mav"],
            f"{race}_flips": "YES" if x["win_b"] != x["win_a"] else "",
            f"{race}_margin_after_subtract_pts": round(x["ma_sub"], 2),
            f"{race}_margin_after_subtract_votes": x["mav_sub"],
        })
    rows_by_county.append(rec)
rows_by_county.sort(key=lambda r: (-r["population_2025"], r["county"]))

# combined master
path = OUT / "master_all_races.csv"
with path.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows_by_county[0].keys()))
    w.writeheader()
    w.writerows(rows_by_county)

# per-race CSVs
for race in RACE_ORDER:
    fields = ["county", "population_2025", "dem_reg_2026", "total_reg_2026", "dem_reg_share_pct"]
    race_fields = [k for k in rows_by_county[0] if k.startswith(race + "_")]
    # write without the race_ prefix for readability
    out_fields = fields + [k[len(race) + 1:] for k in race_fields]
    path = OUT / f"county_{SLUG[race]}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        for r in rows_by_county:
            row = {k: r[k] for k in fields}
            for k in race_fields:
                row[k[len(race) + 1:]] = r[k]
            w.writerow(row)

# top-10
for race in RACE_ORDER:
    path = OUT / f"top10_{SLUG[race]}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["rank", "county", "population_2025", "injected_votes_I", "flips"])
        w.writeheader()
        items = sorted(counties.items(), key=lambda kv: (-kv[1][race]["I"], kv[0]))[:10]
        for i, (c, v) in enumerate(items, 1):
            w.writerow({
                "rank": i,
                "county": c,
                "population_2025": v["pop"],
                "injected_votes_I": v[race]["I"],
                "flips": "YES" if v[race]["win_b"] != v[race]["win_a"] else "",
            })

# statewide summary
path = OUT / "statewide_summary.csv"
fields = [
    "race_key", "race_name", "m", "b", "r2", "constant_source",
    "dem_votes", "rep_votes", "total_votes",
    "injected_votes_I", "injected_unclamped", "counties_I_gt_0", "counties_clamped",
    "winner_before", "margin_before_pts", "margin_before_votes",
    "winner_after_transfer", "margin_after_transfer_pts", "margin_after_transfer_votes",
    "winner_after_subtract", "margin_after_subtract_pts", "margin_after_subtract_votes",
    "statewide_flips_transfer", "county_flips_transfer",
]
with path.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for race in RACE_ORDER:
        s, c = P["summary"][race], P["constants"][race]
        w.writerow({
            "race_key": race,
            "race_name": c["name"],
            "m": c["m"],
            "b": c["b"],
            "r2": round(c["r2"], 4),
            "constant_source": c["source"],
            "dem_votes": s["D"],
            "rep_votes": s["R"],
            "total_votes": s["T"],
            "injected_votes_I": s["I"],
            "injected_unclamped": s["unclamped"],
            "counties_I_gt_0": s["n_pos"],
            "counties_clamped": s["n_clamp"],
            "winner_before": s["win_b"],
            "margin_before_pts": round(s["margin_before_pts"], 2),
            "margin_before_votes": s["margin_before_votes"],
            "winner_after_transfer": s["win_a"],
            "margin_after_transfer_pts": round(s["margin_after_pts"], 2),
            "margin_after_transfer_votes": s["margin_after_votes"],
            "winner_after_subtract": s["sub_win"],
            "margin_after_subtract_pts": round(s["sub_margin_pts"], 2),
            "margin_after_subtract_votes": s["sub_margin_votes"],
            "statewide_flips_transfer": "YES" if s["win_b"] != s["win_a"] else "",
            "county_flips_transfer": "; ".join(s["flips"]),
        })

print("wrote CSVs", len(list(OUT.glob("*.csv"))))
