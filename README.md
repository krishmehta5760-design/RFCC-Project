# SIW Band-Pass Filter at X-Band (openEMS) – RFCC Course Project

We validate and then improve the substrate integrated waveguide (SIW) post and iris band-pass filters from
H. Bandar and N. Türker Tokan, "Comparison of post and iris substrate integrated waveguide band-pass filters for X-Band applications",
*Sigma J. Eng. Nat. Sci.* 40(1), 45–56, 2022 (DOI 10.14744/sigma.2022.00004). All simulations use the free full-wave FDTD solver
[openEMS](https://openems.de) v0.37.0, scripted in Python.

**Specs:** 10 GHz centre, 500 MHz bandwidth (9.75–10.25 GHz), RT/Duroid 5870 substrate (εr 2.33, h 1.57 mm).

## Results in short
* **Validation:** all 7 of the paper's filters were simulated. 87 % of its tabulated values agree within ±0.5 % in frequency (47 % at exactly the same frequency), and every conclusion of the paper is confirmed.
* **Improvement:** a redesigned 4th-order post filter on the same 59.4 mm SIW gives RL ≥ 21.7 dB and IL ≤ 0.82 dB across the whole band. The paper's design reaches 10.7 dB and 1.33 dB.
* **Board:** we also designed the microstrip-to-SIW taper (best width 7.5 mm) and simulated the complete 96.4 × 20 mm board.

## Where things are

| File / folder | Contents |
|---|---|
| `00_IMPLEMENTATION_PLAN.md` | Plan, specifications, work split |
| `01_WHAT_AND_WHY.md` | What was implemented and why |
| `RESULTS_AND_CONCLUSIONS.md` | All numerical results and conclusions |
| `PRESENTATION_GUIDE.md` | Beginner explanation, slide script, likely questions |
| `01_Base_Paper/` | The base paper |
| `02_Design_Calculations/` | Analytical design script and its output |
| `03_openEMS_Simulation/` | openEMS models; `sim_data/` holds the saved simulation results |
| `04_Results/` | Plots, Touchstone (.s2p) files, tables |
| `05_Report/` | Word report (.doc/.docx/.pdf) and the scripts that build it |
| `06_Presentation/` | 10-slide deck, presentation script and slide figures |
| `07_Thesis/` | Thesis (Word + PDF) and `make_thesis.py`, which builds it |
| `08_Research_Paper/` | IEEE conference-format paper: LaTeX source, figures and PDF |
| `make_submission.py` | Builds the upload package (`Desktop/SIW_Filter_Submission`, under 50 MB) |

## How to run
Install openEMS v0.37.0 and its Python packages. Then, from `03_openEMS_Simulation`:

```
python run_all.py          # re-makes all results, plots and the report (cached simulations reused)
python demo_live.py improved   # simulates the improved filter live (~2 min)
```

Delete `sim_data/` to re-run every simulation from scratch, which takes about 1.5 h.

*All results are from simulation. Nothing was fabricated or measured.*
