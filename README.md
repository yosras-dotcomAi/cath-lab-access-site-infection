# Access-Site Infection After Cardiac Catheterisation: STEMI vs Elective PCI

> **Important note on data:** This project uses **simulated data**. It contains no patient or hospital data. The dataset was built to resemble the scale and structure of UK cardiac audit data (NICOR/BCIS), so the analysis workflow looks like a real surveillance project. The infection risks are set within ranges published in the medical literature, but the extra risk for urgent STEMI cases is an **assumption**, not a published finding. Results here show how the analysis works, not what any real cath lab achieves.

## Question
Do patients treated with primary PCI for STEMI have a higher rate of access-site infection within 30 days than patients treated electively, and which factors (access route, haemostasis method, skin preparation, mechanical support) are linked to infection?

## Why this project
I am a cath lab head nurse. Access-site infection is rare after cardiac catheterisation but serious when it happens, and infection-control teams track it as a rate per 1,000 procedures. Because events are rare, this project reports **confidence intervals** and avoids claiming differences the data cannot support.

## Dataset (simulated)
| | |
|---|---|
| Procedures | 1,500 PCI procedures in one year (2025) |
| Follow-up | 30 days for access-site infection |
| Case types | Elective, NSTEMI, STEMI (primary PCI) |
| Access routes | Radial (about 89%) and femoral |
| Tables | `procedures.csv`, `operators.csv`, `infection_events.csv` |

**Outcome levels** (as in routine surveillance):
- **Suspected infection:** clinical signs at the access site that prompt review.
- **Confirmed infection:** a deep or bloodstream infection, or a culture-positive infection.

## How the simulated numbers were chosen
| Item | Value used | Source |
|---|---|---|
| Radial access share | About 89% (2019/20) | [NAPCI 2021 Summary Report (NICOR)](https://www.hqip.org.uk/wp-content/uploads/2026/03/NAPCI-Domain-Report_2021_FINAL.pdf) |
| Radial use and ACS share of PCI | About 94% radial and 70% ACS (2022/23) | [BCIS national audit presentation, reported by TCTMD](https://www.tctmd.com/news/uk-cardiac-audit-reveals-some-good-some-appalling-trends-pci) |
| Case mix (elective, NSTEMI, primary PCI) | Roughly 38%, 32%, 30% | [NICOR PCI Hospital Report, Norfolk and Norwich University Hospital, 2015 to 2018](https://www.nnuh.nhs.uk/wp-content/uploads/2022/07/NICOR-outcome-data.pdf) |
| Femoral groin infection | About 0.2% with manual compression and 0.6% with closure devices | [Meta-analysis (Am Heart J 2010;159:518-531), as reported by Cardiovascular Business](https://cardiovascularbusiness.com/node/1602) |
| Infection after closure devices | Reported range 0% to 5.1% | [Malekpour and Castillo, HMP Global Learning Network](https://www.hmpgloballearningnetwork.com/site/vdm/content/infection-perilous-complication-closure-device) |
| Infectious complications in a PCI cohort with closure devices | 1.6% | [J Invasive Cardiol, 2010](https://hmpgloballearningnetwork.com/site/jic/articles/increased-vascular-access-complications-patients-renal-dysfunction-full-title-below) |
| Femoral vs radial arterial catheter infection (ICU, per 1,000 catheter-days) | Femoral about 4 times radial | Lorente et al., Critical Care 2006 ([doi:10.1186/cc4930](https://link.springer.com/doi/10.1186/cc4930)) |

**Assumptions (not published effect sizes):** higher odds of infection for STEMI (1.5), NSTEMI (1.25), diabetes (1.6), BMI of 35 or more (1.5), mechanical support (2.0), incomplete skin preparation (1.8), and age 75 or more (1.2). Suspected infections are modelled as about 2.5 times more frequent than confirmed ones. All constants are at the top of `generate_data.py` and can be changed.

## How to reproduce
```bash
pip install pandas numpy
python generate_data.py     # creates the three CSV files in data/
```

## Planned work
- [x] Simulated data generator and dataset
- [ ] Python analysis: infection rate per 1,000 procedures with exact confidence intervals, and a monthly control chart
- [ ] SQL queries on the three tables
- [ ] Power BI dashboard for infection-prevention reporting
- [ ] Final conclusions and limitations

## Repository structure
```
cath-lab-access-site-infection/
├── generate_data.py
├── data/
│   ├── procedures.csv
│   ├── operators.csv
│   └── infection_events.csv
└── README.md
```

## Author
**Yosra El Nagar**, Cath Lab Head Nurse moving into Healthcare Data Analytics
[LinkedIn](https://www.linkedin.com/in/yosra-nagar-9a6862118/) | [GitHub](https://github.com/yosras-dotcomAi)
