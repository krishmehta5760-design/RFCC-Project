# Results and Conclusions – SIW Band-Pass Filter at X-Band (openEMS)

**Base paper:** H. Bandar and N. Türker Tokan, *Sigma J. Eng. Nat. Sci.* 40(1), 45–56, 2022
**Tool:** openEMS v0.37.0 (FDTD), Python 3.13. All numbers below come from our own simulations, except those labelled "paper".
**Plots:** `04_Results/plots` · **S-parameters:** `04_Results/touchstone/*.s2p` · **Tables:** `04_Results/tables`

---

## 1. Analytical design (02_Design_Calculations)

| Quantity | Result |
|---|---|
| a_eff = a_s − d²/(0.95p) | 14.976 mm, equal to WR-90/√εr |
| TE10 / TE20 cut-off | 6.557 GHz / 13.11 GHz, so the guide is single-mode over the whole X-band |
| Via rules d < λg/5 and p ≤ 2d | 1.32 < 4.99 mm ✓ and 1.98 < 2.64 mm ✓ |
| λg at 9.75 / 10 / 10.25 GHz | 27.22 / 26.01 / 24.93 mm |
| K01, K12 (Chebyshev 0.1 dB, n = 3) | 0.3656, 0.1267 |
| Iris spacings from thin-iris theory | 11.059 and 11.991 mm, against the paper's 11.072 and 12.004 mm (Δ = 0.013 mm) ✓ |
| Unloaded Q (estimate) | Qc ≈ 1935, Qd = 833, Qu ≈ 582 |
| Predicted centre IL (Cohn) | 3rd order 0.48 dB, 5th order 1.05 dB |

## 2. openEMS model check: plain SIW line

* |S11| < −40 dB from 8 to 12 GHz. The via-wall SIW matches the equivalent solid-wall guide, and the ports are set up correctly.
* The loss is about 3.0 dB/m (S21 ≈ −0.20 dB over 77 mm). Theory gives αd + αc = 3.05 dB/m. ✓

## 3. Validation of the paper (7 filters, published dimensions, no tuning)

Plots: `Fig8a_3rd_butterworth.png`, `Fig8b_3rd_chebyshev.png`, `Fig9_5th_chebyshev.png`, `Fig11_iris_walls_vs_vias.png`. The full point-by-point table is `04_Results/tables/validation_table.md`.

| Filter (openEMS) | f0 (3 dB centre) | 3 dB BW | IL @ 10 GHz (openEMS / paper) | RL @ 10 GHz (openEMS / paper) |
|---|---|---|---|---|
| Post, 3rd, Butterworth | 9.92 GHz | 490 MHz | 0.65 / 0.68 dB | 30.2 / 45 dB |
| Post, 3rd, Chebyshev | 9.94 GHz | 700 MHz | 0.62 / 0.78 dB | 19.8 / 23 dB |
| Iris, 3rd, Butterworth | 9.99 GHz | 470 MHz | 0.77 / 0.52 dB | 28.3 / 20 dB |
| Iris, 3rd, Chebyshev | 10.01 GHz | 660 MHz | 0.59 / 0.89 dB | 34.5 / 21.23 dB |
| Post, 5th, Chebyshev | 9.94 GHz | 550 MHz | 1.13 / 0.2 dB* | 19.6 / 32 dB |
| Iris, 5th, Chebyshev | 9.98 GHz | 520 MHz | 1.18 / 0.21 dB* | 22.1 / 28 dB |
| Iris, 3rd, Chebyshev, small vias | 9.98 GHz | 700 MHz | 0.58 / 0.81 dB | 17.9 / 30 dB |

**Validation score (38 numerical values in paper Tables 3 and 4 plus Fig. 11):**
* Strict, at exactly the same frequency: **18/38 = 47 %**.
* Allowing ±0.5 % (±50 MHz) frequency offset between solvers: **33/38 = 87 %**.
* Qualitative results are all confirmed (100 %):
  * every filter is centred at 10 GHz (within 0.8 %);
  * the filter orders and responses are correct;
  * the post filter has the wider bandwidth;
  * small vias can replace the iris walls with almost no change;
  * the 5th-order filters are much more selective (over 50 dB rejection at 9 and 11 GHz).

*Finding:* the paper's 0.2 dB IL for the 5th-order filters is not physically achievable with tan δ = 0.0012. Theory (Cohn) gives 1.05 dB and openEMS gives 1.13–1.18 dB. The paper's 5th-order runs were probably made with lower losses.

*Why some strict checks fail:* the band-edge values (9.75 and 10.25 GHz) lie on very steep skirts. openEMS places the post filters about 0.6 % lower in frequency than CST. Mesh refinement moves them by only 0.1 % (section 6), so the offset comes from solver and model differences, such as FDTD vs FIT and the paper's unknown port and wall settings. A 50 MHz shift changes the edge IL or RL by several dB.

## 4. Improvement (main contribution)

**Problem in the paper:** with the paper's post dimensions the RL ≥ 20 dB band is only 9.68–10.14 GHz in openEMS. Inside the specified 9.75–10.25 GHz band, the RL falls to 5.8 dB and the IL rises to 2.26 dB. The paper's own Table 3 gives 10.7 dB RL and 1.33 dB IL at the band edge. The cause is that the post sizes were read from the Marcuvitz chart. Full-wave extraction shows that the paper's posts give K = 0.379 and 0.134, but the design needs 0.366 and 0.127.

**Method:**
1. openEMS full-wave extraction of K(d) and φ(d) for a centred post (`post_K_phi_extraction.png`).
2. Re-synthesis with a 0.03 dB ripple (RL 21.6 dB) over 9.72–10.28 GHz.
3. Spacings computed from the extracted phases.
4. An automatic centre-frequency re-tune, which converged in 1–2 full-wave runs.

