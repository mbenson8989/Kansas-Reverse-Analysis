# Methodology: how this analysis was done

This page is the methodology section of the Kansas Reverse Analysis, written so it can be read on its own. 2026 figures are unofficial until December 1, 2026. This is a what-if, not a finding. The work was run by the analyst.

Every step below was applied to all 105 Kansas counties and to all six statewide races on the 2026 ticket: United States Senate, Governor, Secretary of State, Attorney General, State Treasurer, and Commissioner of Insurance. Constitutional amendments, Supreme Court retentions, State Board of Education districts, and U.S. House districts are not in this statewide reversal.

1. **County-level measurement.** From the Kansas SOS unofficial 2026 county HTML (saved 11/19/2026; the live SOS site now returns 403 to this computer), the analyst parsed Democratic votes, Republican votes, and the race total for each county and race. Democratic registration comes from the official October 2026 SOS registration workbook (521,669 Democratic of 2,027,520 statewide). Population is the Census Bureau July 1, 2025 estimate, used only to sort tables. Vote share always uses that race’s total votes as the denominator.

2. **Fit the surplus line.** For each race, surplus S = Democratic vote share minus Democratic registration share. Ordinary least squares across 105 counties gives S = m × (D/100) + b. Governor uses the locked constants; Attorney General uses its stated fit, confirmed from the same files; the other four races use their own 2026* fits, with m and b rounded to four decimals by half-up rounding.

3. **Residual plus offset.** For each county, residual = actual S − (m × D/100 + b). Injection points = residual + b = actual S − m × D/100. This is the full reversal: the gap from the line, plus the offset, solved backward from the 2026* Democratic share.

4. **Convert to votes and clamp.** Votes = points ÷ 100 × the county’s race total. The result is rounded half-up (half away from zero). Negative estimates are set to zero. The count is also capped at the county’s Democratic votes, which did not bind in any race.

5. **Sum, then remove.** County votes are summed to a statewide injection total for that race. In the primary transfer view, those votes are subtracted from the Democrat and added to the Republican in each county; the race total does not change. In the secondary subtract-only view, the same votes are subtracted from the Democrat and from the total. Statewide margins are then recomputed. The six race totals are never added to one another.

6. **Double-verification rule.** Two independent passes recomputed every figure from the raw SOS files with different tools (pass 1: BeautifulSoup and pandas, with a numpy least-squares fit; pass 2: regex HTML parsing, openpyxl, csv, and exact Fraction normal equations). Every county, race, constant, margin, flip, historical fit, and saturation figure was compared. **Zero mismatches were required; if any had appeared, nothing would have been written to a repository.** A further check compared every CSV cell and every plotted number with pass 2.

### Worked example (Sedgwick, Governor)

Sedgwick’s 2026* Democratic registration share is 90,047 / 349,829 = 25.74%. Democratic surplus in the Governor race is 26.59 points. The part of surplus that the slope attributes to registration is 67.6004 × 25.74% = 17.40 points. What remains is 26.59 − 17.40 = 9.19 points, which is the 2.89-point residual from the locked line plus the 6.30-point offset. 9.1883% of 181,679 Governor votes equals 16,693 votes moved. (The rounded 9.19% × 181,679 is 16,696; the 16,693 figure is the correctly rounded exact value.)

### Caveats

- The gap is a distance from a statistical prediction, not evidence that any particular votes were injected.
- R² is about 0.67–0.72 in 2026*, so the line leaves real unexplained variation. The 2022 Governor R² is only 0.30.
- Treating the entire offset as injected is an upper-bound assumption. In a typical year the offset is part of the fitted relationship between registration and vote share, not a pile of extra votes.
- 2026 figures are unofficial until the December 1, 2026 certification.
- Cast vote record (CVR) access may be blocked. This analysis does not use CVRs and cannot speak to ballot-level images or records.
- The six race totals must not be added together. They are six views of the same election.

Verification results and the full analysis, including race tables and the historical hypothesis, are in `report/Kansas-Reverse-Analysis.md`.

