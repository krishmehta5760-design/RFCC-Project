"""Comparison plots: base-paper design vs improved designs (all simulated in openEMS)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "sim_data")
OUT = os.path.abspath(os.path.join(HERE, "..", "04_Results", "plots"))
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)

def load(name):
    p = os.path.join(ROOT, name, "sparams.npz") if not name.endswith(".npz") else os.path.join(ROOT, name)
    z = np.load(p); return z["freq"]/1e9, z["s11"], z["s21"]

def spec_mask(ax):
    ax.add_patch(plt.Rectangle((9.75, -60), 0.5, 40, fc="g", alpha=.08, ec="g", ls="--"))
    ax.plot([9.75, 10.25], [-20, -20], "g--", lw=1.2, label="spec: RL ≥ 20 dB, 9.75–10.25 GHz")

imp = json.load(open(os.path.join(HERE, "..", "04_Results", "tables", "improved_design.json")))["variants"]

# 1. paper vs improved (waveguide-port models)
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
curves = [("post3_cheby", "Paper design (3rd order, Table 1)", "k", "--"),
          (imp["n3r003"]["last_sim"], "Improved 3rd order (0.03 dB)", "tab:orange", "-"),
          (imp["n4r003"]["last_sim"], "Improved 4th order (0.03 dB), same SIW", "tab:blue", "-")]
for name, lab, c, ls in curves:
    f, s11, s21 = load(name)
    for a in ax:
        a.plot(f, db(s21), color=c, ls=ls, lw=1.8, label="S21 " + lab)
        a.plot(f, db(s11), color=c, ls=ls, lw=1.0, alpha=.8, label="S11 " + lab)
for a in ax:
    spec_mask(a); a.grid(alpha=.4); a.set_xlabel("Frequency (GHz)"); a.set_ylabel("S-parameters (dB)")
ax[0].set(xlim=(8, 12), ylim=(-60, 2), title="Wide band")
ax[1].set(xlim=(9.4, 10.6), ylim=(-45, 1), title="Passband zoom")
ax[0].legend(fontsize=7, loc="lower left")
fig.suptitle("openEMS: base-paper post filter vs. improved designs (TE10 waveguide ports)")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "improved_vs_paper.png"), dpi=150); plt.close(fig)

# 2. passband IL zoom
fig, ax = plt.subplots(figsize=(7, 4))
for name, lab, c, ls in curves:
    f, s11, s21 = load(name)
    ax.plot(f, db(s21), color=c, ls=ls, lw=1.8, label=lab)
ax.axvspan(9.75, 10.25, color="g", alpha=.08)
ax.set(xlim=(9.5, 10.5), ylim=(-3, 0), xlabel="Frequency (GHz)", ylabel="|S21| (dB)",
       title="Insertion loss across the specified band")
ax.grid(alpha=.4); ax.legend(fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "improved_vs_paper_IL_zoom.png"), dpi=150); plt.close(fig)

# 3. plain SIW line
if os.path.exists(os.path.join(ROOT, "siw_line", "sparams.npz")):
    f, s11, s21 = load("siw_line")
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
    ax[0].plot(f, db(s11), "b"); ax[0].set(title="Plain SIW line: |S11|", ylabel="dB", xlabel="Frequency (GHz)", ylim=(-80, 0))
    ax[1].plot(f, db(s21), "r"); ax[1].set(title="Plain SIW line: |S21| (77.4 mm incl. feeds)", ylabel="dB", xlabel="Frequency (GHz)", ylim=(-0.4, 0))
    for a in ax: a.grid(alpha=.4); a.set_xlim(8, 12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "siw_line.png"), dpi=150); plt.close(fig)

# 4. analytical vs extracted K
tab = json.load(open(os.path.join(HERE, "..", "04_Results", "tables", "post_K_extraction.json")))
print("ok")
