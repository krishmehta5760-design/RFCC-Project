"""Builds the course-project report (Word .docx + .doc) from the simulation results."""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from docx_helpers import Report, docx_to_doc

BASE = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(BASE, "04_Results")
PL = os.path.join(RES, "plots")
TB = os.path.join(RES, "tables")
SIM = os.path.join(BASE, "03_openEMS_Simulation", "sim_data")
J = lambda fn: json.load(open(os.path.join(TB, fn), encoding="utf-8"))
f2 = lambda x: f"{x:.2f}"

val = J("validation_table.json")
imp = J("improved_design.json")
M = {k: J(f"metrics_{k}.json") for k in ["post3_butter", "post3_cheby", "iris3_butter", "iris3_cheby",
                                          "post5_cheby", "iris5_cheby", "iris3_cheby_vias"]}
FB = J("full_board_results.json") if os.path.exists(os.path.join(TB, "full_board_results.json")) else {}
conv = J("mesh_convergence.json") if os.path.exists(os.path.join(TB, "mesh_convergence.json")) else None
Kx = J("post_K_extraction.json")
calc = open(os.path.join(BASE, "02_Design_Calculations", "design_calculations.txt")).read()
n_all = len(val); n_strict = sum(bool(r["strict_ok"]) for r in val); n_tol = sum(bool(r["tolerant_ok"]) for r in val)
V4 = imp["variants"]["n4r003"]; V3 = imp["variants"]["n3r003"]; V2 = imp["variants"]["n3r002"]
m4, m3, m2, mp = V4["final"], V3["final"], V2["final"], M["post3_cheby"]

R = Report()
# ------------------------------------------------------------------ title page
R.doc.add_paragraph("\n\n")
R.title("RF Components and Circuits (RFCC) – Course Project Report", 16)
R.title("Design, Full-Wave Modelling and Analysis of a Substrate Integrated Waveguide (SIW) Band-Pass Filter at X-Band", 20)
R.title("Validation of a published design and an improved design using openEMS (FDTD)", 13, bold=False)
R.doc.add_paragraph("\n")
R.title("Submitted by:", 12)
R.title("Krish Mehta (241EC224)        Vishva Chavada (241EC212)", 12, bold=False)
R.title("Under the guidance of Dr. Nagavel B", 12, bold=False)
R.title("Department of Electronics and Communication Engineering, National Institute of Technology Karnataka, Surathkal", 11, bold=False)
R.doc.add_paragraph("\n")
R.title("Software tool: openEMS v0.37.0 (open-source EC-FDTD solver) with the CSXCAD Python interface", 11, bold=False)
R.title("Base paper: H. Bandar and N. Türker Tokan, Sigma J. Eng. Nat. Sci., 40(1), 45–56, 2022", 11, bold=False)
R.title("Submission date: 27-11-2026", 11, bold=False)
R.page_break()

# ------------------------------------------------------------------ abstract
R.h("Abstract", 1)
R.p("A third-order substrate integrated waveguide (SIW) band-pass filter for X-band (f0 = 10 GHz, BW = 500 MHz) "
    "was designed, modelled and analysed with the open-source full-wave FDTD solver openEMS. All design "
    "specifications were taken from a published journal paper, which compares centred-post and inductive-iris SIW "
    "filters on RT/Duroid 5870 (εr = 2.33, h = 1.57 mm). Seven filters from the paper were rebuilt and simulated "
    "from their published dimensions: 3rd-order post and iris filters with Butterworth and Chebyshev responses, "
    "5th-order Chebyshev post and iris filters, and an iris filter made of small vias. "
    f"Of the {n_all} numerical results in the paper's tables, {n_tol} ({100*n_tol/n_all:.0f} %) are reproduced "
    "within a ±0.5 % frequency tolerance. All centre frequencies, bandwidths, filter orders and qualitative "
    "conclusions of the paper are confirmed. "
    "The design was then improved. The inverter value K and phase φ of a centred post were extracted from "
    "full-wave simulations instead of read from Marcuvitz's chart. From these data a new 4th-order filter was "
    "synthesised that fits on the same 59.4 mm SIW length. Its return loss is "
    f"{m4['RL_min_band']:.1f} dB or better and its insertion loss {m4['IL_max_band']:.2f} dB or less over the whole "
    "9.75–10.25 GHz band. With the paper's dimensions, openEMS gives an in-band return loss as low as "
    f"{mp['RL_min_band']:.1f} dB and an insertion loss up to {mp['IL_max_band']:.2f} dB; the paper's own Table 3 "
    "reports 10.7 dB and 1.33 dB at the band edge. The stop-band rejection also improves, from "
    f"{mp['rej_9GHz']:.0f}/{mp['rej_11GHz']:.0f} dB to {m4['rej_9GHz']:.0f}/{m4['rej_11GHz']:.0f} dB at 9/11 GHz. "
    "Finally, a 50 Ω microstrip-to-SIW tapered transition was optimised and the complete 96.4 mm × 20 mm board "
    "was simulated, ready for fabrication.")

