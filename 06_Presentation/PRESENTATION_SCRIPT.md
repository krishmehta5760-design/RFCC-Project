# Presentation Script – SIW Band-Pass Filter at X-Band

**Total: 10 minutes.**
* Slides 1–8 take about 6 minutes 20 seconds.
* The live demo (slide 9) takes about 3 minutes.
* The conclusion (slide 10) takes 30 seconds.

**Speakers:**
* **Member 1:** slides 1–4 and 10.
* **Member 2:** slides 5–8.
* **The demo:** Member 2 talks while Member 1 types (or the other way round, whatever you practise).

How to read this script:
* *[Square brackets in italics]* = what to **do** (point, click, type).
* Normal text = what to **say**. You don't have to say it word for word. Say it in your own words, but keep the numbers exact.

---

## Part A – The plan for the day

### A1. The evening before (30 minutes)
1. Put your names and roll numbers on slide 1 (click the placeholder text and type).
2. Rehearse the whole thing **once, out loud, with a timer**, including the demo. If you go over 10 minutes, cut words from slides 2–4, never from slide 7 (the result).
3. Run the demo once (Part C). It should take about 3 minutes.
4. Charge the laptop. Note: openEMS runs about 30 % slower on battery.

### A2. Fifteen minutes before you start
1. Close every Word file from the project folder and anything else heavy (browser tabs, games). The simulation needs the CPU.
2. Open **PowerShell** and type these two lines (copy them from slide 9 if you like), pressing Enter after each:

```powershell
cd "C:\Users\KRISH MEHTA\Desktop\SIW_Filter_Xband_openEMS\03_openEMS_Simulation"
```

```powershell
$py = "C:\Users\KRISH MEHTA\openEMS_install\py313\tools\python.exe"
```

3. Make the PowerShell text big enough to read from the back: right-click the PowerShell title bar → **Properties** → **Font** → size 20 or more.
4. Open the folder `04_Results\plots` in File Explorer. This is your backup if the demo fails.
5. Open the presentation and start **Slide Show → From Beginning**. If you have two screens, use **Presenter View** (Slide Show tab → tick "Use Presenter View"), so you see the notes and a timer while the professor sees only the slides.
6. Switching between the slides and PowerShell: press **Alt+Tab**. Practise this once.

### A3. Golden rules while presenting
* **Talk to the professor, not to the screen.** Glance at the slide, then look up.
* **Point at what you talk about.** Move the mouse in the slide show and the arrow pointer appears; press **Ctrl+A** if it is hidden.
* **Say every number with its meaning.** Not "21.7 dB" but "21.7 dB – less than 1 % of the power is reflected".
* **Slow down on slides 7 and 9.** They are your result and your proof.
* **Hand-overs are one sentence:** "Now [name] will show the results."
* If you don't know an answer, say: "We didn't look at that, but I would expect … because …" Don't guess numbers.

---

## Part B – The script, slide by slide

### Slide 1 – Title  ·  Member 1  ·  20 s

> Good morning. Our project is a **substrate integrated waveguide band-pass filter for X-band**, centred at 10 GHz.
>
> We took a published research paper, rebuilt all of its filters in the free 3-D electromagnetic simulator **openEMS** to check its results, and then we **improved the design**.
>
> *[Point at the drawing.]* This is our final filter: a waveguide made inside an ordinary circuit board by two rows of metal vias, with five metal posts inside it.

**Transition:** "First, why build a waveguide inside a circuit board at all?"

---

### Slide 2 – Why a substrate integrated waveguide?  ·  Member 1  ·  50 s

> At 10 GHz there are two classic options.
>
> *[Point at card 1.]* A **metal waveguide** has very low loss, but it is bulky, expensive, and hard to connect to chips.
>
> *[Card 2.]* A **microstrip line** is cheap and flat, but at 10 GHz it is too lossy to make a sharp filter.
>
> *[Card 3.]* A **substrate integrated waveguide**, or SIW, gives us both. The top and bottom copper of a normal circuit board act as the waveguide walls, and two rows of plated holes – vias – act as the side walls. So we get a low-loss waveguide made with a cheap PCB process.
>
> *[Point at the four tiles.]* Our specifications come from the base paper: centre frequency **10 GHz**, a pass band of **500 MHz**, from 9.75 to 10.25 GHz, on Rogers RT/Duroid 5870 board with permittivity **2.33**.
>
> The paper designs **seven filters**, with posts and with irises, of 3rd and 5th order. It gives every dimension, so we could rebuild all of them exactly.

