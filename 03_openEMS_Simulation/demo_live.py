"""
LIVE DEMO for the presentation.  Runs ONE filter from scratch in openEMS (nothing cached) and plots it
on top of the saved project result.  You can also CHANGE the design from the command line and see what
happens - no code editing needed.

Basic use (PowerShell, inside 03_openEMS_Simulation):
  $py = "C:\\Users\\KRISH MEHTA\\openEMS_install\\py313\\tools\\python.exe"
  & $py demo_live.py                    # paper's 3rd-order Chebyshev iris filter   (~1 min)
  & $py demo_live.py line               # plain SIW line, no filter                (~20 s)
  & $py demo_live.py post3_cheby        # paper's 3rd-order Chebyshev post filter  (~2 min)
  & $py demo_live.py improved           # OUR improved 4th-order post filter       (~2 min)
  & $py demo_live.py improved --view    # only open the 3-D model in AppCSXCAD (no simulation)
  & $py demo_live.py post3_cheby --show # print the dimensions you can change

Changing the design (combine as you like):
  --d=0.8,2.4          post diameters (post filters) or iris window widths (iris filters), in mm,
                       from the outside to the middle (the filter is symmetric)
  --L=12.0,13.4        resonator lengths (distance between neighbouring posts/irises), in mm
  --er=2.2             substrate permittivity (paper: 2.33)
  --tand=0.0009        substrate loss tangent (paper: 0.0012)
  --lossless           switch off all losses (dielectric and copper)
Example:
  & $py demo_live.py iris3_cheby --L=11.6,12.6
The plot then shows the ORIGINAL design (black) and YOUR CHANGED design (colour), and a table of
what changed is printed.

Results go to sim_data_demo/ (safe to delete); the project results are never touched.
"""
import os, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import matplotlib.pyplot as plt
import siw_model
from siw_model import build_and_run, metrics, expand_dims
from paper_designs import PAPER, LABELS

DEMO_ROOT = os.path.join(HERE, "sim_data_demo")
CACHE = os.path.join(HERE, "sim_data")
APPCSXCAD = r"C:\Users\KRISH MEHTA\openEMS_install\openEMS\AppCSXCAD.exe"

# ---------------- command line ----------------
opts, args = {}, []
for a in sys.argv[1:]:
    if a.startswith("--"):
        k, _, v = a[2:].partition("=")
        opts[k] = v
    else:
        args.append(a)
key = args[0] if args else "iris3_cheby"
nums = lambda s: [float(x) for x in s.replace(";", ",").split(",") if x.strip()]

# ---------------- the design to start from ----------------
if key == "line":
    kind, n, d_half, L_half = "line", 0, [], []
    label, cached = "Plain SIW line (no filter)", "siw_line/sparams.npz"
elif key == "improved":
    z = np.load(os.path.join(CACHE, "improved_final.npz"))
    kind, n, d_half, L_half = "post", int(z["n"]), [float(x) for x in z["d"]], [float(x) for x in z["L"]]
    label, cached = f"Improved {n}th-order post filter (our design)", "improved_final.npz"
elif key in PAPER:
    p = PAPER[key]
    kind, n, d_half, L_half = p["kind"], p["n"], list(p["d"]), list(p["L"])
    label, cached = "Paper: " + LABELS[key], f"{key}/sparams.npz"
else:
    sys.exit(f"unknown design '{key}'. Use: line, improved, " + ", ".join(PAPER))

what_d = "iris window widths" if kind.startswith("iris") else "post diameters"
if "show" in opts:
    print(f"{label}\n  order n = {n}")
    if kind != "line":
        print(f"  --d  ({what_d}, outside -> middle, mm): " + ",".join(f"{x:.4f}" for x in d_half))
        print(f"  --L  (resonator lengths, outside -> middle, mm): " + ",".join(f"{x:.4f}" for x in L_half))
    print(f"  --er = {siw_model.SUB['er']}   --tand = {siw_model.SUB['tand']}")
    sys.exit(0)

# ---------------- apply the changes ----------------
changes = []
if "d" in opts and kind != "line":
    new = nums(opts["d"])
    if len(new) != len(d_half):
        sys.exit(f"--d needs {len(d_half)} values ({what_d}, outside -> middle), e.g. --d=" + ",".join(f"{x:.2f}" for x in d_half))
    d_half = new; changes.append(f"d={opts['d']}")
if "L" in opts and kind != "line":
    new = nums(opts["L"])
    if len(new) != len(L_half):
        sys.exit(f"--L needs {len(L_half)} values (outside -> middle), e.g. --L=" + ",".join(f"{x:.2f}" for x in L_half))
    L_half = new; changes.append(f"L={opts['L']}")
if "er" in opts:
    siw_model.SUB["er"] = float(opts["er"]); changes.append(f"er={opts['er']}")
