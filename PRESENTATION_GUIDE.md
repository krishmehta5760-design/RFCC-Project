# Presentation Guide – SIW Band-Pass Filter at X-Band (openEMS)

This guide assumes you know nothing about the project yet. Read it in order:

1. **Part 1** – the whole project in one minute (memorise this).
2. **Part 2** – the basic ideas, explained from zero.
3. **Part 3** – what was done, step by step.
4. **Part 4** – a slide-by-slide script for the presentation, with what to say.
5. **Part 5** – how to run the project and do a live demo.
6. **Part 6** – questions the professor is likely to ask, with answers.
7. **Part 7** – a one-page cheat sheet of numbers.

All figures named here are in `04_Results/plots`. The full numbers are in `RESULTS_AND_CONCLUSIONS.md`, and the full report is `05_Report/SIW_Filter_Xband_Project_Report.doc`.

---

## Part 1 – The project in one minute

> "We designed and simulated a **band-pass filter for 10 GHz (X-band)** built in **substrate integrated waveguide (SIW)** technology – a waveguide made inside an ordinary circuit board using two rows of metal vias.
>
> We took a published paper (Bandar and Türker Tokan, 2022) that compares two kinds of SIW filter – **post** filters and **iris** filters. We rebuilt **all seven of the paper's filters** in the free full-wave simulator **openEMS** and compared our results with the paper's tables. **87 %** of the paper's numbers agree with ours (within a 0.5 % frequency shift), and every conclusion of the paper is confirmed. We also found that the paper's 0.2 dB loss for its 5th-order filters is physically impossible with that material.
>
> Then we **improved the design**. The paper chose its post sizes from an old chart, so its filter is badly matched at the edges of the band. We measured the posts' real behaviour in openEMS and redesigned the filter as a 4th-order filter on the same board. Across the whole 9.75–10.25 GHz band, it reflects less than 1 % of the power (return loss ≥ 21.7 dB, against 10.7 dB in the paper) and has at most 0.82 dB of loss (against 1.33 dB). It also rejects unwanted frequencies better. Finally we designed the microstrip feed, which the paper does not give, and simulated the complete board."

---

## Part 2 – The basics, from zero

### 2.1 What is a band-pass filter?
A circuit that **lets one range of frequencies through and blocks the rest**. Ours must pass **9.75 to 10.25 GHz** (500 MHz wide, centred at 10 GHz) and block frequencies such as 9 GHz and 11 GHz. Every radar and satellite receiver has filters like this so that it only "hears" its own channel.

### 2.2 What is X-band?
The microwave range **8–12 GHz**. It is used for radar (weather, ships, aircraft, police speed guns) and satellite communication. At these frequencies the wavelength is only a few centimetres, so circuit dimensions of a few millimetres matter.

### 2.3 How filters are measured: S-parameters and decibels
Imagine sending power into the filter at port 1:
* **S11 (reflection):** how much comes **back** to port 1. We want it **small** in the pass band.
* **S21 (transmission):** how much gets **through** to port 2. We want it **close to 1 (0 dB)** in the pass band and **small** outside it.

Both are written in **decibels (dB)**. A quick table for reading the plots:

| dB value | Fraction of power |
|---|---|
| 0 dB | 100 % |
| −0.5 dB | 89 % |
| −1 dB | 79 % |
| −3 dB | 50 % (this defines the "3 dB bandwidth") |
| −10 dB | 10 % |
| −20 dB | 1 % |
| −40 dB | 0.01 % |

Two names used everywhere:
* **Insertion loss (IL) = −S21 in dB.** The power lost passing through. **Smaller is better.** IL = 0.82 dB means about 83 % gets through.
* **Return loss (RL) = −S11 in dB.** How well matched the filter is. **Bigger is better.** RL = 20 dB means only 1 % is reflected. **RL ≥ 20 dB is the usual industry target**, and it is our target.

### 2.4 What is a waveguide?
A hollow metal pipe with a rectangular cross-section. Microwaves travel inside it with very little loss. The standard X-band pipe is **WR-90 (22.86 mm × 10.16 mm)**.
* A waveguide only carries frequencies **above its cut-off frequency** (fc). Below fc nothing propagates.
* The basic field pattern is called the **TE10 mode**. Its electric field points from the top wall to the bottom wall and is strongest in the middle of the guide.
* **Guide wavelength (λg)** is the wavelength inside the guide. It is longer than in free space and is about 26 mm at 10 GHz in our guide.