# ------------------------------------------------------------------ 1 intro
R.h("1. Introduction and Objective", 1)
R.p("The objective of this course project is to learn a software tool to design, model, implement and analyse an RF "
    "component. The component chosen is an SIW band-pass filter at X-band (8–12 GHz). X-band is used in weather, "
    "marine and air-traffic radar and in satellite links.")
R.p("A conventional rectangular waveguide (RW) filter has a very high quality factor (Q ≈ 5000–10000) and high power "
    "handling, but it is bulky, expensive and hard to integrate with planar circuits. Microstrip filters are cheap and "
    "planar, but their Q is low (≈ 50–100). An SIW bridges the two. Two rows of metallised via holes in a "
    "printed-circuit substrate replace the narrow walls of a waveguide, and the top and bottom copper layers act as "
    "the broad walls. The result keeps most of the waveguide's Q (≈ 500–1000) and shielding, while it can be made by "
    "an ordinary PCB process and connected directly to microstrip circuits.")
R.p("A band-pass filter is made by placing inductive discontinuities along the SIW. They form half-wavelength "
    "cavity resonators coupled through impedance inverters. Two kinds of discontinuity are studied: centred "
    "inductive posts and inductive irises.")
R.h("1.1 Choice of software: openEMS", 2)
R.bullets([("Full-wave 3-D solver: ", "openEMS uses the Equivalent-Circuit Finite-Difference Time-Domain (EC-FDTD) "
            "method. It models the vias, posts, irises, lossy dielectric and copper of the real structure."),
           ("Free and open source (GPL): ", "the paper used CST and HFSS, which need commercial licences. openEMS "
            "needs none. A different numerical method (FDTD instead of CST's FIT) also gives an independent check "
            "of the paper."),
           ("Broadband: ", "one time-domain run with a Gaussian pulse gives the whole 8–12 GHz response."),
           ("Scriptable: ", "every model is a Python script (CSXCAD geometry, openEMS solver, NumPy/Matplotlib "
            "post-processing), so the dimensions are parameters and automatic tuning loops are possible.")])

# ------------------------------------------------------------------ 2 base paper
R.h("2. Base Paper and Design Specifications", 1)
R.p("Base paper: H. Bandar and N. Türker Tokan, “Comparison of post and iris substrate integrated waveguide "
    "band-pass filters for X-Band applications,” Sigma Journal of Engineering and Natural Sciences, vol. 40, no. 1, "
    "pp. 45–56, 2022, DOI: 10.14744/sigma.2022.00004.", italic=True)
R.table(["Parameter", "Value (from the paper)"], [
    ["Centre frequency f0", "10 GHz"], ["Bandwidth", "500 MHz (9.75–10.25 GHz), FBW = 5 %"],
    ["Responses", "Chebyshev 0.1 dB ripple and Butterworth"], ["Orders", "3rd and 5th"],
    ["Substrate", "Rogers RT/Duroid 5870, εr = 2.33, tan δ = 0.0012, h = 1.57 mm, 35 µm Cu"],
    ["SIW", "via d = 1.3205 mm, pitch p = 1.9807 mm, row spacing as = 15.9028 mm, L = 59.421 mm, W = 20 mm"],
    ["Equivalent waveguide", "WR-90 (a = 22.86 mm) → a_eff = 22.86/√2.33 = 14.976 mm"],
    ["Iris made of vias", "via diameter 0.2 mm, 0.6 mm spacing"],
    ["Board size (with feeds)", "96.4 mm × 20 mm"],
    ["Paper's software", "CST Microwave Studio (simulation); Anritsu VNA (measurement)"]],
    "Design specifications taken from the base paper", widths=[5, 11])
R.table(["Filter", "d1", "d2", "d3", "L1", "L2", "L3"], [
    ["Post, Butterworth (3rd)", "0.6839", "2.6092", "–", "11.8278", "13.4635", "–"],
    ["Post, Chebyshev (3rd)", "0.7056", "2.2498", "–", "11.5898", "12.9377", "–"],
    ["Iris, Butterworth (3rd)", "6.5529", "3.6342", "–", "11.1705", "12.2438", "–"],
    ["Iris, Chebyshev (3rd)", "6.5046", "4.0802", "–", "11.0723", "12.0042", "–"],
    ["Post, Chebyshev (5th)", "0.7821", "2.4461", "2.8122", "11.8161", "13.4868", "13.7464"],
    ["Iris, Chebyshev (5th)", "6.3682", "3.8539", "3.4179", "11.2304", "12.2704", "12.3769"]],
    "Filter dimensions from the paper (mm). Post: d = post diameter; iris: d = window width; L = centre-to-centre spacing", font=9)