if "tand" in opts:
    siw_model.SUB["tand"] = float(opts["tand"]); changes.append(f"tand={opts['tand']}")
lossless = "lossless" in opts
if lossless:
    changes.append("lossless")

if kind == "line":
    cfg = dict(name="siw_line", kind="line", feed="wg")
else:
    d_full, L_full = expand_dims(d_half, L_half, n)
    L_siw = max(59.421, round(sum(L_full) + 2*11.5, 3))
    cfg = dict(name=key, kind=kind, feed="wg", d_full=d_full, L_full=L_full, L_siw=L_siw)
if changes:
    cfg["name"] = key + "_changed"
if lossless:
    cfg["lossless"] = True

if "view" in opts:
    r = build_and_run(dict(cfg, view_only=True), DEMO_ROOT)
    print("3-D model written to", r["xml"], "- opening AppCSXCAD (rotate with the mouse) ...")
    subprocess.Popen([APPCSXCAD, r["xml"]])
    sys.exit(0)

# ---------------- run ----------------
title = label + ("   CHANGED: " + ", ".join(changes) if changes else "")
print(f"=== Simulating: {title} ===")
print("openEMS (FDTD) sends a short pulse covering 8-12 GHz down the waveguide and records what")
print("comes back (S11) and what gets through (S21).  Please wait ...", flush=True)
t0 = time.time()
r = build_and_run(cfg, DEMO_ROOT, verbose=0)
print(f"done in {time.time()-t0:.0f} s\n")

f, s11, s21 = r["freq"], r["s11"], r["s21"]
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)
cfn = os.path.join(CACHE, cached)
c = np.load(cfn) if os.path.exists(cfn) else None

if kind != "line":
    m = metrics(f, s11, s21)
    rows = [("centre frequency (GHz)", "f0_3dB_GHz", "{:.3f}"), ("3 dB bandwidth (MHz)", "BW3dB_MHz", "{:.0f}"),
            ("insertion loss at 10 GHz (dB)", "IL_f0", "{:.2f}"),
            ("worst return loss 9.75-10.25 GHz (dB, want >= 20)", "RL_min_band", "{:.1f}"),
            ("worst insertion loss 9.75-10.25 GHz (dB)", "IL_max_band", "{:.2f}"),
            ("rejection at 9 GHz (dB)", "rej_9GHz", "{:.1f}"), ("rejection at 11 GHz (dB)", "rej_11GHz", "{:.1f}")]
    if changes and c is not None:
        m0 = metrics(c["freq"], c["s11"], c["s21"])
        print(f"{'':52s}{'original':>10s}{'changed':>10s}")
        for name, k, fmt in rows:
            print(f"  {name:50s}{fmt.format(m0[k]):>10s}{fmt.format(m[k]):>10s}")
    else:
        for name, k, fmt in rows:
            print(f"  {name:50s}{fmt.format(m[k]):>10s}")
else:
    i = np.argmin(abs(f - 10e9))
    print(f"  at 10 GHz: S11 = {db(s11)[i]:.1f} dB (almost nothing reflected), S21 = {db(s21)[i]:.2f} dB (almost all passes)")

# ---------------- plot ----------------
fig, ax = plt.subplots(figsize=(10, 5.5))
tag = "changed design" if changes else "just now"
ax.plot(f/1e9, db(s21), "C0", lw=2, label=f"S21 (transmitted) - {tag}")
ax.plot(f/1e9, db(s11), "C3", lw=2, label=f"S11 (reflected) - {tag}")
if c is not None:
    ref = "original design" if changes else "saved project result"
    ax.plot(c["freq"]/1e9, db(c["s21"]), "k--", lw=1, label=f"S21 {ref}")
    ax.plot(c["freq"]/1e9, db(c["s11"]), "k:", lw=1, label=f"S11 {ref}")
ax.axvspan(9.75, 10.25, color="g", alpha=0.08, label="pass band 9.75-10.25 GHz")
ax.axhline(-20, color="g", ls="--", lw=0.8)
ax.set(xlim=(8, 12), ylim=(-60, 2), xlabel="Frequency (GHz)", ylabel="dB")
ax.set_title("openEMS live run: " + title, fontsize=10)
ax.grid(alpha=0.3); ax.legend(loc="lower right", fontsize=8)
fig.tight_layout()
out = os.path.join(DEMO_ROOT, f"demo_{cfg['name']}.png")
fig.savefig(out, dpi=130)
print("\nplot saved to", out)
if plt.get_backend().lower() == "agg":
    # This Python has no window toolkit (no tkinter), so open the saved picture in the Windows image viewer.
    if hasattr(os, "startfile") and not os.environ.get("MPLBACKEND"):
        os.startfile(out)
else:
    plt.show()