Waveguides have very low loss, but they are bulky, expensive and hard to connect to chips.

### 2.5 What is a Substrate Integrated Waveguide (SIW)?
An SIW is **a waveguide built inside a printed circuit board**:
* the board's **top and bottom copper** layers are the top and bottom walls;
* **two rows of metal-plated holes (vias)** act as the side walls.

Look at `geom_post3_cheby.png`: the two long rows of black dots are the via walls.

**Why SIW?** It keeps most of the low loss of a waveguide, but it is **cheap, flat, light, and made by the same PCB process** as the rest of the circuit, so it connects directly to microstrip lines and chips.

Design rules (both are met in this project):
* via diameter d < λg/5, and via spacing p ≤ 2d, so that no energy leaks between the vias;
* the effective width **a_eff = a_s − d²/(0.95·p) = 14.976 mm**. This is exactly WR-90's width divided by √εr (22.86/√2.33). In other words, the board material makes the guide √2.33 times smaller.

Our board: **Rogers RT/Duroid 5870**, relative permittivity εr = 2.33, loss tangent tan δ = 0.0012, thickness 1.57 mm.

### 2.6 How an SIW filter works
1. Put metal obstacles across the guide at chosen places. Each obstacle **reflects part of the wave**.
2. The guide between two obstacles becomes a **resonator** – a small cavity about half a guide wavelength long (≈ 11–13 mm), where the wave bounces back and forth. A resonator only lets through frequencies near its resonance.
3. Several resonators **coupled in a chain** form a filter.
   * **Filter order n** = the number of resonators.
   * More resonators give **steeper edges** (better rejection), but more loss and a longer filter.

Two kinds of obstacle are compared in the paper:
* **Post (inductive post):** a single metal via in the centre of the guide. Bigger diameter → stronger reflection. This is the cheapest option because it is just another drilled hole.
* **Iris:** two metal walls coming in from the sides, leaving a window in the middle. A narrower window → stronger reflection. On a PCB it can be made as a row of small vias (paper Fig. 11).

In circuit theory each obstacle acts as an **impedance inverter (K)**. The value of K says how strongly two neighbouring resonators are coupled. A small K means weak coupling, which needs a big post or a narrow iris.

### 2.7 Butterworth vs Chebyshev
These are two standard "recipes" for the filter shape. Each recipe gives a set of numbers called **g-values**, and those give the K values.
* **Butterworth:** maximally flat pass band, but softer edges.
* **Chebyshev:** the pass band has a small, controlled ripple (here 0.1 dB), and the edges are steeper in return. **Smaller ripple means better matching:**

| Chebyshev ripple | Best RL in band |
|---|---|
| 0.1 dB (paper) | 16.4 dB |
| 0.03 dB (our design) | 21.6 dB |

This is why our improved design uses a 0.03 dB ripple.

### 2.8 What is openEMS / FDTD?
* **openEMS** is a free, open-source **3-D electromagnetic simulator**. You describe the structure (board, copper, vias, ports) in a Python script.
* It uses the **FDTD method (Finite-Difference Time-Domain)**:
  1. The space is cut into a 3-D grid of tiny boxes (the **mesh**, about 0.06–0.3 mm here).
  2. Maxwell's equations are stepped forward in time on that grid.
  3. A short pulse that contains all frequencies from 8 to 12 GHz is sent in, and the program records what comes back and what goes through.
  4. A Fourier transform turns these signals into S11 and S21 at every frequency, **all from one run**.
* The paper used **CST Microwave Studio** (a commercial tool using a similar method called FIT). openEMS was chosen because it is free, accurate, scriptable, and runs on our laptop.

### 2.9 Losses and unloaded Q
Energy is lost in the board material (tan δ) and in the copper. Together these give the resonators an **unloaded quality factor Qu ≈ 582** (higher is better). Cohn's formula then predicts the filter's minimum loss:

> IL ≈ 4.343 · Σg / (FBW · Qu)

where FBW is the fractional bandwidth (5 %). It gives 0.48 dB for 3rd order and 1.05 dB for 5th order. We use this formula to check the paper's numbers.

---

## Part 3 – What was done, step by step