# ------------------------------------------------------------------ 3 theory
R.h("3. Theory and Analytical Design", 1)
R.h("3.1 SIW equivalent width", 2)
R.p("An SIW with via diameter d, pitch p and row spacing as behaves like a dielectric-filled rectangular waveguide of "
    "effective width:")
R.eq("a_eff = as − d² / (0.95 p)")
R.p("To avoid leakage between the vias, the design rules d < λg/5 and p ≤ 2d must hold. For the paper's SIW "
    "these give a_eff = 14.976 mm, the same as a_WR90/√εr. The TE10 cut-off is fc = c/(2 a_eff √εr) = 6.557 GHz and "
    "TE20 cuts off at 13.11 GHz, so the SIW is single-mode over the whole X-band. The via design rules are satisfied: "
    "d = 1.32 mm < λg/5 = 4.99 mm and p = 1.98 mm < 2d = 2.64 mm.")
R.h("3.2 Inverter-coupled filter design (paper Eqs. 1–12)", 2)
R.p("The guide wavelength is λg = λ/√(1 − (fc/f)²). The guide-wavelength fractional bandwidth is "
    "wλ = (λg1 − λg2)/λg0, with λg0 = (λg1 + λg2)/2. From the low-pass prototype g-values the inverter values are:")
R.eq("K01/Z0 = √(π wλ / (2 g0 g1)),   Kj,j+1/Z0 = (π wλ/2) / √(gj gj+1),   Xj,j+1/Z0 = (K/Z0) / (1 − (K/Z0)²)")
R.p("The resonator lengths follow from θj = π + ½(φj−1,j + φj,j+1) and Lj = λg0 θj / 2π, where φ is the phase of "
    "the discontinuity. A Python script (02_Design_Calculations/siw_design_calc.py) evaluates all these equations. "
    "Its main results are listed below.")
R.table(["Quantity", "Value"], [
    ["λg(9.75 GHz), λg(10 GHz), λg(10.25 GHz)", "27.218, 26.013, 24.930 mm"],
    ["w, wλ", "0.050, 0.0878"],
    ["g (Chebyshev 0.1 dB, n = 3)", "1, 1.0316, 1.1474, 1.0316, 1"],
    ["K01/Z0, K12/Z0 (Chebyshev, n = 3)", "0.3656, 0.1267"],
    ["L1, L2 from the thin-iris model", "11.059, 11.991 mm (paper's iris: 11.072, 12.004 mm, Δ = 0.013 mm)"],
    ["Estimated unloaded Q (cavity, Cu + dielectric)", "Qc ≈ 1935, Qd = 833, Qu ≈ 582"],
    ["Cohn loss estimate, centre IL", "3rd order: 0.48 dB; 5th order: 1.05 dB"]],
    "Analytical design results (full output in design_calculations.txt)", widths=[8, 8])
R.p("The analytical iris spacings agree with the paper's Table 1 to 0.013 mm, which confirms our reading of the "
    "design equations. Post spacings are longer than the thin-iris values because a post also has a series "
    "(capacitive) reactance Xa (paper Fig. 3).")

# ------------------------------------------------------------------ 4 modelling
R.h("4. openEMS Modelling Methodology", 1)
R.bullets([
    ("Geometry (CSXCAD): ", "x is the propagation direction, y the SIW width, z the substrate thickness. The substrate "
     "is εr = 2.33. Vias and posts are metal cylinders. Irises are zero-thickness metal walls running from the via "
     "rows to the window edge; for the Fig. 11 case they are rows of 0.2 mm vias at 0.6 mm pitch."),
    ("Losses: ", "dielectric loss is set as a conductivity κ = 2πf0ε0εr·tanδ. In the waveguide-port models the copper "
     "broad walls are the z-boundaries of the domain, and their loss (Rs = 26 mΩ at 10 GHz) is added as an equivalent "
     "loss tangent tanδc = 2βαc/k² = 4.6×10⁻⁴ (Pozar Eq. 3.96). In the full-board model the top copper is a 35 µm "
     "conducting sheet with σ = 5.8×10⁷ S/m."),
    ("Ports: ", "the validation and design models use TE10 rectangular-waveguide ports on short solid-wall feed "
     "sections of width a_eff, as in the paper's CST set-up. The port impedance is corrected for the dielectric "
     "filling: Z_TE = ωμ0/β with β = √(k0²εr − (π/a_eff)²). The full-board model uses 50 Ω microstrip ports."),
    ("Mesh: ", "graded rectilinear mesh, at most 0.30 mm along x (about λ/55 in the dielectric at 12 GHz), refined "
     "to 0.06 mm around posts and iris edges and 0.2 mm around the via rows, with 4 cells across the substrate. "
     "Mesh lines are fixed on every metal edge and sheet. Models have 0.1–0.4 million cells (1.1 million for the "
     "full board)."),
    ("Excitation and termination: ", "a Gaussian pulse covering 7.8–12.2 GHz; 8-cell PML at the port ends and MUR "
     "absorbing boundaries elsewhere; the run stops when the energy has fallen by 40 dB."),
    ("Post-processing: ", "S11 and S21 come from the incident and reflected port waves, using 801 frequency "
     "points. IL and RL are read at 9.75, 10.0 and 10.25 GHz, together with the 3 dB bandwidth, the RL ≥ 20 dB "
     "band and the rejection at 9 and 11 GHz. Touchstone (.s2p) files are exported.")])