**Transition:** "Let me show how such a filter works."

---

### Slide 3 – How an SIW post filter works  ·  Member 1  ·  1 min

> This is the paper's 3rd-order post filter, as we modelled it, seen from above.
>
> *[Point at the two long rows of dots.]* **One:** these rows of vias are the side walls of the waveguide. The effective width is 14.98 mm. That puts the cut-off at 6.56 GHz, so exactly one wave pattern, the TE10 mode, travels through the whole X-band.
>
> *[Point at the four posts in the middle.]* **Two:** these are metal posts. Each post reflects part of the wave. In filter theory, it acts as an impedance inverter, which sets how strongly two neighbouring sections are coupled. The small outer posts couple strongly to the input and output; the big inner posts couple weakly.
>
> *[Point at the spaces between posts – the 11.6 and 12.9 mm arrows.]* **Three:** the spaces between the posts, about 12 mm or half a wavelength inside the guide, are **resonators**. Three resonators make a third-order filter.
>
> Before simulating anything, we did the design by hand with the paper's equations. Our resonator lengths match the paper's to **13 micrometres**.

**Transition:** "To check the paper's results, we used a full 3-D simulation."

---

### Slide 4 – Method: full-wave simulation in openEMS  ·  Member 1  ·  50 s

> The paper used the commercial tool CST. We used **openEMS**, which is free and open-source.
>
> openEMS works with scripts, not a drawing window.
>
> *[Box 1.]* A Python script builds the 3-D model: the board with its losses, the copper, the vias, the posts and the ports.
>
> *[Box 2.]* openEMS cuts this into about **200 000 tiny cells**, sends one short pulse that covers 8 to 12 GHz, and solves Maxwell's equations step by step in time. One filter takes one to two minutes.
>
> *[Box 3.]* Python then turns the result into **S11**, the reflected power, and **S21**, the transmitted power, at 801 frequencies.
>
> *[Point at the three green tiles.]* Before trusting any filter, we checked the model three ways.
> 1. An empty waveguide reflects less than **−40 dB**, so the walls and ports are right.
> 2. Its loss is **3.0 dB per metre**, against 3.05 from theory.
> 3. A **2.5-times finer mesh** changed the result by only **0.1 %**, so the results are converged.

**Hand-over:** "Now [Member 2] will show what we found."

---

### Slide 5 – Validation: the paper's filters reproduced  ·  Member 2  ·  1 min

> We rebuilt all seven of the paper's filters with its exact dimensions, without any tuning.
>
> *[Point at the left plot.]* Here are the two 3rd-order Chebyshev filters. The **lines are openEMS**, and the **markers are the numbers printed in the paper**.
>
> *[Trace the dark line.]* The dark line is **S21**, what passes through. It is close to 0 dB inside the green band and falls away outside, so the filter passes 9.75 to 10.25 GHz and blocks the rest.
>
> *[Trace the copper line.]* The copper line is **S11**, what is reflected. It has **three dips**, one for each resonator.
>
> *[Point at the 87 % tile.]* **87 %** of the paper's 38 numbers match ours if we allow a 0.5 % frequency shift between the two simulators.
>
> *[47 % tile.]* At exactly the same frequency it is **47 %**. The reason is that the band-edge values sit on very steep slopes, where a shift of only 50 MHz changes the value by several dB.
>
> *[7/7 tile.]* All seven filters were rebuilt, and **every conclusion of the paper is confirmed**.
>
> *[Point at the Finding box.]* We also found a mistake. The paper reports only **0.2 dB** of loss for its 5th-order filters. With this board material, theory gives **1.05 dB**, and openEMS gives **1.13 dB**. A 5th-order filter cannot lose less than a 3rd-order one, so those paper values are not possible.

**Transition:** "Validation also showed us a real weakness in the paper's design."

---

### Slide 6 – The paper's design is poorly matched at the band edges  ·  Member 2  ·  50 s