| Step | What | Plain explanation | Result |
|---|---|---|---|
| A | Analytical design (`02_Design_Calculations`) | Used the paper's equations to compute the SIW width, the cut-off, λg, the g-values, the K values and the resonator lengths | a_eff = 14.976 mm, fc = 6.557 GHz. Our iris spacings 11.059 / 11.991 mm match the paper's 11.072 / 12.004 mm to 0.013 mm, which shows the theory is understood |
| B | Plain SIW line test | Simulated an empty SIW (no filter) to check the model before trusting it | S11 < −40 dB (perfect ports). Loss 3.0 dB/m against 3.05 dB/m from theory |
| C–E | Validation: all 7 paper filters | Built every filter with the paper's exact dimensions and no tuning, then compared IL and RL with paper Tables 3 and 4 | 87 % agree (within ±0.5 % frequency), 47 % at exactly the same frequency. All conclusions confirmed |
| F | Improvement | Measured the real K of a post for 10 diameters in openEMS, redesigned with a smaller ripple and one more resonator, then auto-tuned | 4th-order filter: RL ≥ 21.7 dB and IL ≤ 0.82 dB in the whole band |
| G | Transition and full board | Designed the microstrip-to-SIW taper (not given in the paper) and simulated the complete 96.4 × 20 mm board | Best taper width 7.5 mm. On the full board the improved filter still clearly beats the paper's |
| – | Mesh convergence | Re-ran a filter on a finer mesh (2.5× more cells) | Changed by only 0.1 % in frequency and 0.02 dB in IL, so the results are trustworthy |

---

## Part 4 – Slide-by-slide presentation script (12–15 minutes)

There is no slide deck yet. Put these figures on slides, or show them straight from `04_Results/plots`. A suggested split between the two members: **Member 1 presents slides 1–7** (background, theory, design, tool), and **Member 2 presents slides 8–14** (validation, improvement, board, conclusions). Both members should still read the whole guide, because the professor can ask either of you anything.

### Slide 1 – Title (30 s)
"Substrate integrated waveguide band-pass filter at X-band – validation and improvement of a published design using openEMS." Names, roll numbers, course.

### Slide 2 – Motivation (1 min)
* X-band (8–12 GHz) is used for radar and satellite links, and every receiver needs a band-pass filter.
* Metal waveguide filters have low loss but are bulky. **SIW** puts the waveguide into a PCB: low loss, cheap, flat.
* *Say:* "Our goal was to learn a full-wave EM tool, reproduce a published SIW filter, and then make it better."

### Slide 3 – Base paper and specifications (1 min)
* Paper: H. Bandar and N. Türker Tokan, *Sigma J. Eng. Nat. Sci.* 40(1), 2022 – post vs iris SIW band-pass filters.
* Specs: f0 = 10 GHz, BW = 500 MHz (9.75–10.25 GHz), Chebyshev 0.1 dB and Butterworth, orders 3 and 5, RT/Duroid 5870 (εr 2.33, h 1.57 mm).
* *Say:* "We chose this paper because it gives every dimension, so we can rebuild its filters exactly."

### Slide 4 – SIW and the filter structure (1.5 min)
Show `geom_post3_cheby.png` and `geom_iris3_cheby.png`.
* Point at the via rows: "these are the side walls of the waveguide".
* Point at the posts: "each post reflects part of the wave; the space between two posts is a resonator about 12 mm long".
* "3 resonators make a 3rd-order filter. The small outer posts give strong coupling to the ports; the big inner posts give weak coupling between resonators."

### Slide 5 – Design theory (1.5 min)
* SIW width rule → a_eff = 14.976 mm; cut-off 6.557 GHz, so only one mode propagates in the whole X-band.
* g-values → impedance inverters K → resonator lengths.
* *Say:* "Our own calculation of the iris spacings – 11.059 and 11.991 mm – matches the paper's 11.072 and 12.004 mm to within 13 micrometres."

### Slide 6 – The tool: openEMS (1 min)
* Free, open-source 3-D FDTD solver, controlled by our Python scripts (geometry, mesh, ports, losses, post-processing).
* Model: RT5870 substrate with dielectric loss, copper loss, via walls, posts or irises, and TE10 waveguide ports – the same set-up as the paper's CST simulation.
* Mention the run times: about 20 s for the plain line, 1–2 min per filter, 17 min for the full board.