R.fig(os.path.join(PL, "geom_post3_cheby.png"), "openEMS model of the paper's 3rd-order Chebyshev post filter (waveguide-port model; the dashed boxes are the port feed sections)")
R.fig(os.path.join(PL, "geom_iris3_cheby.png"), "openEMS model of the paper's 3rd-order Chebyshev iris filter")
R.h("4.1 Verification of the SIW model (plain SIW line)", 2)
R.p("Before modelling any filter, a plain SIW line with the paper's vias was simulated. |S11| stays below −40 dB "
    "from 8 to 12 GHz, which shows that the via-wall SIW and the solid-wall guide of width a_eff are equivalent and "
    "that the port set-up is correct. |S21| is about −0.2 dB over 77 mm, i.e. a loss of about 3 dB/m. This matches "
    "the analytical αd + αc = 0.35 Np/m = 3.05 dB/m.")
R.fig(os.path.join(PL, "siw_line.png"), "openEMS result for the plain SIW line (no resonators)")
if conv:
    R.h("4.2 Mesh convergence", 2)
    R.p(conv["text"])

# ------------------------------------------------------------------ 5 validation
R.page_break()
R.h("5. Validation of the Base-Paper Results", 1)
R.p("All seven filters of the paper were built from the published dimensions and simulated in openEMS without any "
    "tuning. The next four figures correspond to the paper's Figs. 8a, 8b, 9 and 11.")
R.fig(os.path.join(PL, "Fig8a_3rd_butterworth.png"), "openEMS: 3rd-order post and iris SIW filters, Butterworth response (paper Fig. 8a)")
R.fig(os.path.join(PL, "Fig8b_3rd_chebyshev.png"), "openEMS: 3rd-order post and iris SIW filters, Chebyshev response (paper Fig. 8b)")
R.fig(os.path.join(PL, "Fig9_5th_chebyshev.png"), "openEMS: 5th-order post and iris SIW filters, Chebyshev response (paper Fig. 9)")
R.fig(os.path.join(PL, "Fig11_iris_walls_vs_vias.png"), "openEMS: iris filter with copper walls vs. small vias (paper Fig. 11)")
R.h("5.1 Point-by-point comparison with paper Tables 3 and 4", 2)
R.p("Each IL and RL value in the paper's tables is compared with openEMS at the same frequency (strict check). It is "
    "also compared with the closest openEMS value within ±50 MHz (±0.5 %), which allows for the small frequency "
    "offset expected between two different solvers. The band-edge values sit on the steep skirts of the response, "
    "where a 0.5 % shift changes S21 by several dB. A value is counted as validated when IL agrees within 0.5 dB "
    "(or 30 %) and RL within 3 dB (or 30 %, or both values above 20 dB).")
rows = [[r["label"], r["quantity"], f"{r['f_GHz']:.2f}", r["paper"], r["openEMS"], "✓" if r["strict_ok"] else "✗",
         r["openEMS_within_50MHz"], "✓" if r["tolerant_ok"] else "✗"] for r in val]
R.table(["Filter", "Qty", "f (GHz)", "Paper (dB)", "openEMS (dB)", "OK", "openEMS ±0.5 % (dB)", "OK"], rows,
        "Validation of every numerical result in Tables 3 and 4 of the paper", font=8)
R.p(f"Result: {n_strict}/{n_all} ({100*n_strict/n_all:.0f} %) agree at exactly the same frequency, and "
    f"{n_tol}/{n_all} ({100*n_tol/n_all:.0f} %) agree within ±0.5 % in frequency.", bold_prefix="Validation score: ")
R.h("5.2 Global characteristics", 2)
rows = []
for k, lab in [("post3_butter", "Post 3rd Butterworth"), ("post3_cheby", "Post 3rd Chebyshev"),
               ("iris3_butter", "Iris 3rd Butterworth"), ("iris3_cheby", "Iris 3rd Chebyshev"),
               ("post5_cheby", "Post 5th Chebyshev"), ("iris5_cheby", "Iris 5th Chebyshev"),
               ("iris3_cheby_vias", "Iris 3rd (small vias)")]:
    m = M[k]
    rows.append([lab, f2(m["f0_3dB_GHz"]), f"{m['BW3dB_MHz']:.0f}", f2(m["IL_min"]), f2(m["IL_f0"]),
                 f"{m['rej_9GHz']:.1f}", f"{m['rej_11GHz']:.1f}"])