> *[Point at 5.8 dB.]* Inside the band, the paper's post filter has a return loss of only **5.8 dB** at the edge. That means about a quarter of the power is reflected back. The usual target is **20 dB**, which means 1 % reflected.
>
> *[2.26 dB.]* The loss inside the band also rises to **2.26 dB**.
>
> *[Cause box.]* The cause: the paper read its post sizes from an old handbook chart.
>
> *[Point at the graph on the right.]* So we simulated a single post for ten different diameters and measured its real coupling – that is this curve. The **red crosses** are the paper's posts; the **green stars** are the sizes that are actually needed. The paper's posts couple **4 to 6 % too strongly**, and that is enough to spoil the matching.
>
> *[Point at the four steps.]* Our fix in four steps:
> 1. Use our measured curve instead of the chart.
> 2. Redesign with a smaller ripple, 0.03 dB, which targets about 21.6 dB return loss.
> 3. Use **four resonators** instead of three.
> 4. Let the script automatically re-tune the centre frequency. It converged in two runs.

**Transition:** "And this is the result."

---

### Slide 7 – Improved 4th-order filter meets the spec  ·  Member 2  ·  1 min *(slow down here)*

> *[Point at the green box.]* The green box is our specification: from 9.75 to 10.25 GHz, the reflection must stay **below the dashed −20 dB line**.
>
> *[Trace the grey dotted line.]* The **grey** curves are the paper's design. Its reflection leaves the box and rises to −5.8 dB at the upper edge.
>
> *[Trace the copper line.]* The **coloured** curves are our design. The copper reflection curve has **four dips** – four resonators – and stays **below −20 dB across the whole band**.
>
> *[Point at the three tiles, one by one.]* In numbers:
> * the worst return loss improves from **5.8 to 21.7 dB**;
> * the worst loss inside the band drops from **2.26 to 0.82 dB**;
> * and unwanted signals at 9 and 11 GHz are blocked better: **46 and 30 dB** instead of 33 and 24.
>
> *[Point at the small layout drawing.]* It uses the **same 59.4 mm waveguide on the same board**. Only the post sizes and positions changed.

**Transition:** "Finally, we looked at the complete board."

---

### Slide 8 – Complete board, and what is still open  ·  Member 2  ·  40 s

> A real board also needs a feed from the 50-ohm connector into the waveguide. The paper does not give it, so we designed a **tapered microstrip transition**; the best width is **7.5 mm**. Then we simulated the complete 96 × 20 mm board.
>
> *[Point at the plot and the two tiles.]* On the complete board our design is still far better: worst return loss **17.7 dB against 4.0**, worst loss **0.74 against 2.48 dB**.
>
> *[Limits box.]* To be honest about the limits:
> * This is **simulation only**. Nothing was built or measured.
> * On the full board our return loss dips to **17.7 dB at the upper edge**, because the tapers add small reflections of their own. Tuning the taper and the posts together is the next step.

**Transition:** "Now let us show it running live in openEMS."

---

### Slide 9 – Live demo  ·  both  ·  about 3 min

→ Follow **Part C** below step by step.

---

### Slide 10 – Conclusions  ·  Member 1  ·  30 s

> To conclude:
> 1. We learned openEMS and scripted the complete design flow in Python.
> 2. We validated the paper: 87 % of its numbers and all of its conclusions. We also found an error in its 5th-order loss values.
> 3. Our improved filter meets the 20 dB matching target across the whole band, with lower loss, on the same board.
> 4. We designed the feed transition and simulated the complete board.
>
> Next steps would be to fabricate it and measure it, tune the taper together with the posts, and check manufacturing tolerances.
>
> **Thank you – we are happy to take questions.**

*[Stop talking and wait. Silence is fine.]*

---

## Part C – The live demo, step by step (about 3 minutes)

Before you start: PowerShell is open in `03_openEMS_Simulation`, `$py` is set (A2), and the slide show is on slide 9. Press **Alt+Tab** to switch to PowerShell.

### Step 1 – Show the 3-D model (30 s)
*[Type, then Enter:]*

```powershell
& $py demo_live.py improved --view
```

A window called **AppCSXCAD** opens after about 5 seconds.

> This is openEMS's own viewer, AppCSXCAD. It shows the exact 3-D model that openEMS simulates.

*[Drag with the left mouse button to rotate; scroll to zoom.]*

> Here is the board, the two rows of vias that form the walls, the five posts inside, and the waveguide ports at both ends, where the signal goes in and comes out.

*[Close the AppCSXCAD window.]*

### Step 2 – Run the simulation live (2 min)
*[Type, then Enter:]*

```powershell
& $py demo_live.py improved
```

**While it runs (about 2 minutes), talk.** This is the best moment to explain:

