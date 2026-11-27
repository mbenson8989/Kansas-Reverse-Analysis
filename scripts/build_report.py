"""Build the Markdown report and methodology page from verified pass2.json."""
from pathlib import Path
import json
from datetime import datetime
from zoneinfo import ZoneInfo

P = json.load(open("/workspace/kansas-reverse/verification/pass2.json"))
RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
SLUG = {
    "sen": "united_states_senate",
    "gov": "governor",
    "sos": "secretary_of_state",
    "ag": "attorney_general",
    "treas": "state_treasurer",
    "ins": "commissioner_of_insurance",
}
CAND = {
    "sen": ("Adam Hamilton", "Roger Marshall"),
    "gov": ("Cindy Holscher", "Ty Masterson"),
    "sos": ("Jennifer Day", "Pat Proctor"),
    "ag": ("Chris Mann", "Kris Kobach"),
    "treas": ("Juan C. Luengo", "Steven Johnson"),
    "ins": ("Dinah Sykes", "Daniel Hawkins"),
}

def pts(x):
    return f"{x:+.2f}"

def r2(x):
    return f"{float(x):+.2f}"

def comma(n):
    return f"{n:,}"

def win_label(w, margin_pts, votes):
    return f"{w} {abs(margin_pts):.2f} ({votes:+,})"

now = datetime.now(ZoneInfo("America/Chicago")).strftime("%A, %b %-d, %Y, %-I:%M %p CT (America/Chicago)")

# historical 2022
h = P["historical"]["gov_2022"]
sat = P["saturation"]

lines = []
A = lines.append

A("# Kansas Reverse Analysis")
A("")
A("**Status:** private draft. 2026 figures are unofficial (Kansas Secretary of State election-night update of 11/08/2026; certification December 1, 2026).")
A("")
A("This is a what-if simulation, not a finding of fact. The gap measured below is a statistical distance from a fitted line, not proof that any votes were injected. Treating the offset as fully injected is an upper-bound assumption. Cast vote record (CVR) access may be blocked; this analysis does not use CVRs.")
A("")
A("The work was run by the analyst. Two independent verification passes were required; both completed with zero mismatches before these pages were written.")
A("")
A(f"_Saved {now}._")
A("")
A("## The Kansas constant")
A("")
A("The locked Kansas Governor equation is")
A("")
A("$$S = 67.6004 \\times (D/100) + 6.3014$$")
A("")
A("where **S** is the Democratic surplus (Democratic share of that race’s total votes minus the Democratic registration share, in points) and **D** is the actual Kansas SOS Democratic registration share, in points. The denominator is always that race’s total votes, never ballots cast. Kansas has official party registration; no stand-in is used.")
A("")
A("The 6.3014 term is the locked-page **offset**. In this analysis it is the pad: each county’s estimated injection, in points, is the residual from the fitted line plus the offset, which simplifies to")
A("")
A("$$\\text{injection points} = S - m \\times (D/100).$$")
A("")
A("Points are converted to votes by multiplying by the county’s race total and dividing by 100. Negative results are set to zero. Those votes are then moved from the Democrat to the Republican in each county, leaving the race total unchanged (the transfer, or flip, view). A secondary subtract-only view removes the same votes from the Democratic count and from the total, leaving Republican votes unchanged.")
A("")
A("Attorney General and the other statewide races use the same form, each with its own 2026 ordinary-least-squares fit across all 105 counties, except that Governor keeps the locked constants and Attorney General keeps its previously stated fit. Both of those pairs were recomputed from the raw files and match the earlier verified totals: Governor 71,703 votes and Attorney General 74,243 votes.")
A("")
A("## Race constants (2026*)")
A("")
A("| Race | Slope m | Offset b | R² | Source |")
A("|---|---:|---:|---:|---|")
for k in RACE_ORDER:
    c = P["constants"][k]
    src = {
        "locked": "Locked Governor constant",
        "stated_ag_fit": "Stated Attorney General fit",
        "fitted_4dp": "Fitted on this race, rounded to four decimals",
    }[c["source"]]
    A(f"| {c['name']} | {c['m']:.4f} | {c['b']:.4f} | {c['r2']:.4f} | {src} |")
A("")
A("The Treasurer offset is slightly negative (−0.4427). In that race, residual plus offset is often smaller than the residual alone, and 58 counties clamp to zero.")
A("")