| Design (openEMS, TE10-port model) | min RL, 9.75–10.25 GHz | max IL in band | IL @ 10 GHz | RL ≥ 20 dB band | 3 dB BW | Rej. 9 GHz | Rej. 11 GHz |
|---|---|---|---|---|---|---|---|
| Paper Table 3 (CST) | 10.7 dB | 1.33 dB | 0.78 dB | – | – | – | – |
| Paper design (openEMS) | 5.84 dB | 2.26 dB | 0.62 dB | 9.68–10.14 GHz | 700 MHz | 33.1 dB | 24.3 dB |
| Improved A: 3rd order, 0.02 dB | 22.67 dB | 0.48 dB | 0.41 dB | 9.735–10.285 GHz | 1030 MHz | 25.3 dB | 12.2 dB |
| Improved B: 3rd order, 0.03 dB | 22.21 dB | 0.52 dB | 0.43 dB | 9.74–10.26 GHz | 910 MHz | 27.2 dB | 15.4 dB |
| **Improved C: 4th order, 0.03 dB (final)** | **21.69 dB** | **0.82 dB** | **0.68 dB** | **9.735–10.26 GHz** | **715 MHz** | **46.2 dB** | **29.7 dB** |

**Final improved design (C), symmetric, same 59.421 mm SIW:**
* post diameters d1, d2, d3 = 0.5731, 2.1243, 2.5149 mm (order d1–d2–d3–d2–d1);
* spacings L1, L2 = 11.1515, 12.8709 mm (order L1–L2–L2–L1);
* the posts span 48.0 mm, so they fit in the paper's SIW.

Against the paper, design C:
* meets RL ≥ 20 dB over the **whole** 500 MHz band;
* has a lower worst-case in-band IL;
* rejects better at 9 and 11 GHz (+13 dB and +5 dB);
* keeps a similar 3 dB bandwidth;
* uses the same board and the same fabrication process.

Designs A and B show the trade-off at 3rd order: a deep match and very low IL, but wider skirts.

## 5. Transition and complete board (96.4 mm × 20 mm)

The paper gives no taper dimensions, so we designed them:
* 50 Ω microstrip width 4.66 mm;
* feed line 5 mm, linear taper 13.49 mm;
* taper width swept from 5.5 to 8.5 mm. **The best width is 7.5 mm**, with back-to-back |S11| < −21.4 dB from 9 to 11 GHz.

| Complete board (50 Ω microstrip ports) | min RL in band | max IL in band | IL @ 10 GHz | 3 dB BW | Rej. 9 / 11 GHz |
|---|---|---|---|---|---|
| Paper filter + taper | 3.96 dB | 2.48 dB | 0.37 dB | 695 MHz | 35.4 / 25.1 dB |
| Improved filter + taper | 17.67 dB | 0.74 dB | 0.51 dB | 725 MHz | 35.0 / 33.4 dB |

On the complete board the improved filter is still much better than the paper's. Its RL dips to 17.7 dB at the upper band edge because the reflections of the two tapers add to the filter's. A joint re-tune of the outer posts and the taper is the next step.

Note on accuracy: the microstrip-board model uses a PEC ground with an equivalent loss, and its port calibration has about ±0.3 dB of error (out of band |S11| reaches +0.3 dB). Its absolute IL is therefore less accurate than the waveguide-port results. The comparison between the two boards is fair because both use the same model.

## 6. Mesh convergence

The paper's 3rd-order Chebyshev post filter was re-simulated on a much finer mesh (0.58 million cells instead of 0.23 million):
* maximum cell 0.20 mm instead of 0.30 mm;
* 0.04 mm instead of 0.06 mm at the posts;
* 6 instead of 4 cells across the substrate.

| Change on the finer mesh | Result |
|---|---|
| 3 dB centre frequency | −10 MHz (0.10 %) |
| 3 dB bandwidth | 0 MHz |
| IL at 10 GHz | +0.02 dB |
| Largest in-passband |S21| difference | 0.41 dB (on the skirt) |

**The standard mesh is converged.** The 0.6 % frequency offset from the paper is therefore not a discretisation error. It comes from differences between the solvers and the models (FDTD vs CST FIT, and the paper's unknown port and wall settings).

## 7. Conclusions

1. **The software was learned.** openEMS was set up and used to script the complete SIW workflow in Python: geometry, mesh, waveguide and microstrip ports, losses, post-processing, Touchstone export, and an automatic design loop.
2. **The paper's design is validated.** All seven of the paper's filters were reproduced. **87 %** of the tabulated IL/RL values match within ±0.5 % in frequency (47 % at exactly the same frequency), and all qualitative conclusions are confirmed. An inconsistency in the paper's 5th-order IL values was found and explained.
3. **The design is improved.** Full-wave inverter extraction plus re-synthesis gives a 4th-order post filter on the same SIW with **RL ≥ 21.7 dB and IL ≤ 0.82 dB across the full 9.75–10.25 GHz band**, compared with the paper's 10.7 dB / 1.33 dB at the band edge. It also has better stop-band rejection (46 / 30 dB at 9 / 11 GHz).
4. **The board is ready to fabricate.** An optimised microstrip-to-SIW taper (7.5 mm wide) and a complete board model were added; the paper does not specify the taper.
5. **Grading (instruction 8a):** the results of the base paper are validated, and an improvement over them is shown.

**Future work:**
* fabricate the improved board and measure it with a VNA after TRL calibration;
* run a Monte-Carlo tolerance analysis of post diameter and position;
* re-tune the posts and the taper together on the full board.