### Slide 7 – Checking the model first (1 min)
Show `siw_line.png`.
* An empty SIW: almost nothing reflected (S11 < −40 dB), and loss 3.0 dB/m against 3.05 dB/m from theory.
* *Say:* "Before trusting any filter result we checked that the bare waveguide behaves exactly as theory predicts."

### Slide 8 – Validation of the paper (2 min)
Show `Fig8b_3rd_chebyshev.png`, then `Fig9_5th_chebyshev.png` and `Fig11_iris_walls_vs_vias.png`, and the table from `RESULTS_AND_CONCLUSIONS.md` §3.
* All 7 filters were rebuilt with the paper's dimensions and no tuning.
* **87 %** of the paper's 38 tabulated IL/RL values agree within ±0.5 % in frequency; **47 %** agree at exactly the same frequency.
* *Explain the 47 % honestly:* "The band-edge values sit on very steep slopes. openEMS puts our filters about 0.6 % lower in frequency than CST. That tiny shift changes a band-edge value by several dB, so we also report the frequency-tolerant score."
* All of the paper's **conclusions** are confirmed:
  * all filters are centred at 10 GHz;
  * the post filters have the wider bandwidth;
  * small vias can replace the iris walls;
  * the 5th-order filters are much more selective.

### Slide 9 – A finding: an error in the paper (45 s)
* The paper reports **0.2 dB** loss for its 5th-order filters. With this material, Cohn's formula gives **1.05 dB**, and openEMS gives **1.13–1.18 dB**.
* *Say:* "A 5th-order filter cannot have less loss than a 3rd-order one made in the same material. The paper's 5th-order runs were probably done without losses."

### Slide 10 – The problem we fixed (1.5 min)
* With the paper's post filter, the return loss inside the band drops to **5.8 dB** in openEMS (10.7 dB in the paper's own table). About 26 % of the power is reflected at the band edge.
* **Cause:** the paper read its post sizes from an old chart (the Marcuvitz Waveguide Handbook). Its posts give K = 0.379 and 0.134, but the design needs 0.366 and 0.127.
* Show `post_K_phi_extraction.png`: "We simulated a single post of 10 different diameters in openEMS and measured its real K and phase. This curve replaces the old chart."

### Slide 11 – Our improved filter (2 min)
Show `improved_vs_paper.png` (and `geom_improved_post4.png`).
* Method:
  1. Redesign with a 0.03 dB ripple instead of 0.1 dB (target RL 21.6 dB).
  2. Use 4 resonators instead of 3.
  3. Take the post sizes from our own K curve.
  4. Re-tune the centre frequency automatically – it converged in 2 runs.
* Result, on the **same 59.4 mm SIW**, with only post sizes and positions changed:

| | Paper's design (openEMS) | Paper's own table | **Our improved design** |
|---|---|---|---|
| Worst RL in band | 5.8 dB | 10.7 dB | **21.7 dB** |
| Worst IL in band | 2.26 dB | 1.33 dB | **0.82 dB** |
| Rejection at 9 GHz / 11 GHz | 33 / 24 dB | – | **46 / 30 dB** |

* *Say:* "The green box on the plot is the spec – RL of 20 dB or better from 9.75 to 10.25 GHz. The paper's design (black dashed) leaves the box; our design (blue) stays inside it across the whole band."

### Slide 12 – Transition and complete board (1 min)
Show `transition_sweep.png` and `full_board_comparison.png`.
* The paper does not give the microstrip taper, so we designed it: a 50 Ω line 4.66 mm wide, a 13.49 mm taper, and a best taper width of 7.5 mm (reflection below −21 dB from 9 to 11 GHz).
* On the complete 96.4 × 20 mm board: worst RL **17.7 dB vs 4.0 dB**, worst IL **0.74 dB vs 2.48 dB** (improved vs paper).
* *Be honest:* "On the full board our RL dips to 17.7 dB at the upper edge, because the tapers add their own small reflections. Tuning the posts and the taper together is the next step."

### Slide 13 – How sure are we? (45 s)
* Mesh convergence: a finer mesh (2.5× more cells) changed the centre frequency by 0.1 % and the IL by 0.02 dB.
* Model checks: the plain-line test, and agreement with the analytical spacings.
* **Limitations:** simulation only, nothing was fabricated or measured; the microstrip-port model has about ±0.3 dB of calibration error.