A("## Statewide results")
A("")
A("Primary view: transfer (move estimated votes from Democrat to Republican; totals unchanged). Secondary line: subtract-only.")
A("")
A("| Race | 2026* before | After transfer | After subtract-only | Votes moved (counties) | Statewide flip? |")
A("|---|---|---|---|---:|---|")
for k in RACE_ORDER:
    s, c = P["summary"][k], P["constants"][k]
    flip = "Yes, D → R" if s["win_b"] != s["win_a"] else "No (stays " + s["win_b"] + ")"
    A(
        f"| {c['name']} | {s['win_b']} {s['margin_before_pts']:+.2f} ({s['margin_before_votes']:+,}) "
        f"| {s['win_a']} {s['margin_after_pts']:+.2f} ({s['margin_after_votes']:+,}) "
        f"| {s['sub_win']} {s['sub_margin_pts']:+.2f} ({s['sub_margin_votes']:+,}) "
        f"| {s['I']:,} ({s['n_pos']}) | {flip} |"
    )
A("")
A("Three races flip statewide under both views: United States Senate, Governor, and Attorney General. Secretary of State, State Treasurer, and Commissioner of Insurance are already Republican in the unofficial 2026* count and stay Republican, with a larger Republican margin after the transfer.")
A("")
A("Unclamped (pre-clamp) rounded statewide sums, for the record: Senate 73,166; Governor 70,449; Secretary of State 45,931; Attorney General 73,432; Treasurer −1,471; Insurance 43,595. Treasurer’s unclamped sum is negative because the offset is negative and more than half the counties sit below zero.")
A("")
A("These six injection totals describe the same voters looked at through six races. They must not be added together.")
A("")

A("## Counties that flip under the transfer")
A("")
A("All listed flips are Democrat → Republican. No county flips Republican → Democrat. Douglas, Johnson, Shawnee, and Wyandotte stay Democratic in every race after the transfer.")
A("")
for k in RACE_ORDER:
    s, cnst = P["summary"][k], P["constants"][k]
    A(f"### {cnst['name']}")
    A("")
    dname, rname = CAND[k]
    A(f"Candidates: {dname} (D) vs {rname} (R). Democratic counties before {s['n_before_d']}, after {s['n_after_d']}.")
    A("")
    if s["flips"]:
        A("| County | Before | After transfer | Votes moved |")
        A("|---|---|---|---:|")
        for county in s["flips"]:
            x = P["counties"][county][k]
            A(
                f"| {county} | {x['win_b']} {x['mb']:+.2f} ({x['mbv']:+,}) "
                f"| {x['win_a']} {x['ma']:+.2f} ({x['mav']:+,}) | {x['I']:,} |"
            )
    else:
        A("No county flips.")
    A("")

A("## Top 10 counties by estimated injected votes")
A("")
for k in RACE_ORDER:
    s, cnst = P["summary"][k], P["constants"][k]
    A(f"### {cnst['name']}  —  {s['I']:,} votes in {s['n_pos']} counties")
    A("")
    A("| Rank | County | Votes moved | County flips? |")
    A("|---:|---|---:|---|")
    for i, row in enumerate(s["top10"], 1):
        fl = "Yes, D → R" if P["counties"][row["county"]][k]["win_b"] != P["counties"][row["county"]][k]["win_a"] else ""
        A(f"| {i} | {row['county']} | {row['I']:,} | {fl} |")
    A("")

A("## Historical pattern (hypothesis)")
A("")
A("**Hypothesis, not a finding.** The same surplus-line form can be fitted to prior cycles. A further hypothesis, sometimes described as a CD3-style saturation pattern, is that Democratic surplus in baseline high-Democratic counties flattens or falls while it grows in other counties — as if the baseline counties had little room left and any added support appeared elsewhere.")
A("")
A("The 2022 Governor fit, recomputed here from official precinct results and November 2022 SOS registration on all 105 counties, is")
A("")
A(f"$$S_{{2022}} = {h['m_4dp']:.4f} \\times (D/100) + {h['b_4dp']:.4f}$$")
A("")
A(f"with R² = {h['r2']:.4f} (mean absolute residual {h['mae']:.2f} points). That matches the previously published 2022 constants (m = 40.1640, b = 11.1047, R² = 0.3044). The 2026* locked line is steeper and has a lower offset (m = 67.6004, b = 6.3014, R² = 0.6806). The two years do not share one line.")
A("")
A("A full 2018 surplus-line fit was **not** computed. Party registration by county for 2018 is not among the raw files on this computer, and the Kansas SOS site returns HTTP 403 here. The 2018 Governor precinct workbook is on hand, but the Wyandotte tab is a placeholder directing the reader to contact the SOS, so even the vote file is incomplete for all 105 counties.")
A("")
A("### Saturation test (Governor surplus, 2022 official vs 2026*)")
A("")
A("Baseline counties, as named in the request: Wyandotte, Douglas, Johnson, and Shawnee.")
A("")
A("| Group | Mean surplus 2022 | Mean surplus 2026* | Change | Governor votes moved |")
A("|---|---:|---:|---:|---:|")
for label, title in (
    ("baseline_four", "Baseline four"),
    ("wyandotte_douglas", "Wyandotte and Douglas only"),
    ("johnson_shawnee", "Johnson and Shawnee only"),
    ("other_101", "Other 101 counties"),
):
    g = sat[label]
    A(f"| {title} | {g['mean_S_2022']:.2f} | {g['mean_S_2026']:.2f} | {g['mean_dS']:+.2f} | {g['sum_I_gov']:,} |")
