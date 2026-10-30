"""
Synthetic data generator: access-site infection after cardiac catheterisation
-----------------------------------------------------------------------------
Creates SIMULATED records for 1,500 PCI procedures in one year (2025) with a
30-day follow-up for access-site infection. No real patient or hospital data
is used.

Two outcome levels, as in routine infection surveillance:
  suspected_infection_30d  clinical signs at the access site that prompt review
  confirmed_infection_30d  deep or bloodstream infection, or culture-positive

Outputs (folder "data/"):
  procedures.csv         one row per procedure
  operators.csv          one row per operator
  infection_events.csv   one row per infection (a small subset of procedures)

HOW THE NUMBERS WERE CHOSEN
Volumes and access-route mix are adapted from published UK audit figures
(NICOR/BCIS). Baseline infection risks per access route are set inside the
range reported in the literature (see README "Data sources"). The extra risk
for urgent STEMI cases, diabetes, obesity, mechanical support and incomplete
skin preparation are ASSUMPTIONS based on clinical reasoning, not published
effect sizes. Change the constants below to test other assumptions.
"""

import os
import numpy as np
import pandas as pd

SEED = 2025
N_PROCEDURES = 1500
YEAR_START, YEAR_END = "2025-01-01", "2025-12-31"
FOLLOW_UP_DAYS = 30

# ---------- Case mix (adapted from a UK hospital audit report, rounded) ----------
CASE_MIX = {"Elective": 0.38, "NSTEMI": 0.32, "STEMI": 0.30}

# ---------- Access route: share of FEMORAL access by case type ----------
# Overall radial use is ~90% in UK audits; STEMI / shock cases use femoral more.
P_FEMORAL = {"Elective": 0.06, "NSTEMI": 0.09, "STEMI": 0.15}
P_VCD_GIVEN_FEMORAL = 0.55   # closure device use among femoral cases (assumption)

# ---------- Baseline 30-day access-site infection risk (before risk factors) ----------
# Femoral: ~0.2% manual compression vs ~0.6% closure device in pooled data;
# radial is lower. Values are set within published ranges.
BASE_RISK = {"Radial": 0.0020, "Femoral_manual": 0.0060, "Femoral_VCD": 0.0140}

# ---------- Odds multipliers (ASSUMPTIONS) ----------
OR_CASE = {"Elective": 1.0, "NSTEMI": 1.25, "STEMI": 1.5}
OR_DIABETES = 1.6
OR_OBESE = 1.5          # BMI >= 35
OR_MECH_SUPPORT = 2.0   # IABP / Impella
OR_PREP_INCOMPLETE = 1.8
OR_AGE_75 = 1.2

# Suspected infections are more common than confirmed ones (assumption).
SUSPECTED_MULTIPLIER = 2.5

rng = np.random.default_rng(SEED)
os.makedirs("data", exist_ok=True)
n = N_PROCEDURES

# ---------- Operators ----------
operators = pd.DataFrame({
    "operator_id": [f"OP{i:02d}" for i in range(1, 9)],
    "years_experience": [4, 6, 9, 12, 15, 18, 22, 25],
    "annual_volume_band": ["Medium", "Medium", "Medium", "High",
                           "High", "High", "High", "High"],
})

# ---------- Case type, dates and times ----------
case_type = rng.choice(list(CASE_MIX), n, p=list(CASE_MIX.values()))
all_days = pd.date_range(YEAR_START, YEAR_END)
weekdays = all_days[all_days.dayofweek < 5]

dates, hours = [], []
for c in case_type:
    if c == "Elective":                       # planned list, weekdays, daytime
        d = rng.choice(weekdays)
        h = int(rng.integers(8, 17))
    elif c == "NSTEMI":                       # mostly weekdays, extended hours
        d = rng.choice(weekdays if rng.random() < 0.8 else all_days)
        h = int(rng.integers(7, 23))
    else:                                     # STEMI: 24/7, any day
        d = rng.choice(all_days)
        h = int(rng.choice(24, p=np.r_[np.full(7, 0.045), np.full(10, 0.0385),
                                       np.full(7, 0.0432)] / 
                           np.r_[np.full(7, 0.045), np.full(10, 0.0385),
                                 np.full(7, 0.0432)].sum()))
    dates.append(pd.Timestamp(d))
    hours.append(h)

dates = pd.Series(dates)
hours = np.array(hours)
out_of_hours = ((hours < 8) | (hours >= 18) | (dates.dt.dayofweek >= 5)).astype(int)

# ---------- Patient characteristics ----------
age_mean = {"Elective": 65, "NSTEMI": 66, "STEMI": 61}
age = np.array([rng.normal(age_mean[c], 11) for c in case_type]).round().clip(30, 92).astype(int)
sex = np.where(rng.random(n) < 0.72, "Male", "Female")
bmi = np.clip(rng.normal(28.5, 5.0, n), 17, 50).round(1)
diabetes = (rng.random(n) < np.where(case_type == "Elective", 0.28, 0.30)).astype(int)
ckd = (rng.random(n) < 0.10).astype(int)

# ---------- Access route and haemostasis ----------
femoral = np.array([rng.random() < P_FEMORAL[c] for c in case_type])
mech_support = (rng.random(n) < np.where(case_type == "STEMI", 0.05, 0.004)).astype(int)
femoral = femoral | (mech_support == 1)       # mechanical support needs femoral access
access_site = np.where(femoral, "Femoral", "Radial")

vcd = femoral & (rng.random(n) < P_VCD_GIVEN_FEMORAL)
haemostasis = np.where(~femoral, "Radial band",
                       np.where(vcd, "Closure device", "Manual compression"))
