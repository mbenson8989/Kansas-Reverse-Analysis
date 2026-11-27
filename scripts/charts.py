"""Presentation graphics for the Kansas reverse analysis. Values from pass2.json."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import Rectangle

FONT = "/usr/share/fonts/truetype/sand-box/google/Source Sans 3/SourceSans3-VariableFont_wght.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Source Sans 3", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

def fp(weight, size):
    return font_manager.FontProperties(fname=FONT, size=size, weight=weight)

NAVY, INK, MUTED = "#1b365d", "#1a1a1a", "#4a4a4a"
BLUE, RED, LINE, BG = "#1a56b8", "#b42318", "#d0cdc6", "#fbfaf7"

P = json.load(open("/workspace/kansas-reverse/verification/pass2.json"))
OUT = Path("/workspace/kansas-reverse/graphics")
OUT.mkdir(parents=True, exist_ok=True)

RACE_ORDER = ["sen", "gov", "sos", "ag", "treas", "ins"]
FILE_STEM = {
    "sen": "1_KS_senate_injection_removed",
    "gov": "2_KS_governor_injection_removed",
    "sos": "3_KS_secretary_of_state_injection_removed",
    "ag": "4_KS_attorney_general_injection_removed",
    "treas": "5_KS_treasurer_injection_removed",
    "ins": "6_KS_insurance_injection_removed",
}
TITLE = "When you remove the injection equation / share injection, this is what happens"
FOOT = (
    "2026 results unofficial (KS SOS 11/08/2026; certification Dec 1)  ·  "
    "Hypothetical what-if: the offset is treated as fully injected, an upper-bound assumption, not a finding."
)
CAND = {
    "sen": ("Adam Hamilton", "Roger Marshall"),
    "gov": ("Cindy Holscher", "Ty Masterson"),
    "sos": ("Jennifer Day", "Pat Proctor"),
    "ag": ("Chris Mann", "Kris Kobach"),
    "treas": ("Juan C. Luengo", "Steven Johnson"),
    "ins": ("Dinah Sykes", "Daniel Hawkins"),
}

def r2(x):
    return round(float(x) + 0.0, 2)

manifest = {"races": {}, "totals": {}}

def race_graphic(key):
    s = P["summary"][key]
    name = P["constants"][key]["name"]
    d_name, r_name = CAND[key]
    before = s["margin_before_pts"]
    after = s["margin_after_pts"]
    b_pts, a_pts = r2(before), r2(after)
    b_win, a_win = s["win_b"], s["win_a"]
    b_votes, a_votes = s["margin_before_votes"], s["margin_after_votes"]
    flipped = b_win != a_win

    fig = plt.figure(figsize=(19.20, 10.80), dpi=100, facecolor=BG)
    header = fig.add_axes([0, 0.88, 1, 0.12])
    header.set_xlim(0, 1)
    header.set_ylim(0, 1)
    header.axis("off")
    header.add_patch(Rectangle((0, 0), 1, 1, transform=header.transAxes, color=NAVY, zorder=0, clip_on=False))
    header.text(0.025, 0.68, TITLE, fontproperties=fp(700, 23), color="white", va="center", ha="left")
    header.text(0.025, 0.26, f"{name}  ·  unofficial 2026*", fontproperties=fp(400, 17), color="#d7deea", va="center", ha="left")

    ax = fig.add_axes([0.10, 0.28, 0.80, 0.52])
    ax.set_facecolor(BG)
    x = np.array([0, 1])
    w = 0.48
    colors = [BLUE if before > 0 else RED, BLUE if after > 0 else RED]
    ax.bar(x, [before, after], w, color=colors, zorder=3)
    ax.axhline(0, color=INK, lw=1.4, zorder=4)
    ax.axhspan(min(0, min(before, after) - 4), 0, color="#f8efee", zorder=0, lw=0)
    ax.set_xticks(x)
    ax.set_xticklabels(["Before", "After"], fontproperties=fp(700, 20), color=INK)
    ax.tick_params(axis="x", length=0, pad=8)
    ax.set_ylabel("Statewide margin, points\n(above 0 = Democratic lead)", fontproperties=fp(500, 14), color=MUTED)
    lo = min(before, after, 0) - 4.5
    hi = max(before, after, 0) + 4.5
    ax.set_ylim(lo, hi)
    ax.set_xlim(-0.7, 1.7)
    ax.tick_params(axis="y", colors=MUTED, length=0)
    for lab in ax.get_yticklabels():
        lab.set_fontproperties(fp(500, 13))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(LINE)
    ax.spines["bottom"].set_visible(False)
    ax.grid(axis="y", color="#ece8e0", zorder=0)
    ax.set_axisbelow(True)

    def annotate(i, pts_signed, win, votes, yval):
        # Winner-centric label: D +0.70 or R +12.40, plus D-minus-R vote margin
        lead = abs(pts_signed)
        if yval >= 0:
            va, y = "bottom", yval + 0.35
            color = BLUE
        else:
            va, y = "top", yval - 0.35
            color = RED
        ax.text(
            i, y, f"{win}  +{lead:.2f}\n({votes:+,})",
            ha="center", va=va, fontproperties=fp(700, 22), color=color, linespacing=1.25,
        )

    annotate(0, b_pts, b_win, b_votes, before)
    annotate(1, a_pts, a_win, a_votes, after)

    # outcome strip
    if flipped:
        outcome = f"Statewide outcome flips  {b_win}  →  {a_win}"
    else:
        outcome = f"Statewide outcome stays  {b_win}  (margin changes, no flip)"
    ax.text(0.5, 1.04, outcome, transform=ax.transAxes, ha="center", va="bottom",
            fontproperties=fp(700, 18), color=NAVY)

    mid = fig.add_axes([0, 0.115, 1, 0.13])
    mid.set_xlim(0, 1)
    mid.set_ylim(0, 1)
    mid.axis("off")
    mid.text(0.5, 0.72,
             "Before: unofficial 2026* result      ·      After: estimated gap votes moved from Democrat to Republican (totals unchanged)",
             fontproperties=fp(400, 13), color=MUTED, ha="center", va="center")
    mid.text(
        0.5, 0.32,
        f"Estimated injected votes moved  {s['I']:,}    in    {s['n_pos']} of 105 counties"
        f"      ·      {d_name}  (D)    vs    {r_name}  (R)",
        fontproperties=fp(600, 15), color=NAVY, ha="center", va="center",
    )

    foot = fig.add_axes([0, 0, 1, 0.10])
    foot.set_xlim(0, 1)
    foot.set_ylim(0, 1)
    foot.axis("off")
    foot.add_patch(Rectangle((0, 0.82), 1, 0.03, color=LINE, lw=0, transform=foot.transAxes, clip_on=False))
    foot.text(0.025, 0.42, FOOT, fontproperties=fp(400, 12), color=MUTED, ha="left", va="center")

    path = OUT / f"{FILE_STEM[key]}.png"
    fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
    plt.close()
    from PIL import Image
    im = Image.open(path)
    assert im.size == (1920, 1080), im.size
    manifest["races"][key] = {
        "path": str(path),
        "before_pts": before,
        "after_pts": after,
        "before_pts_disp": b_pts,
        "after_pts_disp": a_pts,
        "before_votes": b_votes,
        "after_votes": a_votes,
        "I": s["I"],
        "n_pos": s["n_pos"],
        "win_b": b_win,
        "win_a": a_win,
        "title": TITLE,
        "subtitle": f"{name}  ·  unofficial 2026*",
    }
    print("wrote", path)


for key in RACE_ORDER:
    race_graphic(key)

# ----- statewide injection totals (do NOT sum) -----
fig = plt.figure(figsize=(19.20, 10.80), dpi=100, facecolor=BG)
header = fig.add_axes([0, 0.88, 1, 0.12])
header.set_xlim(0, 1)
header.set_ylim(0, 1)
header.axis("off")
header.add_patch(Rectangle((0, 0), 1, 1, transform=header.transAxes, color=NAVY, zorder=0, clip_on=False))
header.text(0.025, 0.68, "Estimated injected votes by race", fontproperties=fp(700, 26), color="white", va="center")
header.text(
    0.025, 0.28,
    "One bar per race.  Do not add these bars together — they describe the same voters, not separate ballots.",
    fontproperties=fp(400, 16), color="#d7deea", va="center",
)

ax = fig.add_axes([0.22, 0.20, 0.72, 0.60])
ax.set_facecolor(BG)
names = [P["constants"][k]["name"] for k in RACE_ORDER]
vals = [P["summary"][k]["I"] for k in RACE_ORDER]
npos = [P["summary"][k]["n_pos"] for k in RACE_ORDER]
y = np.arange(len(RACE_ORDER))[::-1]
ax.barh(y, vals, color=NAVY, height=0.62, zorder=3)
ax.set_yticks([])
ax.set_xlim(0, max(vals) * 1.28)
ax.set_ylim(-0.7, 5.7)
for yi, name, val, n in zip(y, names, vals, npos):
    ax.text(-0.012, yi, name, transform=ax.get_yaxis_transform(), ha="right", va="center",
            fontproperties=fp(700, 16), color=INK)
    ax.text(val + max(vals) * 0.02, yi, f"{val:,}   in {n} counties", va="center", ha="left",
            fontproperties=fp(700, 15), color=NAVY)
ax.set_xlabel("Estimated injected votes  (residual + offset, negatives set to 0)", fontproperties=fp(500, 13), color=MUTED)
ax.tick_params(axis="x", colors=MUTED, labelsize=12)
for lab in ax.get_xticklabels():
    lab.set_fontproperties(fp(400, 12))
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_visible(False)
ax.spines["bottom"].set_color(LINE)
ax.grid(axis="x", color="#ece8e0", zorder=0)
ax.set_axisbelow(True)

foot = fig.add_axes([0, 0, 1, 0.12])
foot.set_xlim(0, 1)
foot.set_ylim(0, 1)
foot.axis("off")
foot.add_patch(Rectangle((0, 0.82), 1, 0.03, color=LINE, lw=0, transform=foot.transAxes, clip_on=False))
foot.text(
    0.025, 0.55,
    "These are six views of the same election, not six independent piles of votes.  A voter who is counted in the Governor bar is also in the Senate bar.",
    fontproperties=fp(600, 13), color=NAVY, ha="left", va="center",
)
foot.text(0.025, 0.22, FOOT, fontproperties=fp(400, 12), color=MUTED, ha="left", va="center")

path = OUT / "7_KS_votes_removed_by_race.png"
fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
plt.close()
from PIL import Image
im = Image.open(path)
assert im.size == (1920, 1080), im.size
manifest["totals"] = {"path": str(path), "values": {k: P["summary"][k]["I"] for k in RACE_ORDER}, "n_pos": {k: P["summary"][k]["n_pos"] for k in RACE_ORDER}}
print("wrote", path)

# ----- top-10 multi-panel -----
fig = plt.figure(figsize=(19.20, 10.80), dpi=100, facecolor=BG)
header = fig.add_axes([0, 0.90, 1, 0.10])
header.set_xlim(0, 1)
header.set_ylim(0, 1)
header.axis("off")
header.add_patch(Rectangle((0, 0), 1, 1, transform=header.transAxes, color=NAVY, zorder=0, clip_on=False))
header.text(0.025, 0.55, "Top 10 counties by estimated injected votes, each race",
            fontproperties=fp(700, 24), color="white", va="center")

positions = [
    [0.08, 0.50, 0.40, 0.36],
    [0.55, 0.50, 0.40, 0.36],
    [0.08, 0.08, 0.40, 0.36],
    [0.55, 0.08, 0.40, 0.36],
    # wait that's only 4. Use 2x3
]
# redo as 2x3
positions = []
for row in range(2):
    for col in range(3):
        positions.append([0.07 + col * 0.31, 0.12 + (1 - row) * 0.38, 0.28, 0.33])
# actually 2 rows x 3 cols with header leaving y 0 to 0.90
positions = []
for row in range(2):
    for col in range(3):
        left = 0.07 + col * 0.31
        bottom = 0.10 if row == 1 else 0.54
        positions.append([left, bottom, 0.28, 0.30])

ORANGE = "#e8590c"
for axp, key in zip(positions, RACE_ORDER):
    ax = fig.add_axes(axp)
    ax.set_facecolor(BG)
    items = sorted(P["counties"].items(), key=lambda kv: (-kv[1][key]["I"], kv[0]))[:10]
    names = [c for c, _ in items]
    vals = [v[key]["I"] for _, v in items]
    flips = [v[key]["win_b"] != v[key]["win_a"] for _, v in items]
    y = np.arange(10)[::-1]
    colors = [ORANGE if f else "#1f5fbf" for f in flips]
    ax.barh(y, vals, color=colors, height=0.72, zorder=3)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontproperties=fp(600, 9), color=INK)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(vals) * 1.38 if vals else 1)
    for yi, val, fl in zip(y, vals, flips):
        ax.text(val + max(vals) * 0.03, yi, f"{val:,}", va="center", ha="left",
                fontproperties=fp(600, 8), color="#9a3412" if fl else NAVY)
    ax.set_title(P["constants"][key]["name"], fontproperties=fp(700, 13), color=NAVY, loc="left", pad=4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_color(LINE)
    ax.tick_params(axis="x", labelsize=8, colors=MUTED)
    ax.grid(axis="x", color="#ece8e0", zorder=0)
    ax.set_axisbelow(True)

foot = fig.add_axes([0, 0, 1, 0.10])
foot.set_xlim(0, 1)
foot.set_ylim(0, 1)
foot.axis("off")
foot.text(0.025, 0.62, "Orange = the county flips Democrat → Republican under the transfer.  Blue = no county-level flip.",
          fontproperties=fp(500, 12), color=INK, ha="left", va="center")
foot.text(0.025, 0.28, FOOT, fontproperties=fp(400, 11), color=MUTED, ha="left", va="center")

path = OUT / "8_KS_top10_by_race.png"
fig.savefig(path, dpi=100, facecolor=fig.get_facecolor())
plt.close()
im = Image.open(path)
assert im.size == (1920, 1080), im.size
manifest["top10"] = {
    "path": str(path),
    "values": {k: [(c, P["counties"][c][k]["I"]) for c, _ in sorted(P["counties"].items(), key=lambda kv: (-kv[1][k]["I"], kv[0]))[:10]] for k in RACE_ORDER},
}
print("wrote", path)

json.dump(manifest, open("/workspace/kansas-reverse/verification/chart_manifest.json", "w"), indent=1)
print("manifest written")