### Slide 14 – Conclusions and future work (1 min)
1. We learned openEMS and scripted the complete SIW design flow in Python.
2. We validated the paper: 87 % of its values (within ±0.5 % frequency) and all of its conclusions.
3. We found an inconsistency in the paper's 5th-order loss.
4. We improved the filter: RL ≥ 21.7 dB and IL ≤ 0.82 dB over the whole band, on the same board.
5. Future work: fabricate and measure, tune posts and taper together, and do a manufacturing-tolerance analysis.

### Slide 15 – Live demo / questions
Run the demo from Part 5 while you take questions (it takes about 1 minute).

---

## Part 5 – How to run the project and give a live demo

Everything is already installed. openEMS and a separate Python are in `C:\Users\KRISH MEHTA\openEMS_install`. Open **PowerShell** and go to the simulation folder:

```powershell
cd "C:\Users\KRISH MEHTA\Desktop\SIW_Filter_Xband_openEMS\03_openEMS_Simulation"
```

Store the path of the Python that has openEMS (repeat this in every new PowerShell window):

```powershell
$py = "C:\Users\KRISH MEHTA\openEMS_install\py313\tools\python.exe"
```

### 5.1 Re-make every result, plot and the report (about 1 minute)
Finished simulations are saved in `sim_data`, so this only re-creates the tables, plots and the Word report:

```powershell
& $py run_all.py
```

To redo every simulation from scratch (about 1.5 hours), delete the `sim_data` folder first. Don't do this right before the presentation.

### 5.2 Live demo – run a filter in front of the professor
`demo_live.py` simulates one filter **from scratch**. While it runs, the window prints openEMS progress, with the "energy" falling towards −40 dB. When it finishes, it prints the IL and RL and opens a plot (in the Windows image viewer) that draws the new result over the saved one. The two curves lie on top of each other, which shows the results are reproducible.

| Command | What it shows | Time |
|---|---|---|
| `& $py demo_live.py line` | Empty SIW: everything passes, nothing reflects | ~10 s |
| `& $py demo_live.py iris3_cheby` | The paper's 3rd-order iris filter | ~1 min |
| `& $py demo_live.py post3_cheby` | The paper's 3rd-order post filter | ~2 min |
| `& $py demo_live.py improved` | **Our improved 4th-order filter** | ~2 min |
| `& $py demo_live.py improved --view` | Opens the **3-D model** in the AppCSXCAD viewer (rotate with the mouse); no simulation | ~5 s |

The best demo is `improved --view` (show the 3-D structure), then `improved` (run it and show the curve inside the green spec box). The script ends by itself, and the plot opens in the Windows image viewer (Photos). It is also saved as `sim_data_demo/demo_<name>.png`.

The demo writes only to `sim_data_demo`, which is safe to delete, and never changes the project results. The message "Warning: No primitives found in property: copper" is normal: in this model the copper layers are the domain's boundaries rather than drawn objects.

### 5.3 Where to find things during the presentation

| You want | Open |
|---|---|
| Any plot | `04_Results/plots/*.png` |
| The validation table (all 38 values) | `04_Results/tables/validation_table.md` |
| All final numbers | `RESULTS_AND_CONCLUSIONS.md` |
| The report to submit (.doc) | `05_Report/SIW_Filter_Xband_Project_Report.doc` |
| The base paper | `01_Base_Paper/…pdf` |
| S-parameter files for another simulator | `04_Results/touchstone/*.s2p` |

---

## Part 6 – Questions the professor may ask

**Q1. Why SIW and not a normal metal waveguide or a microstrip filter?**
A metal waveguide has very low loss but is bulky and expensive. A microstrip filter is cheap but lossy at 10 GHz (low Q). SIW is in between: it is almost as low-loss as a waveguide (Qu ≈ 580 here), and it is made on a normal PCB that connects directly to microstrip circuits.

**Q2. Why do the vias have to be so close together?**
If the gaps between vias are too big, energy leaks out sideways. The rules d < λg/5 and p ≤ 2d keep the leakage negligible. Our values are d = 1.32 mm, p = 1.98 mm, and λg/5 = 4.99 mm, so both rules are met.

**Q3. What is a_eff and why is it smaller than the via spacing?**
The vias are round and have gaps, so the wave "sees" a wall slightly inside the via centres. a_eff = a_s − d²/(0.95p) = 14.976 mm. That equals 22.86/√2.33, so our SIW behaves exactly like a WR-90 waveguide filled with the board material.

