# Implementation Plan – Substrate Integrated Waveguide (SIW) Band-Pass Filter at X-Band

**Course:** RF Components & Circuits (RFCC) – Course Project
**Topic:** Substrate integrated waveguide filter at X-band
**Software:** openEMS v0.37.0 (open-source 3-D FDTD full-wave EM solver) + Python 3.13 (CSXCAD geometry, NumPy/SciPy/Matplotlib post-processing)
**Report deadline (per instructions):** 27-11-2026, 5 PM, in Word format

---

## 1. What the instruction sheet requires and how this plan meets it

| Instruction (from the PDF) | How it is handled |
|---|---|
| Objective: learn a software tool to design, model and analyse RF components | openEMS full-wave FDTD solver, scripted in Python. All geometry, meshing, ports, solving and post-processing are done in it. |
| Rule 7: find a simple research paper and take the design specs from it | **Base paper:** H. Bandar and N. Türker Tokan, "Comparison of post and iris substrate integrated waveguide band-pass filters for X-Band applications", *Sigma J. Eng. Nat. Sci.*, vol. 40, no. 1, pp. 45–56, 2022, DOI 10.14744/sigma.2022.00004 (open access, saved in `01_Base_Paper`). |
| Rule 8b: validate all results of the paper (8/10) | Re-simulate every simulated filter of the paper whose dimensions are published (Tables 1 and 2) and compare IL and RL point by point with Tables 3 and 4 and Figs. 8, 9 and 11. |
| Rule 8a: validate and improve on the results (10/10) | Re-design the 3rd-order Chebyshev post filter with openEMS-extracted post data so that the whole 9.75–10.25 GHz band has RL ≥ 20 dB (the paper only reaches 14 dB and 10.7 dB at the band edges). Add an optimised microstrip-to-SIW transition, because the paper blames its 4 dB measured loss partly on the transition and connectors. |
| Rule 10: report in Word format with all results | A Word report is generated in `05_Report`, with every figure and table. |

## 2. Design specifications taken from the base paper

| Parameter | Value |
|---|---|
| Centre frequency f0 | 10 GHz |
| Bandwidth | 500 MHz (9.75–10.25 GHz), FBW = 5 % |
| Response | Chebyshev, 0.1 dB ripple (also Butterworth) |
| Filter order | 3 (also 5) |
| Substrate | Rogers RT/Duroid 5870, εr = 2.33, tan δ = 0.0012 at 10 GHz, h = 1.57 mm, 35 µm copper |
| SIW | via diameter d = 1.3205 mm, pitch p = 1.9807 mm, via-row spacing a_s = 15.9028 mm, SIW length L = 59.421 mm, board width W = 20 mm |
| Equivalent waveguide | WR-90 (a = 22.86 mm), a_eff = 22.86/√2.33 = 14.976 mm |
| Topologies | (i) centred inductive post filter, (ii) inductive iris filter (copper wall, or small vias of 0.2 mm diameter at 0.6 mm spacing) |
| Overall prototype size | 96.4 mm × 20 mm, including the tapered microstrip feeds |

## 3. Work breakdown (two-member group, split evenly as Rule 9 asks)

| # | Phase | Output | Folder | Suggested owner |
|---|---|---|---|---|
| 1 | Literature survey and base paper selection | Base paper PDF and spec table | `01_Base_Paper` | Member A |
| 2 | Analytical design: SIW width rules, a_eff, cut-off, guide wavelength, g-values, impedance-inverter values (paper Eqs. 1–12) | `siw_design_calc.py` and `design_calculations.txt` | `02_Design_Calculations` | Member A |
| 3 | openEMS model of the plain SIW line (checks cut-off and loss, verifies the a_eff rule) | S-parameters of the SIW line | `03_openEMS_Simulation` | Member B |
| 4 | openEMS models of all paper filters (post and iris; Chebyshev and Butterworth; 3rd and 5th order; iris made of vias) | S-parameter plots, Touchstone files | `03_…` and `04_Results` | A and B |
| 5 | Validation: compare IL and RL with paper Tables 3 and 4 | Validation table with % agreement | `04_Results` | Member B |
| 6 | Improvement: full-wave post characterisation, re-synthesis, tuned design, microstrip taper transition, full 96.4 mm board model | Improved-design plots and comparison | `03_…` and `04_Results` | Member A |
| 7 | Results, conclusions, Word report | `RESULTS_AND_CONCLUSIONS.md` and the Word report | root and `05_Report` | A and B |