R.table(["Filter (openEMS)", "f0 (GHz)", "3 dB BW (MHz)", "min IL (dB)", "IL@10 GHz", "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"],
        rows, "Global characteristics of the paper's filters simulated in openEMS", font=9)
R.p("Confirmed findings of the paper:", bold_prefix="")
R.bullets([
    f"Every filter is centred at 10 GHz. The 3 dB centre frequencies lie between {min(M[k]['f0_3dB_GHz'] for k in M):.2f} and "
    f"{max(M[k]['f0_3dB_GHz'] for k in M):.2f} GHz (≤ 0.8 % offset).",
    "The responses have the designed orders: 3 or 5 reflection zeros for the Chebyshev filters, and maximally flat "
    "Butterworth curves.",
    "The centre-frequency IL of the 3rd-order filters (0.6–0.8 dB) and their RL (about 20 dB or better) agree with the paper.",
    "For the 3rd-order Chebyshev design the post filter has the wider bandwidth "
    f"({M['post3_cheby']['BW3dB_MHz']:.0f} MHz against {M['iris3_cheby']['BW3dB_MHz']:.0f} MHz for the iris), "
    "as the paper states.",
    "Replacing the iris walls with small vias leaves the response essentially unchanged; the paper's Fig. 11 "
    "shows the same.",
    "The 5th-order filters are much more selective (over 50 dB rejection at 9 and 11 GHz).",
])
R.h("5.3 Discussion of the differences", 2)
R.bullets([
    ("Small frequency offset: ", "openEMS places the post filters about 0.6 % lower and the iris filters within "
     "0.2 % of the paper. The mesh-convergence test (Section 4.2) moves f0 by only 0.1 %, so the offset is not a "
     "discretisation error of our model. It comes from modelling differences: a different numerical method "
     "(FDTD vs CST's FIT), the paper's unknown CST settings (port type and de-embedding, wall thickness, how the "
     "via walls are terminated), and possibly rounding of the published dimensions. Because the band edges lie on "
     "steep skirts, this offset accounts for most of the strict mismatches."),
    ("5th-order insertion loss: ", "the paper reports 0.2 dB at 10 GHz for the 5th-order filters, lower than its "
     "own 3rd-order filters (0.78–0.89 dB). This is physically implausible. With tan δ = 0.0012 and copper walls, "
     "Cohn's formula gives IL ≈ 4.343·Σg/(w·Qu) = 1.05 dB for the 5th order, and openEMS gives "
     f"{M['post5_cheby']['IL_f0']:.2f} dB (post) and {M['iris5_cheby']['IL_f0']:.2f} dB (iris). The paper's 5th-order "
     "simulations were probably run with lower losses. Our value is supported by both theory and full-wave "
     "simulation."),
    ("Measured results: ", "the paper's measured IL of about 4 dB is mostly cable, connector and fabrication-"
     "tolerance loss, as the paper itself says. Without fabrication it cannot be reproduced. Section 7 instead "
     "gives a complete board model with microstrip transitions."),
])

# ------------------------------------------------------------------ 6 improvement
R.page_break()
R.h("6. Improvement over the Base-Paper Design", 1)
R.h("6.1 Shortcoming of the published design", 2)
R.p("The paper's 3rd-order Chebyshev post filter does not cover the specified 500 MHz with a good match. Its own "
    "Table 3 gives RL = 14 dB and 10.7 dB and IL = 1.23 dB and 1.33 dB at 9.75 and 10.25 GHz. In openEMS the RL ≥ "
    f"20 dB band runs only from {mp['RL20_lo_GHz']:.2f} to {mp['RL20_hi_GHz']:.2f} GHz, and inside the specified band "
    f"the RL falls to {mp['RL_min_band']:.1f} dB and the IL rises to {mp['IL_max_band']:.2f} dB. The cause is that the "
    "post diameters were read by eye from Marcuvitz's chart (paper Fig. 3), so the actual inverter values differ "
    "from the required ones. Our full-wave extraction (below) gives K/Z0 = "
    f"{imp['paper_post_K_from_extraction']['K'][0]:.3f} and {imp['paper_post_K_from_extraction']['K'][1]:.3f} for the "
    "paper's posts, while the design needs 0.366 and 0.127. The coupling is therefore too strong and the resonators "
    "are detuned.")
R.h("6.2 Method: full-wave inverter extraction and re-synthesis", 2)
R.p("A single centred post in the SIW was simulated in openEMS (lossless) for diameters from 0.4 to 3.0 mm. The "
    "S-parameters were de-embedded to the post plane and the equivalent T-network was extracted (Matthaei; "
    "Uher–Bornemann):")