**Q4. What is the cut-off frequency and why does it matter?**
fc = c/(2·a_eff·√εr) = 6.557 GHz for TE10. Below it nothing propagates. The next mode (TE20) starts at 13.1 GHz, so the guide is single-mode over the whole X-band. That is necessary for a clean filter.

**Q5. How does a post act like a filter element?**
In the TE10 mode the electric field is strongest at the centre of the guide. A metal post there shorts part of that field and stores magnetic energy, so it acts like a **shunt inductor**. An inductor with short pieces of line on each side behaves like an **impedance inverter K**, which sets how strongly two neighbouring resonators are coupled.

**Q6. Why are the resonators about 11–13 mm long and not exactly λg/2 = 13 mm?**
Each post adds its own phase shift, so the line between two posts must be a bit shorter than λg/2 to resonate at 10 GHz. The paper's equations (and our extraction) include this phase.

**Q7. Post or iris – which is better?**
* The paper (and our simulations) show the post filter gives a slightly wider bandwidth for the same design.
* The post filter is easier to make: it is one drilled hole per obstacle.
* The iris can be made from small vias (Fig. 11) with almost no change in the response.
* Both have similar loss.

**Q8. What does FDTD actually do?**
1. It divides space into a grid of small cells.
2. It updates the electric and magnetic fields step by step in time using Maxwell's equations.
3. One short broadband pulse is sent in; recording the signals at the ports and taking a Fourier transform gives S-parameters over the whole 8–12 GHz band from a single run.

**Q9. Why openEMS and not HFSS or CST?**
HFSS and CST need paid licences. openEMS is free and open-source, and it is a proper full-wave 3-D solver that has been validated in many publications. Using a different solver from the paper also makes our validation independent.

**Q10. How do you know your simulation is right?**
Four checks:
1. The empty SIW line matches theory: no reflection, and a loss of 3.0 dB/m against 3.05 dB/m.
2. Mesh convergence: a finer mesh (2.5× more cells) changes the results by only 0.1 % in frequency and 0.02 dB in IL.
3. Our analytical design matches the paper's dimensions to 0.013 mm.
4. 87 % of the paper's values are reproduced.