## 4. Simulation methodology in openEMS

1. **Geometry (CSXCAD):** substrate block (εr = 2.33, with a conductivity κ = 2πf0·ε0·εr·tanδ to model dielectric loss), top and bottom copper as conducting sheets (σ = 5.8×10⁷ S/m, 35 µm), via holes and posts as metal cylinders, irises as thin metal walls or rows of 0.2 mm vias.
2. **Ports:**
   - *Validation models:* TE10 rectangular waveguide ports on short solid-wall feed sections of width a_eff. This copies the paper's CST waveguide-port set-up. The port impedance is corrected for the dielectric filling: Z_TE = ωμ0/β with β = √(k0²εr − kc²).
   - *Full-board model:* 50 Ω microstrip ports, a tapered transition, and the SIW filter.
3. **Mesh:** a graded rectilinear mesh, at most λ/20 at 12 GHz in the dielectric, refined to about 0.1 mm around posts, vias and irises, with fixed mesh lines on the metal edges.
4. **Excitation:** a Gaussian pulse covering 8–12 GHz. The run stops when the energy has fallen by 40 dB (end criterion 1e-4).
5. **Boundaries:** PML at the port ends and MUR absorbing boundaries on the sides and in the air above and below the board.
6. **Post-processing:** S11 and S21 from the port voltage and current waves, IL and RL read at 9.75, 10.0 and 10.25 GHz. The 3 dB and 20 dB-RL bandwidths, the stop-band rejection, and Touchstone (.s2p) export are also produced.

## 5. Validation criteria (used for the "% of results validated" score)

A paper result counts as **validated** when the openEMS value at the same frequency agrees within:
- ±0.5 dB for IL in the passband, and ±3 dB (or the same side of the 20 dB line) for RL;
- ±1.5 % for the centre frequency and the shape of the response (number of reflection zeros, order).

Small differences are expected between a CST FIT solver and an openEMS FDTD solver, and from staircasing of the round vias. They are explained in the report.

## 6. Planned improvement (for full marks)

* **Problem in the paper:** the 3rd-order Chebyshev post filter has only 14 dB / 10.7 dB RL and 1.23 / 1.33 dB IL at the band edges (Table 3). The 0.1 dB-ripple passband therefore does not cover the specified 500 MHz. The measured IL is about 4 dB.
* **Fix:**
  1. Extract the true inverter value K(d) and phase of a centred post with openEMS, instead of reading the Marcuvitz chart by eye.
  2. Re-synthesise with a slightly wider design bandwidth and re-tune d1, d2, L1 and L2 so that RL ≥ 20 dB over all of 9.75–10.25 GHz.
  3. Design and simulate a low-reflection microstrip-to-SIW taper and the complete 96.4 mm × 20 mm board.
* **Target:** RL ≥ 20 dB over the full band, IL ≤ 1 dB across the band, and f0 within 0.5 % of 10 GHz.

## 7. Folder structure (Desktop\SIW_Filter_Xband_openEMS)

```
00_IMPLEMENTATION_PLAN.md          ← this file
01_WHAT_AND_WHY.md                 ← what is implemented and why
RESULTS_AND_CONCLUSIONS.md         ← all numeric results and conclusions
01_Base_Paper/                     ← base research paper (PDF)
02_Design_Calculations/            ← analytical design script and output
03_openEMS_Simulation/             ← openEMS Python models (re-runnable)
04_Results/                        ← plots (PNG), S-parameters (.s2p/.csv), tables
05_Report/                         ← final Word report
```

## 8. How to re-run

```powershell
# openEMS and portable Python 3.13 are installed in C:\Users\KRISH MEHTA\openEMS_install
& "C:\Users\KRISH MEHTA\openEMS_install\py313\tools\python.exe" 03_openEMS_Simulation\run_all.py
```
