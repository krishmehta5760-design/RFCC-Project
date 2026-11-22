"""
LIVE DEMO for the presentation.  Runs ONE filter from scratch in openEMS (nothing cached) and plots
the result on top of the saved result, so the professor can see the solver actually working.

Usage (from PowerShell):
  $py = "C:\\Users\\KRISH MEHTA\\openEMS_install\\py313\\tools\\python.exe"
  & $py demo_live.py                 # paper's 3rd-order Chebyshev iris filter   (~1-2 min)
  & $py demo_live.py line            # plain SIW line, no filter                (~20 s)
  & $py demo_live.py post3_cheby     # paper's 3rd-order Chebyshev post filter  (~2 min)
  & $py demo_live.py improved        # OUR improved 4th-order post filter       (~2 min)
  & $py demo_live.py improved --view # only open the 3-D model in AppCSXCAD (no simulation)

Fresh results go to sim_data_demo/ (safe to delete); the project results are not touched.
"""
import os, sys, json, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import matplotlib.pyplot as plt
from siw_model import build_and_run, metrics, expand_dims
from paper_designs import PAPER, LABELS, make_cfg

DEMO_ROOT = os.path.join(HERE, "sim_data_demo")
CACHE = os.path.join(HERE, "sim_data")
APPCSXCAD = r"C:\Users\KRISH MEHTA\openEMS_install\openEMS\AppCSXCAD.exe"

args = [a for a in sys.argv[1:] if not a.startswith("--")]
view_only = "--view" in sys.argv
key = args[0] if args else "iris3_cheby"

if key == "line":
    cfg, label, cached = dict(name="siw_line", kind="line", feed="wg"), "Plain SIW line (no filter)", "siw_line/sparams.npz"
elif key == "improved":
    d = np.load(os.path.join(CACHE, "improved_final.npz"))
    n = int(d["n"])
    d_full, L_full = expand_dims(list(d["d"]), list(d["L"]), n)
    cfg = dict(name="improved", kind="post", feed="wg", d_full=d_full, L_full=L_full)
    label, cached = f"Improved {n}th-order post filter (our design)", "improved_final.npz"
elif key in PAPER:
    cfg, label, cached = make_cfg(key), "Paper: " + LABELS[key], f"{key}/sparams.npz"
else:
    sys.exit(f"unknown design '{key}'. Use: line, improved, " + ", ".join(PAPER))

if view_only:
    r = build_and_run(dict(cfg, view_only=True), DEMO_ROOT)
    print("3-D model written to", r["xml"], "- opening AppCSXCAD (rotate with the mouse) ...")
    subprocess.Popen([APPCSXCAD, r["xml"]])
    sys.exit(0)

print(f"=== Simulating: {label} ===")
print("openEMS (FDTD) sends a short pulse covering 8-12 GHz down the waveguide and records what")
print("comes back (S11) and what gets through (S21).  Please wait ...", flush=True)
t0 = time.time()
r = build_and_run(cfg, DEMO_ROOT, verbose=0)
print(f"done in {time.time()-t0:.0f} s")

f, s11, s21 = r["freq"], r["s11"], r["s21"]
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)
if key != "line":
    m = metrics(f, s11, s21)
    print(f"  insertion loss at 10 GHz     : {m['IL_f0']:.2f} dB")
    print(f"  worst return loss 9.75-10.25 : {m['RL_min_band']:.1f} dB   (20 dB or more is the goal)")
    print(f"  worst insertion loss in band : {m['IL_max_band']:.2f} dB")
    print(f"  3 dB bandwidth               : {m['BW3dB_MHz']:.0f} MHz, centred at {m['f0_3dB_GHz']:.3f} GHz")
else:
    i = np.argmin(abs(f - 10e9))
    print(f"  at 10 GHz: S11 = {db(s11)[i]:.1f} dB (almost nothing reflected), S21 = {db(s21)[i]:.2f} dB (almost all passes)")

fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(f/1e9, db(s21), "C0", lw=2, label="S21 (transmitted) - just now")
ax.plot(f/1e9, db(s11), "C3", lw=2, label="S11 (reflected) - just now")
cfn = os.path.join(CACHE, cached)
if os.path.exists(cfn):
    c = np.load(cfn)
    ax.plot(c["freq"]/1e9, db(c["s21"]), "k--", lw=1, label="S21 saved project result")
    ax.plot(c["freq"]/1e9, db(c["s11"]), "k:", lw=1, label="S11 saved project result")
ax.axvspan(9.75, 10.25, color="g", alpha=0.08, label="pass band 9.75-10.25 GHz")
ax.axhline(-20, color="g", ls="--", lw=0.8)
ax.set(xlim=(8, 12), ylim=(-60, 2), xlabel="Frequency (GHz)", ylabel="dB", title="openEMS live run: " + label)
ax.grid(alpha=0.3); ax.legend(loc="lower right", fontsize=8)
fig.tight_layout()
out = os.path.join(DEMO_ROOT, f"demo_{key}.png")
fig.savefig(out, dpi=130)
print("plot saved to", out)
if plt.get_backend().lower() == "agg":
    # This Python has no window toolkit (no tkinter), so open the saved picture in the Windows image viewer.
    if hasattr(os, "startfile") and not os.environ.get("MPLBACKEND"):
        os.startfile(out)
else:
    plt.show()