> openEMS has cut the structure into about 250 000 cells. *[point at the "mesh" line]*
>
> Now it is sending a short pulse that contains all frequencies from 8 to 12 GHz into the filter, and stepping Maxwell's equations forward in time – each step is less than a picosecond.
>
> *[Point at the "Energy" numbers going down.]* This number is how much of the pulse is still bouncing around inside the filter. The simulation stops when it falls to −40 dB, when only 0.01 % is left.
>
> From the signals at the two ports, Python then calculates the reflection and transmission at every frequency.

The terminal then prints a small table (insertion loss, return loss, bandwidth) and the **plot opens** in the Photos app.

> *[Point at the plot.]* The coloured lines are the run we just did; the black dashed lines are our saved result from the project – they lie exactly on top of each other, so the result is reproducible.
>
> And as on slide 7: the copper reflection curve has four dips and stays below the green −20 dB line across the whole pass band.

*[Read one number from the terminal table aloud, e.g. "worst return loss 21.7 dB".]*

### Step 3 – Only if the professor asks you to change something (1 min)
**First say your prediction**, then run it. The most likely requests:

| Professor asks | Type | Say before Enter | Result |
|---|---|---|---|
| "Make it longer" | `& $py demo_live.py iris3_cheby --L=11.6,12.6` | "Longer resonators fit a longer wavelength, so the filter should move **down**." | 10.01 → 9.77 GHz |
| "Change the material" | `& $py demo_live.py iris3_cheby --er=2.2` | "Lower permittivity, waves travel faster, the filter moves **up**." | 10.01 → 10.30 GHz |
| "Make it wider" | `& $py demo_live.py iris3_cheby --d=7.0,4.6` | "Wider windows mean stronger coupling, so the band gets **wider**." | 660 → 825 MHz |
| "What if no loss?" | `& $py demo_live.py iris3_cheby --lossless` | "The shape stays the same, and the loss should go almost to **zero**." | 0.59 → 0.01 dB |

The iris filter is used here because it runs in 1 minute instead of 2. To see the current values first: `& $py demo_live.py iris3_cheby --show`.

In the plot, **black = original, colour = changed**, so the shift is easy to see.

### If something goes wrong
* **It takes too long or hangs:** press **Ctrl+C**, say "in the interest of time, here is the saved result", and open `04_Results\plots\improved_vs_paper.png`.
* **A red error appears:** don't try to fix it live. Show the saved plots and offer to show it again after the session.
* **The plot window doesn't appear:** it is saved in `03_openEMS_Simulation\sim_data_demo\`. Open the newest picture there.

*[Press Alt+Tab back to the slide show, then go to slide 10.]*

---

## Part D – Quick answers to likely questions

Keep each answer to two or three sentences. The long versions are in `PRESENTATION_GUIDE.md`, Part 6.

| Question | Short answer |
|---|---|
| Why 10 GHz? | It is the base paper's specification and the centre of X-band, used for radar and satellite links. |
| Why 500 MHz? | Also from the paper: 5 % of 10 GHz, a typical channel-filter width that posts and irises can realise easily. |
| What do S11 and S21 mean? | S11 is the power reflected back to the input; S21 is the power that passes to the output. Both are in dB: −20 dB means 1 %. |
| Why −20 dB as the target? | Less than 1 % of the power is reflected – the usual industry requirement. |
| Why is the loss not zero? | The board material (tan δ 0.0012) and the copper turn a little power into heat – about 0.6 dB for a 3rd-order filter. |
| Why only 47 % strict? | The band-edge values are on steep slopes. Our simulator is about 0.6 % lower in frequency than CST, and that changes edge values by several dB. With a ±0.5 % tolerance it is 87 %. |
| How do you know openEMS is right? | The empty waveguide matches theory (no reflection, loss 3.0 vs 3.05 dB/m), the mesh is converged (0.1 %), and the hand calculation matches the paper to 0.013 mm. |
| Why openEMS, not HFSS or CST? | It is free and open-source but still a full 3-D solver. Using a different solver from the paper also makes the validation independent. |
| Why posts and not irises? | Posts are the simplest to manufacture – just one more drilled hole – and gave a slightly wider bandwidth. |
| Doesn't 4th order add loss? | At the centre a little (0.68 vs 0.62 dB), but the worst loss in the band is much lower (0.82 vs 2.26 dB), and rejection is better. |
| Did you build it? | No – simulation only. Fabrication and measurement are future work. |
| What would you do next? | Fabricate and measure it, tune the taper and posts together on the full board, and do a tolerance analysis. |