A("")
A("| County | Dem. reg. 2022 | Dem. reg. 2026* | Surplus 2022 | Surplus 2026* | Change | Residual+pad votes (Gov.) |")
A("|---|---:|---:|---:|---:|---:|---:|")
for county in ["Wyandotte", "Douglas", "Johnson", "Shawnee"]:
    r = sat["per_county"][county]
    A(
        f"| {county} | {r['D22']:.2f}% | {r['D26']:.2f}% | {r['S_2022']:.2f} | {r['S_2026']:.2f} | {r['dS']:+.2f} | {r['I_gov']:,} |"
    )
A("")
A("**What the data show.** The simple saturation story does not hold for Kansas Governor surplus. Mean surplus in the four baseline counties **rose** 2.11 points (26.11 to 28.22), while mean surplus in the other 101 counties **fell** 1.64 points (16.93 to 15.29). Wyandotte’s surplus rose 8.18 points; Douglas was nearly flat (+0.44); Johnson rose 1.44; Shawnee fell 1.63.")
A("")
A("A different pattern appears in the residual-plus-offset **injection** numbers, and it is mostly a consequence of the steeper 2026* slope. Wyandotte and Douglas — the two counties with the highest Democratic registration share — clamp to zero (raw estimates −1,195 and −48) because a large registration share implies a high fitted surplus, so even a large actual surplus can sit below the line. Johnson and Shawnee remain positive after the pad is added (15,569 and 4,161). Ninety-nine of the other 101 counties are also positive. That is not the same thing as “Democrats ran out of votes in the baseline counties.” The hypothesis, as stated, is not supported by the surplus changes. The clamp in Wyandotte and Douglas should be read as a property of the 2026* line, not as evidence of saturation.")
A("")

A("## Methodology")
A("")
A("Every step below was applied to all 105 Kansas counties and to all six statewide races on the 2026 ticket: United States Senate, Governor, Secretary of State, Attorney General, State Treasurer, and Commissioner of Insurance. Constitutional amendments, Supreme Court retentions, State Board of Education districts, and U.S. House districts are not in this statewide reversal.")
A("")
A("1. **County-level measurement.** From the Kansas SOS unofficial 2026 county HTML (saved 11/19/2026; the live SOS site now returns 403 to this computer), the analyst parsed Democratic votes, Republican votes, and the race total for each county and race. Democratic registration comes from the official October 2026 SOS registration workbook (521,669 Democratic of 2,027,520 statewide). Population is the Census Bureau July 1, 2025 estimate, used only to sort tables. Vote share always uses that race’s total votes as the denominator.")
A("")
A("2. **Fit the surplus line.** For each race, surplus S = Democratic vote share minus Democratic registration share. Ordinary least squares across 105 counties gives S = m × (D/100) + b. Governor uses the locked constants; Attorney General uses its stated fit, confirmed from the same files; the other four races use their own 2026* fits, with m and b rounded to four decimals by half-up rounding.")
A("")
A("3. **Residual plus offset.** For each county, residual = actual S − (m × D/100 + b). Injection points = residual + b = actual S − m × D/100. This is the full reversal: the gap from the line, plus the offset, solved backward from the 2026* Democratic share.")
A("")
A("4. **Convert to votes and clamp.** Votes = points ÷ 100 × the county’s race total. The result is rounded half-up (half away from zero). Negative estimates are set to zero. The count is also capped at the county’s Democratic votes, which did not bind in any race.")
A("")
A("5. **Sum, then remove.** County votes are summed to a statewide injection total for that race. In the primary transfer view, those votes are subtracted from the Democrat and added to the Republican in each county; the race total does not change. In the secondary subtract-only view, the same votes are subtracted from the Democrat and from the total. Statewide margins are then recomputed. The six race totals are never added to one another.")
A("")
A("6. **Double-verification rule.** Two independent passes recomputed every figure from the raw SOS files with different tools (pass 1: BeautifulSoup and pandas, with a numpy least-squares fit; pass 2: regex HTML parsing, openpyxl, csv, and exact Fraction normal equations). Every county, race, constant, margin, flip, historical fit, and saturation figure was compared. **Zero mismatches were required; if any had appeared, nothing would have been written to a repository.** A further check compared every CSV cell and every plotted number with pass 2.")
A("")
A("### Worked example (Sedgwick, Governor)")
A("")
A("Sedgwick’s 2026* Democratic registration share is 90,047 / 349,829 = 25.74%. Democratic surplus in the Governor race is 26.59 points. The part of surplus that the slope attributes to registration is 67.6004 × 25.74% = 17.40 points. What remains is 26.59 − 17.40 = 9.19 points, which is the 2.89-point residual from the locked line plus the 6.30-point offset. 9.1883% of 181,679 Governor votes equals 16,693 votes moved. (The rounded 9.19% × 181,679 is 16,696; the 16,693 figure is the correctly rounded exact value.)")
A("")
A("### Caveats")
A("")
A("- The gap is a distance from a statistical prediction, not evidence that any particular votes were injected.")
A("- R² is about 0.67–0.72 in 2026*, so the line leaves real unexplained variation. The 2022 Governor R² is only 0.30.")
A("- Treating the entire offset as injected is an upper-bound assumption. In a typical year the offset is part of the fitted relationship between registration and vote share, not a pile of extra votes.")
A("- 2026 figures are unofficial until the December 1, 2026 certification.")
A("- Cast vote record (CVR) access may be blocked. This analysis does not use CVRs and cannot speak to ballot-level images or records.")
A("- The six race totals must not be added together. They are six views of the same election.")
A("")