**Q11. Why is your strict validation score only 47 %?**
The band-edge values (9.75 and 10.25 GHz) sit on very steep slopes of the response, where 50 MHz changes the value by several dB. openEMS places the post filters about 0.6 % lower than CST. This comes from solver differences (FDTD vs FIT, staircased round vias, the paper's unknown port and boundary settings), not from mesh error, which we checked. Allowing a ±0.5 % shift, 87 % match. The centre values and all conclusions match.

**Q12. You say the paper's 0.2 dB loss is wrong. How can you be sure?**
The loss of a filter grows with the number of resonators. Cohn's formula gives 1.05 dB for 5th order with tan δ = 0.0012 and copper loss, and our full-wave simulation gives 1.13–1.18 dB. Even the paper's own 3rd-order filters have 0.68–0.89 dB, so a 5th-order filter cannot have only 0.2 dB. Their 5th-order simulations were most likely run without losses.

**Q13. What exactly is your improvement?**
The paper's post sizes came from reading a chart by eye, so the couplings are about 4–6 % too strong, and the filter is badly matched at the band edges (RL 5.8 dB in our model, 10.7 dB in their table). We:
1. measured the real coupling K of a post versus its diameter in openEMS;
2. redesigned with a smaller ripple (0.03 dB, so RL ≥ 21.6 dB in theory);
3. used 4 resonators instead of 3;
4. auto-tuned the centre frequency.

The result: RL ≥ 21.7 dB and IL ≤ 0.82 dB over the full 9.75–10.25 GHz band, and better rejection at 9 and 11 GHz (46 and 30 dB) – on the same board size and with the same fabrication process.

**Q14. Doesn't a 4th-order filter have more loss?**
Each extra resonator adds loss, so the loss at the centre is a little higher (0.68 dB vs 0.62 dB). But the **worst-case** loss inside the band is much lower (0.82 dB vs 2.26 dB), because the paper's design is so badly matched at the band edge. In return we get much better rejection.

**Q15. What is K extraction?**
We simulated a single post in the SIW for 10 diameters (0.4–3.0 mm). From each result's S11 and S21 we calculated the equivalent inverter value K and its phase φ. That gives a curve "diameter → K", which we used to pick the post sizes instead of the old chart (`post_K_phi_extraction.png`).

**Q16. What is the microstrip taper for?**
The connector and the rest of the circuit use a 50 Ω microstrip line (4.66 mm wide), but the SIW has a different field pattern and impedance. A gradually widening taper converts one into the other with little reflection. We swept its end width and found 7.5 mm best (back-to-back reflection below −21 dB from 9 to 11 GHz).

**Q17. Why does the full board only reach 17.7 dB RL?**
The two tapers add their own small reflections to the filter's. At the upper band edge they add up. The filter itself (with ideal waveguide ports) reaches 21.7 dB. A joint re-tune of the outer posts and the taper would fix it; that is our next step. The improved board is still far better than the paper's board (4.0 dB).

**Q18. Why did you use waveguide ports for the validation and not microstrip?**
The paper's Tables 3 and 4 come from simulations with waveguide ports in CST. Using the same kind of port makes the comparison fair and separates the filter from the transition. The transition was then added separately in the full-board model.

**Q19. Did you build or measure anything?**
No. This is a simulation project. Fabrication and VNA measurement (with TRL calibration) are listed as future work. All results are clearly labelled as simulated.

**Q20. What is Qu and what limits the loss?**
* Qu is the unloaded quality factor of one resonator: how slowly it loses energy.
* We have Qd = 833 from the dielectric (1/tan δ) and Qc ≈ 1935 from the copper, which combine to Qu ≈ 582.
* The dielectric loss dominates, so a lower-loss board material would reduce the IL most.

**Q21. How were the two members' tasks divided?**
State your real split. The suggested split in `00_IMPLEMENTATION_PLAN.md` §3:
* Member A: literature, analytical design, improvement.
* Member B: openEMS line model, validation.
* Both: the paper filters, the results and the report.

**Q22. What are the main applications?**
X-band radar front-ends (weather, marine and airborne radar), satellite communication receivers, and point-to-point radio links – anywhere a compact, low-loss, cheap filter is needed at about 10 GHz.

---

## Part 7 – Cheat sheet

| Item | Value |
|---|---|
| Centre frequency / band | 10 GHz / 9.75–10.25 GHz (500 MHz, 5 %) |
| Substrate | RT/Duroid 5870, εr 2.33, tan δ 0.0012, h 1.57 mm |
| SIW | vias d 1.32 mm, pitch 1.98 mm, row spacing 15.90 mm, a_eff 14.976 mm, length 59.42 mm |
| Cut-off TE10 / TE20 | 6.557 GHz / 13.11 GHz |
| λg at 10 GHz | 26.0 mm |
| Qu (estimate) | ≈ 582 |
| Validation | 87 % (±0.5 % freq) · 47 % strict · 7 of 7 filters · all conclusions confirmed |
| Paper error found | 5th-order IL 0.2 dB → really about 1.1 dB |
| Paper post filter (openEMS) | worst RL 5.8 dB, worst IL 2.26 dB in band |
| **Improved 4th-order filter** | **worst RL 21.7 dB, worst IL 0.82 dB, IL at 10 GHz 0.68 dB, rejection 46 / 30 dB at 9 / 11 GHz** |
| Improved post diameters | 0.573 / 2.124 / 2.515 / 2.124 / 0.573 mm |
| Improved spacings | 11.152 / 12.871 / 12.871 / 11.152 mm |
| Taper | 50 Ω line 4.66 mm, taper 13.49 mm long, 7.5 mm wide at the SIW |
| Full board, improved vs paper | worst RL 17.7 vs 4.0 dB · worst IL 0.74 vs 2.48 dB |
| Mesh convergence | Δf0 0.1 %, ΔIL 0.02 dB |
| Run times | line ~10–20 s · 3rd-order filter 1–2 min · full board ~17 min · everything ~1.5 h |

**If you remember only five things:**
1. SIW = a waveguide inside a PCB, made with two rows of vias.
2. Posts in the guide create resonators; 3 or 4 resonators make the filter.
3. We reproduced all 7 of the paper's filters in openEMS: 87 % agreement, all conclusions confirmed.
4. The paper's posts were sized from a chart, so its filter is poorly matched at the band edges. We measured the real post behaviour and redesigned: RL ≥ 21.7 dB and IL ≤ 0.82 dB over the full band.
5. Everything is simulation; fabrication and measurement are future work.
