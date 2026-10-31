"""
Analysis of simulated access-site infection data after PCI
----------------------------------------------------------
Input : data/procedures.csv, data/infection_events.csv  (SIMULATED data)
Output: results/*.csv and images/*.png

Infection events are rare, so every rate is reported per 1,000 procedures
with an exact (Clopper-Pearson) 95% confidence interval, and group
comparisons use Fisher's exact test.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

os.makedirs("results", exist_ok=True)
os.makedirs("images", exist_ok=True)

df = pd.read_csv("data/procedures.csv", parse_dates=["procedure_date"])
events = pd.read_csv("data/infection_events.csv")

OUTCOMES = {
    "Suspected infection": "suspected_infection_30d",
    "Confirmed infection": "confirmed_infection_30d",
}


def rate_row(label, group, k, n):
    """Rate per 1,000 procedures with an exact 95% CI."""
    ci = stats.binomtest(int(k), int(n)).proportion_ci(method="exact")
    return {
        "Outcome": label, "Group": group, "Procedures": int(n), "Events": int(k),
        "Rate_per_1000": round(k / n * 1000, 1),
        "CI_low": round(ci.low * 1000, 1), "CI_high": round(ci.high * 1000, 1),
    }


# ---------- 1. Overall and by case type ----------
rows = []
for label, col in OUTCOMES.items():
    rows.append(rate_row(label, "All procedures", df[col].sum(), len(df)))
    for case in ["Elective", "NSTEMI", "STEMI"]:
        sub = df[df["case_type"] == case]
        rows.append(rate_row(label, case, sub[col].sum(), len(sub)))
by_case = pd.DataFrame(rows)
by_case.to_csv("results/rates_by_case_type.csv", index=False)
print("RATES PER 1,000 PROCEDURES (exact 95% CI)")
print(by_case.to_string(index=False))

# ---------- 2. STEMI vs elective ----------
comp_rows = []
for label, col in OUTCOMES.items():
    a = df[df["case_type"] == "STEMI"][col]
    b = df[df["case_type"] == "Elective"][col]
    ka, na, kb, nb = a.sum(), len(a), b.sum(), len(b)
    _, p = stats.fisher_exact([[ka, na - ka], [kb, nb - kb]])
    # Rate ratio with an approximate (Katz) 95% CI; unreliable when counts are tiny
    rr = (ka / na) / (kb / nb) if kb > 0 else np.nan
    if kb > 0 and ka > 0:
        se = np.sqrt(1 / ka - 1 / na + 1 / kb - 1 / nb)
        lo, hi = np.exp(np.log(rr) - 1.96 * se), np.exp(np.log(rr) + 1.96 * se)
    else:
        lo = hi = np.nan
    comp_rows.append({
        "Outcome": label,
        "STEMI_events": int(ka), "STEMI_n": na,
        "Elective_events": int(kb), "Elective_n": nb,
        "Rate_ratio": round(rr, 2), "RR_CI_low": round(lo, 2), "RR_CI_high": round(hi, 2),
        "Fisher_p": round(p, 3),
    })
comparison = pd.DataFrame(comp_rows)
comparison.to_csv("results/stemi_vs_elective.csv", index=False)
print("\nSTEMI VS ELECTIVE")
print(comparison.to_string(index=False))

# ---------- 3. Rates by possible risk factors (suspected infection) ----------
df["Access / haemostasis"] = df["haemostasis_method"]
df["Skin prep"] = np.where(df["skin_prep_complete"] == 1, "Complete", "Incomplete")
df["Timing"] = np.where(df["out_of_hours"] == 1, "Out of hours", "In hours")
df["Diabetes"] = np.where(df["diabetes"] == 1, "Diabetes", "No diabetes")
df["Mechanical support"] = np.where(df["mechanical_support"] == 1, "Yes", "No")

factor_rows = []
for factor in ["Access / haemostasis", "Skin prep", "Timing", "Diabetes", "Mechanical support"]:
    for level, sub in df.groupby(factor):
        r = rate_row("Suspected infection", f"{factor}: {level}",
                     sub["suspected_infection_30d"].sum(), len(sub))
        r["Factor"] = factor
        factor_rows.append(r)
factors = pd.DataFrame(factor_rows)
factors.to_csv("results/rates_by_risk_factor.csv", index=False)
print("\nSUSPECTED INFECTION BY RISK FACTOR")
print(factors[["Group", "Procedures", "Events", "Rate_per_1000", "CI_low", "CI_high"]]
      .to_string(index=False))

# ---------- 4. Monthly control chart (p-chart, 3-sigma limits) ----------
df["month"] = df["procedure_date"].dt.to_period("M")
monthly = df.groupby("month").agg(procedures=("procedure_id", "count"),
                                  events=("suspected_infection_30d", "sum")).reset_index()
p_bar = monthly["events"].sum() / monthly["procedures"].sum()
monthly["rate_per_1000"] = monthly["events"] / monthly["procedures"] * 1000
sigma = np.sqrt(p_bar * (1 - p_bar) / monthly["procedures"])
monthly["UCL"] = (p_bar + 3 * sigma) * 1000
monthly["LCL"] = np.maximum(p_bar - 3 * sigma, 0) * 1000
monthly["centre_line"] = p_bar * 1000
monthly["month"] = monthly["month"].astype(str)
monthly.round(1).to_csv("results/monthly_control_chart.csv", index=False)
print("\nMONTHS ABOVE THE UPPER CONTROL LIMIT:",
      int((monthly["rate_per_1000"] > monthly["UCL"]).sum()))

# ---------- 5. Charts ----------
TEAL, GREY, RED = "#2a9d8f", "#9aa0a6", "#c0392b"

# 5a. Rate by case type with CIs
fig, ax = plt.subplots(figsize=(7, 4.5))
sub = by_case[by_case["Outcome"] == "Suspected infection"]
sub = sub[sub["Group"] != "All procedures"].reset_index(drop=True)
x = np.arange(len(sub))
ax.bar(x, sub["Rate_per_1000"], color=[GREY, GREY, TEAL],
       yerr=[sub["Rate_per_1000"] - sub["CI_low"], sub["CI_high"] - sub["Rate_per_1000"]],
       capsize=5)
for i, r in sub.iterrows():
    ax.text(i, r["CI_high"] + 1, f"{r['Events']}/{r['Procedures']}", ha="center", fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(sub["Group"])
ax.set_ylabel("Suspected infections per 1,000 procedures")
ax.set_title("Suspected access-site infection by case type\n(simulated data, exact 95% CI)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("images/rate_by_case_type.png", dpi=130)
plt.close()

# 5b. Monthly control chart
fig, ax = plt.subplots(figsize=(8, 4.5))
ax.plot(monthly["month"], monthly["rate_per_1000"], marker="o", color=TEAL, label="Monthly rate")
ax.plot(monthly["month"], monthly["centre_line"], color=GREY, label="Average")
ax.plot(monthly["month"], monthly["UCL"], color=RED, linestyle="--", label="Upper control limit")
out = monthly[monthly["rate_per_1000"] > monthly["UCL"]]
ax.scatter(out["month"], out["rate_per_1000"], color=RED, zorder=5, s=60)
ax.set_ylabel("Suspected infections per 1,000 procedures")
ax.set_title("Monthly control chart: suspected access-site infection\n(simulated data)")
ax.tick_params(axis="x", rotation=60)
ax.legend(frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("images/monthly_control_chart.png", dpi=130)
plt.close()

# 5c. Risk-factor rates with CIs
fig, ax = plt.subplots(figsize=(8, 5.5))
f = factors.iloc[::-1].reset_index(drop=True)
y = np.arange(len(f))
ax.errorbar(f["Rate_per_1000"], y,
            xerr=[f["Rate_per_1000"] - f["CI_low"], f["CI_high"] - f["Rate_per_1000"]],
            fmt="o", color=TEAL, ecolor=GREY, capsize=3)
ax.set_yticks(y)
ax.set_yticklabels(f["Group"], fontsize=9)
ax.set_xlabel("Suspected infections per 1,000 procedures (exact 95% CI)")
ax.set_title("Suspected infection rate by possible risk factor\n(simulated data)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig("images/rate_by_risk_factor.png", dpi=130)
plt.close()

print("\nDone: results/ and images/ saved.")