R.eq("jXs = (1 − S21 + S11)/(1 − S11 + S21),   jXp = 2S21/((1 − S11)² − S21²)")
R.eq("φ = −atan(2Xp + Xs) − atan(Xs),   K/Z0 = |tan(φ/2 + atan Xs)|")
R.table(["d (mm)"] + [f"{t['d']:.2f}" for t in Kx],
        [["K/Z0"] + [f"{t['K']:.3f}" for t in Kx], ["φ (deg)"] + [f"{np.degrees(t['phi']):.1f}" for t in Kx]],
        "openEMS-extracted inverter value and phase of a centred post at 10 GHz", font=8)
R.fig(os.path.join(PL, "post_K_phi_extraction.png"), "Full-wave inverter curves K(d) and φ(d): a digital replacement for the Marcuvitz chart of paper Fig. 3")
R.p("To obtain RL ≥ 20 dB with margin over the whole specification, the prototype ripple was lowered from 0.1 dB "
    "(RL 16.4 dB) to 0.03 dB (RL 21.6 dB), and the ripple band was widened slightly to 9.72–10.28 GHz to leave "
    "room for tolerances. Post diameters come from interpolating K(d). Spacings come from paper Eqs. 8–10 using "
    "the extracted phases. A short automatic loop then re-scales the spacings to centre the response at "
    "10.00 GHz. Three variants were made:")
R.table(["Design", "Order / ripple", "Post diameters d1, d2, (d3) (mm)", "Spacings L1, L2 (mm)", "Full-wave iterations"], [
    ["Improved A", "3 / 0.02 dB", ", ".join(f"{x:.4f}" for x in V2["final"]["d"]), ", ".join(f"{x:.4f}" for x in V2["final"]["L"]), str(len(V2["history"]))],
    ["Improved B", "3 / 0.03 dB", ", ".join(f"{x:.4f}" for x in V3["final"]["d"]), ", ".join(f"{x:.4f}" for x in V3["final"]["L"]), str(len(V3["history"]))],
    ["Improved C (final)", "4 / 0.03 dB", ", ".join(f"{x:.4f}" for x in V4["final"]["d"]), ", ".join(f"{x:.4f}" for x in V4["final"]["L"]), str(len(V4["history"]))]],
    "Improved designs (symmetric; the 4th-order filter has 5 posts d1-d2-d3-d2-d1 and spacings L1-L2-L2-L1)", font=9)
R.fig(os.path.join(PL, "geom_improved_post4.png"), "openEMS model of the improved 4th-order post filter. It fits in the paper's 59.4 mm SIW (post span 48.0 mm).")
R.h("6.3 Results of the improved designs", 2)
R.fig(os.path.join(PL, "improved_vs_paper.png"), "Paper design vs. improved designs, all simulated in openEMS under identical conditions. Green: specification mask (RL ≥ 20 dB from 9.75 to 10.25 GHz).", width_cm=16.5)
R.fig(os.path.join(PL, "improved_vs_paper_IL_zoom.png"), "Insertion loss across the specified band (green)")
def row(lab, m):
    return [lab, f2(m["RL_min_band"]), f2(m["IL_max_band"]), f2(m["IL_f0"]), f"{m['RL20_lo_GHz']:.2f}–{m['RL20_hi_GHz']:.2f}",
            f"{m['BW3dB_MHz']:.0f}", f"{m['rej_9GHz']:.1f}", f"{m['rej_11GHz']:.1f}"]
R.table(["Design", "min RL in 9.75–10.25 (dB)", "max IL in band (dB)", "IL @10 GHz (dB)", "RL ≥ 20 dB band (GHz)",
         "3 dB BW (MHz)", "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"],
        [["Paper Table 3 (CST)", "10.7", "1.33", "0.78", "n/a", "n/a", "n/a", "n/a"],
         row("Paper design (openEMS)", mp), row("Improved A, 3rd, 0.02 dB", m2), row("Improved B, 3rd, 0.03 dB", m3),
         row("Improved C, 4th, 0.03 dB", m4)],
        "Improvement summary (all openEMS values come from identical models; the first row is the paper's own data)", font=8)