route_group = np.where(~femoral, "Radial",
                       np.where(vcd, "Femoral_VCD", "Femoral_manual"))

# Hours the access site/sheath is managed after the procedure
sheath_dwell_hours = np.where(
    ~femoral, np.round(rng.uniform(0, 2, n), 1),
    np.where(vcd, 0.0,
             np.round(rng.gamma(4, 1.2, n) + np.where(case_type == "STEMI", 2, 0), 1)))

# ---------- Process measure: complete skin preparation ----------
# Less likely in time-critical STEMI and out-of-hours cases (assumption).
p_prep = np.where(case_type == "STEMI", 0.82, 0.96) - 0.05 * out_of_hours
prep_complete = (rng.random(n) < p_prep).astype(int)

# ---------- Procedure details ----------
duration_mean = {"Elective": 55, "NSTEMI": 60, "STEMI": 48}
procedure_minutes = np.array([rng.lognormal(np.log(duration_mean[c]), 0.35)
                              for c in case_type]).round().astype(int).clip(15, 240)
operator_id = rng.choice(operators.operator_id, n,
                         p=[0.06, 0.08, 0.10, 0.14, 0.16, 0.16, 0.15, 0.15])
lab_room = rng.choice(["Cath Lab 1", "Cath Lab 2", "Cath Lab 3"], n, p=[0.40, 0.35, 0.25])

# ---------- Infection risk model ----------
base = np.array([BASE_RISK[g] for g in route_group])
odds = base / (1 - base)
odds *= np.array([OR_CASE[c] for c in case_type])
odds *= np.where(diabetes == 1, OR_DIABETES, 1.0)
odds *= np.where(bmi >= 35, OR_OBESE, 1.0)
odds *= np.where(mech_support == 1, OR_MECH_SUPPORT, 1.0)
odds *= np.where(prep_complete == 0, OR_PREP_INCOMPLETE, 1.0)
odds *= np.where(age >= 75, OR_AGE_75, 1.0)
risk = odds / (1 + odds)                       # risk of a CONFIRMED-level infection
suspected_risk = np.minimum(risk * SUSPECTED_MULTIPLIER, 0.5)
suspected = (rng.random(n) < suspected_risk).astype(int)

# Event details for every suspected infection decide whether it is confirmed
sus_idx = np.flatnonzero(suspected == 1)
m = len(sus_idx)
severity = rng.choice(["Superficial", "Deep", "Bloodstream"], m, p=[0.80, 0.15, 0.05])
culture_taken = (severity != "Superficial") | (rng.random(m) < 0.70)
growth = culture_taken & ((severity != "Superficial") | (rng.random(m) < 0.35))
confirmed_events = (severity != "Superficial") | growth
organism = np.where(
    ~culture_taken, "Not cultured",
    np.where(~growth, "No growth",
             rng.choice(["Staphylococcus aureus (MSSA)", "MRSA",
                         "Coagulase-negative Staph", "Gram-negative"], m,
                        p=[0.62, 0.12, 0.16, 0.10])))
confirmed = np.zeros(n, dtype=int)
confirmed[sus_idx] = confirmed_events.astype(int)

# ---------- Assemble procedures table ----------
df = pd.DataFrame({
    "procedure_id": [f"PR{100000 + i}" for i in range(n)],
    "procedure_date": dates.dt.strftime("%Y-%m-%d"),
    "procedure_hour": hours,
    "out_of_hours": out_of_hours,
    "case_type": case_type,
    "age": age,
    "sex": sex,
    "bmi": bmi,
    "diabetes": diabetes,
    "ckd": ckd,
    "access_site": access_site,
    "haemostasis_method": haemostasis,
    "mechanical_support": mech_support,
    "sheath_dwell_hours": sheath_dwell_hours,
    "skin_prep_complete": prep_complete,
    "procedure_minutes": procedure_minutes,
    "operator_id": operator_id,
    "lab_room": lab_room,
    "suspected_infection_30d": suspected,
    "confirmed_infection_30d": confirmed,
})
df = df.sort_values(["procedure_date", "procedure_hour"]).reset_index(drop=True)
df["procedure_id"] = [f"PR{100000 + i}" for i in range(n)]

# ---------- Infection events table (one row per suspected infection) ----------
treatment = np.where(severity == "Superficial",
                     np.where(growth, "Oral antibiotics", "Wound care / review"),
                     np.where(severity == "Deep", "IV antibiotics + drainage",
                              "IV antibiotics"))
events = pd.DataFrame({
    "procedure_id": df.loc[sus_idx, "procedure_id"].values,
    "days_to_onset": np.clip(rng.gamma(3, 2.4, m).round(), 1, FOLLOW_UP_DAYS).astype(int),
    "severity": severity,
    "organism": organism,
    "confirmed": confirmed_events.astype(int),
    "treatment": treatment,
    "readmitted": ((severity != "Superficial") | (rng.random(m) < 0.10)).astype(int),
})

df.to_csv("data/procedures.csv", index=False)
operators.to_csv("data/operators.csv", index=False)
events.to_csv("data/infection_events.csv", index=False)

print(f"Saved {len(df)} procedures, {len(operators)} operators, "
      f"{len(events)} suspected-infection events to the data/ folder.")
print("Model-expected confirmed:", round(risk.sum(), 1),
      "| suspected:", round(suspected_risk.sum(), 1))
print("Simulated suspected:", int(suspected.sum()),
      "| confirmed:", int(confirmed.sum()))
