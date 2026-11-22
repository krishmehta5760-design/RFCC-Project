# What we are implementing and why

## 1. The device: a Substrate Integrated Waveguide (SIW) band-pass filter at X-band

**What:** An SIW is a rectangular waveguide built inside a printed circuit board. The top and bottom copper layers act as the broad walls. Two rows of plated via holes act as the narrow side walls. Inductive discontinuities placed inside the SIW turn it into a chain of coupled half-wavelength cavity resonators, which gives a band-pass filter. We use two kinds of discontinuity:
* **centred inductive posts** (one plated via on the centre line, with a diameter set by the design), and
* **inductive irises** (metal walls, or rows of small vias, that narrow the guide to a window).

**Why an SIW filter:**
* Rectangular metal waveguides have very high Q (5000–10000) and handle high power, but they are bulky, expensive and hard to integrate.
* Microstrip filters are cheap and planar, but their Q is low (50–100) and they lose more at X-band.
* An SIW sits between the two. It keeps most of the waveguide's Q (500–1000) and its shielding, but it is made by an ordinary PCB process and connects directly to microstrip circuits.

**Why X-band (8–12 GHz), centred at 10 GHz with 500 MHz bandwidth:** X-band is used for radar (weather, marine, air traffic) and satellite links. Its atmospheric attenuation is low, and a 5 % fractional bandwidth is a typical channel-select requirement.

## 2. The base paper and why we chose it

H. Bandar and N. Türker Tokan, "Comparison of post and iris substrate integrated waveguide band-pass filters for X-Band applications", *Sigma Journal of Engineering and Natural Sciences*, 40(1), 45–56, 2022.

We chose it because:
1. It is a **simple, complete paper**. It gives the full design procedure (Eqs. 1–12) and **all the dimensions** (Tables 1 and 2), so every result can be reproduced. Rule 7 of the instructions asks for this.
2. It gives **numeric results** (Tables 3 and 4: IL and RL at the lower edge, centre and upper edge). This lets us state exactly what percentage of the results we validated, which matches the Rule 8 grading scale.
3. It has **two topologies, two responses and two orders**: post or iris, Butterworth or Chebyshev, 3rd or 5th order. That is plenty to learn the software with.
4. The paper has **room to improve**. Its Chebyshev filter does not reach the specified 500 MHz with good matching (RL is only 10.7 dB at the upper edge), and its measured loss is about 4 dB. This gives the "improvement over existing results" that Rule 8a asks for.

## 3. Why openEMS

| Requirement | openEMS |
|---|---|
| Full-wave 3-D solver that can model vias, posts, irises and radiation and leakage between vias | Yes. It is an FDTD (Finite-Difference Time-Domain) solver using the EC-FDTD method. |
| Available to us without a licence | Yes. It is free and open source (GPL). HFSS and CST, which the paper used, need paid licences. |
| Waveguide ports, microstrip ports, lossy dielectric, finite-conductivity copper | Yes: RectWGPort, MSLPort, material κ, and conducting sheets. |
| Broadband result in one run | Yes. FDTD gives the whole 8–12 GHz sweep from a single pulse simulation. |
| Scriptable and repeatable | Yes. Every model is a Python script, so the dimensions are parameters and the design can be tuned in a loop. |
| Lets us learn the tool, which is the course objective | Scripting forces us to define the geometry, mesh, boundaries, ports and post-processing explicitly, so we see how an EM solver works. |

A different solver (FDTD in openEMS against FIT in CST) is an **independent check** of the paper. When two different numerical methods agree, the validation is stronger.

## 4. What exactly is implemented

| Step | What | Why |
|---|---|---|
| A | **Analytical design** (`02_Design_Calculations/siw_design_calc.py`): SIW via rules (d < λg/5, p ≤ 2d), equivalent width a_eff, TE10 cut-off, guide wavelengths (paper Eq. 1), Chebyshev and Butterworth g-values, inverter values K/Z0 (Eqs. 4–6) and shunt reactances X/Z0 (Eq. 7) | To understand and check the paper's design numbers before any EM simulation |
| B | **Plain SIW line** in openEMS | To confirm that the via walls behave like a WR-90-equivalent guide (cut-off near 6.56 GHz, low loss and leakage) and to check the mesh and ports |
| C | **Paper post filters** (3rd-order Butterworth and Chebyshev; 5th-order Chebyshev) | To validate the paper's results (Tables 3a and 4, Figs. 8 and 9) |
| D | **Paper iris filters** (the same set, plus the iris built from small vias) | To validate Tables 3b and 4 and Figs. 8, 9 and 11 |
| E | **Validation table**: openEMS against the paper at 9.75, 10 and 10.25 GHz | To give the percentage of results validated (grading rule 8) |
| F | **Improved design**: openEMS-extracted post inverter curve K(d), re-synthesis and tuning | To get RL ≥ 20 dB over the whole 500 MHz band, which the paper does not reach |
| G | **Microstrip-to-SIW taper and complete board** (96.4 mm × 20 mm) | The paper's measured IL was about 4 dB, partly from the transitions. We design a low-loss transition so the board is ready to fabricate. |
| H | **Results and conclusions file and Word report** | Rule 10 requires them |

## 5. Assumptions made where the paper is silent

* Iris walls are thin metal walls running from the via rows to the window edge. "Window width d" is the opening between the two walls.
* "Lower and upper cut-off frequency" in Tables 3 and 4 is taken as the passband edges, 9.75 GHz and 10.25 GHz (f0 ± BW/2).
* Copper is σ = 5.8×10⁷ S/m and 35 µm thick, and the loss tangent is 0.0012, as stated in the paper.
* The paper does not give the taper dimensions. We design them ourselves (step G).