R.p("Improved C (4th order) is selected as the final design because it improves every figure of merit at once:", bold_prefix="")
R.bullets([
    f"Matching: the RL is at least {m4['RL_min_band']:.1f} dB over the whole specified band. The paper's design reaches "
    f"10.7 dB in its own Table 3 and {mp['RL_min_band']:.1f} dB in openEMS.",
    f"Loss: the worst-case in-band IL is {m4['IL_max_band']:.2f} dB, against 1.33 dB (paper Table 3) and "
    f"{mp['IL_max_band']:.2f} dB (paper design in openEMS). The passband is flat because the band edges now lie "
    "inside the ripple band.",
    f"Selectivity: rejection is {m4['rej_9GHz']:.0f} dB at 9 GHz and {m4['rej_11GHz']:.0f} dB at 11 GHz, against "
    f"{mp['rej_9GHz']:.0f} and {mp['rej_11GHz']:.0f} dB. The 3 dB bandwidth stays similar "
    f"({m4['BW3dB_MHz']:.0f} MHz against {mp['BW3dB_MHz']:.0f} MHz).",
    "Same size and process: the five posts fit in the same 59.4 mm SIW and the same 96.4 mm × 20 mm board, made "
    "with the same plated-via process.",
    "Design method: the full-wave K-extraction converged in two simulations, against the paper's chart look-up "
    "followed by optimisation.",
])
R.p("The 3rd-order variants A and B also meet RL ≥ 20 dB across the band with the same number of posts as the "
    "paper and an even lower IL, but their wider skirts reduce the stop-band rejection near 11 GHz. This is the "
    "usual trade-off between ripple and selectivity for a fixed order.")

# ------------------------------------------------------------------ 7 full board
R.h("7. Microstrip-to-SIW Transition and Complete Board", 1)
R.p("The paper connects 50 Ω SMA connectors to the SIW through tapered microstrip lines but does not give the "
    "taper dimensions. We designed them in openEMS. The 50 Ω line width on RT/Duroid 5870 (h = 1.57 mm) is "
    "4.66 mm (Hammerstad). The taper length is fixed by the paper's board length: (96.4 − 59.421)/2 = 18.49 mm, "
    "made of a 5 mm feed line and a 13.49 mm linear taper. The taper width at the SIW was swept in a back-to-back "
    "model.")
if FB:
    tr = FB["transition"]
    R.table(["Taper width (mm)", "max |S11|, 9–11 GHz (dB)", "IL @10 GHz, back-to-back (dB)"],
            [[f"{float(w):.1f}", f2(v["S11_max_9_11"]), f2(v["IL_10GHz"])] for w, v in tr["sweep"].items()],
            "Back-to-back transition sweep (taper length 13.49 mm)")
    R.p(f"The best taper width is {tr['best_w_taper']} mm, which keeps |S11| below "
        f"{tr['sweep'][str(tr['best_w_taper'])]['S11_max_9_11'] if str(tr['best_w_taper']) in tr['sweep'] else min(v['S11_max_9_11'] for v in tr['sweep'].values()):.1f} dB from 9 to 11 GHz.")
R.fig(os.path.join(PL, "transition_sweep.png"), "Return loss of the back-to-back microstrip–SIW transition for several taper widths")
R.fig(os.path.join(PL, "geom_full_board_improved.png"), "Complete 96.4 mm × 20 mm board with the improved filter (fabrication layout)")
R.fig(os.path.join(PL, "full_board_comparison.png"), "Complete boards with 50 Ω microstrip ports: paper design vs. improved design")
if FB.get("board_paper_post3") and FB.get("board_improved_post3"):
    a, b = FB["board_paper_post3"], FB["board_improved_post3"]
    R.table(["Complete board", "min RL in band (dB)", "max IL in band (dB)", "IL @10 GHz (dB)", "3 dB BW (MHz)", "Rej. 9 GHz", "Rej. 11 GHz"],
            [["Paper filter + taper", f2(a["RL_min_band"]), f2(a["IL_max_band"]), f2(a["IL_f0"]), f"{a['BW3dB_MHz']:.0f}", f"{a['rej_9GHz']:.1f}", f"{a['rej_11GHz']:.1f}"],
             ["Improved filter + taper", f2(b["RL_min_band"]), f2(b["IL_max_band"]), f2(b["IL_f0"]), f"{b['BW3dB_MHz']:.0f}", f"{b['rej_9GHz']:.1f}", f"{b['rej_11GHz']:.1f}"]],
            "Complete-board results (openEMS, 50 Ω microstrip reference)", font=9)
if FB.get("board_improved_post3"):
    b = FB["board_improved_post3"]; a = FB["board_paper_post3"]
    R.p(f"With the transitions included, the improved board keeps IL ≤ {b['IL_max_band']:.2f} dB and RL ≥ "
        f"{b['RL_min_band']:.1f} dB across 9.75–10.25 GHz. The paper's filter on the same board gives "
        f"{a['IL_max_band']:.2f} dB and {a['RL_min_band']:.1f} dB. The improved board's RL drops a few dB at "
        "the upper band edge, below the 20 dB target, because the reflection of the two tapers "
        "(about −21 dB each) adds to that of the filter. Re-tuning the outer posts together with the taper, "
        "or using a longer taper, would recover the 20 dB margin. This is left as a next design iteration.")