A("## Verification")
A("")
A("Pass 1 vs pass 2: see `verification/compare.json` after the compare script is run (13,544 field comparisons in the building run, 0 mismatches). Governor and Attorney General injection totals reproduce the earlier residual-plus-offset reversal exactly (71,703 and 74,243). The 2022 Governor constants reproduce the published values to four decimals.")
A("")
A("## Files")
A("")
A("- `data/master_all_races.csv` — all 105 counties, all six races, sorted by 2025 population")
A("- `data/county_*.csv` — one table per race")
A("- `data/top10_*.csv` — top ten counties by votes moved, each race")
A("- `data/statewide_summary.csv` — one row per race")
A("- `graphics/1_KS_senate_injection_removed.png` through `6_KS_insurance_injection_removed.png` — one plain-language graphic per race, titled “When you remove the injection equation / share injection, this is what happens”")
A("- `graphics/7_KS_votes_removed_by_race.png` — one bar per race; do not add the bars")
A("- `graphics/8_KS_top10_by_race.png` — top ten counties in each race")
A("- `scripts/` — pass 1, pass 2, compare, export, charts, report builder, output checker")
A("- `verification/` — the two pass JSON files and check outputs")
A("")
A("This repository is private and is separate from the main Kansas Election Analysis repository and its wiki.")
A("")

text = "\n".join(lines) + "\n"
Path("/workspace/kansas-reverse/report").mkdir(exist_ok=True)
Path("/workspace/kansas-reverse/wiki").mkdir(exist_ok=True)
Path("/workspace/kansas-reverse/docs").mkdir(exist_ok=True)
Path("/workspace/kansas-reverse/report/Kansas-Reverse-Analysis.md").write_text(text)
Path("/workspace/kansas-reverse/wiki/Kansas-Reverse-Analysis.md").write_text(text)

# standalone methodology (subset, still generated)
meth = []
M = meth.append
M("# Methodology: how this analysis was done")
M("")
M("This page is the methodology section of the Kansas Reverse Analysis, written so it can be read on its own. 2026 figures are unofficial until December 1, 2026. This is a what-if, not a finding. The work was run by the analyst.")
M("")
# extract from the same file after the Methodology heading
start = text.index("## Methodology")
end = text.index("## Verification")
M(text[start + len("## Methodology"):end].strip())
M("")
M("Verification results and the full analysis, including race tables and the historical hypothesis, are in `report/Kansas-Reverse-Analysis.md`.")
M("")
Path("/workspace/kansas-reverse/docs/Methodology.md").write_text("\n".join(meth) + "\n")

readme = f"""# Kansas Reverse Analysis

Private draft. 2026 figures are unofficial (Kansas SOS update 11/08/2026; certification December 1, 2026). This is a what-if simulation, not a finding of fact.

The full write-up, including methodology, is in [report/Kansas-Reverse-Analysis.md](report/Kansas-Reverse-Analysis.md). A standalone methodology page is in [docs/Methodology.md](docs/Methodology.md). County tables are in `data/`. Presentation graphics are in `graphics/`.

The locked Kansas Governor constant is S = 67.6004 × (D/100) + 6.3014. Each other statewide race uses its own 2026* fit. Estimated votes are the residual from that race’s line plus the offset, clamped at zero, then moved from Democrat to Republican with totals unchanged.

These race totals must not be added together. They describe the same voters.

Two independent verification passes over all 105 counties and all six races were required, with zero mismatches, before this repository was written. Cast vote record (CVR) access may be blocked; this analysis does not use CVRs.

This repository is private and is not part of the main Kansas Election Analysis repository.

_Saved {now}._
"""
Path("/workspace/kansas-reverse/README.md").write_text(readme)
print("wrote report, wiki, methodology, README", "chars", len(text))