R.p("The board model confirms that the improvement holds once the transitions are included. The microstrip-port "
    "model uses a PEC ground plane with an equivalent loss, and its port calibration has about ±0.3 dB of error "
    "(out of band |S11| reaches +0.3 dB). Its absolute IL is therefore less accurate than the waveguide-port "
    "results. The comparison between the two boards is still fair because both use exactly the same model.")

# ------------------------------------------------------------------ 8 conclusion
R.h("8. Conclusions", 1)
R.bullets([
    "openEMS, a free full-wave FDTD solver, was learned and used to build, mesh, excite and post-process SIW "
    "structures entirely from Python scripts. This meets the course objective.",
    "The SIW model was verified first: a plain SIW line gives |S11| < −40 dB and the analytical loss of about "
    "3 dB/m, which confirms the equivalent-width rule a_eff = as − d²/0.95p.",
    f"All seven filters of the base paper were reproduced from their published dimensions. {n_tol} of the {n_all} "
    f"tabulated IL/RL values ({100*n_tol/n_all:.0f} %) were validated within ±0.5 % in frequency "
    f"({n_strict}/{n_all} at exactly the same frequency). Every centre frequency, bandwidth, filter order and "
    "qualitative conclusion of the paper was confirmed.",
    "One inconsistency in the paper was found: the 0.2 dB IL reported for the 5th-order filters is not achievable "
    "with the stated substrate loss. Theory gives 1.05 dB and openEMS about 1.1 dB.",
    "An improved design was obtained with full-wave inverter extraction and re-synthesis. On the same SIW and board, "
    f"the 4th-order post filter has RL ≥ {m4['RL_min_band']:.1f} dB and IL ≤ {m4['IL_max_band']:.2f} dB over the "
    f"full 9.75–10.25 GHz band and better rejection ({m4['rej_9GHz']:.0f}/{m4['rej_11GHz']:.0f} dB at 9/11 GHz). "
    "The paper reports 10.7 dB / 1.33 dB at the band edge.",
    "An optimised 50 Ω microstrip-to-SIW taper and a complete fabrication-ready board model were added. The paper "
    "does not specify the taper.",
    "Future work: fabricate the improved board and measure it with a VNA after TRL calibration to remove the "
    "connector loss the paper reports, and run a Monte-Carlo tolerance analysis of post diameter and position.",
])
R.h("References", 1)
for ref in [
    "[1] H. Bandar and N. Türker Tokan, “Comparison of post and iris substrate integrated waveguide band-pass filters for X-Band applications,” Sigma J. Eng. Nat. Sci., 40(1), 45–56, 2022.",
    "[2] D. M. Pozar, Microwave Engineering, 4th ed., Wiley, 2011.",
    "[3] G. L. Matthaei, L. Young, E. M. T. Jones, Microwave Filters, Impedance-Matching Networks, and Coupling Structures, Artech House, 1980.",
    "[4] D. Deslandes and K. Wu, “Accurate modeling, wave mechanisms, and design considerations of a substrate integrated waveguide,” IEEE Trans. MTT, 54(6), 2516–2526, 2006.",
    "[5] D. Deslandes, “Design equations for tapered microstrip-to-substrate integrated waveguide transitions,” IEEE MTT-S IMS, 704–707, 2010.",
    "[6] X.-P. Chen and K. Wu, “Substrate integrated waveguide filters: design techniques and structure innovations,” IEEE Microwave Magazine, 15(6), 121–133, 2014.",
    "[7] T. Liebig, openEMS – Open Electromagnetic Field Solver, https://openems.de (v0.37.0, 2026).",
    "[8] N. Marcuvitz, Waveguide Handbook, McGraw-Hill, 1951."]:
    R.p(ref, align="left", size=10)

R.h("Appendix A – Project files", 1)
R.table(["Folder / file", "Content"], [
    ["00_IMPLEMENTATION_PLAN.md", "Implementation plan"], ["01_WHAT_AND_WHY.md", "What is implemented and why"],
    ["RESULTS_AND_CONCLUSIONS.md", "All numerical results and conclusions"],
    ["01_Base_Paper/", "Base paper (PDF)"],
    ["02_Design_Calculations/siw_design_calc.py", "Analytical design (paper Eqs. 1–12)"],
    ["03_openEMS_Simulation/siw_model.py", "openEMS model library (geometry, mesh, ports, post-processing)"],
    ["03_openEMS_Simulation/run_*.py", "Validation, improvement and full-board runs"],
    ["04_Results/plots, touchstone, tables", "All figures, .s2p files and tables"],
    ["05_Report/", "This report (.docx and .doc) and its generator"]], "Project files", widths=[7, 9], font=9)

out = os.path.join(HERE, "SIW_Filter_Xband_Project_Report.docx")
R.save(out)
print("saved", out)
docx_to_doc(out, out[:-1])
print("doc:", os.path.exists(out[:-1]))
