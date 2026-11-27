"""Single-column (3.5 in) vector figures for the IEEE-format paper, from the saved openEMS results.
Run with the openEMS Python:  & $py make_paper_figures.py   ->  08_Research_Paper/figs/*.pdf"""
import os, sys, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SIM = os.path.join(ROOT, "03_openEMS_Simulation")
sys.path.insert(0, SIM)
from paper_designs import PAPER_RESULTS
OUT = os.path.join(HERE, "figs"); os.makedirs(OUT, exist_ok=True)

plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "DejaVu Serif"], "mathtext.fontset": "stix",
                     "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 6.5, "xtick.labelsize": 7.5,
                     "ytick.labelsize": 7.5, "lines.linewidth": 1.1, "axes.linewidth": 0.6, "grid.linewidth": 0.4,
                     "legend.frameon": True, "legend.framealpha": 0.9, "legend.edgecolor": "0.8"})
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)
W = 3.45


def load(rel):
    d = np.load(os.path.join(SIM, "sim_data", rel))
    return d["freq"]/1e9, db(d["s11"]), db(d["s21"])


def band(ax):
    ax.axvspan(9.75, 10.25, color="0.88", lw=0, zorder=0)
    ax.axhline(-20, color="0.45", ls=(0, (4, 2)), lw=0.6, zorder=1)


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), bbox_inches="tight", pad_inches=0.02)
    plt.close(fig); print("saved", name)


# Fig. 2: validation of the two 3rd-order Chebyshev filters (lines: openEMS, markers: paper Table 3)
fig, axs = plt.subplots(2, 1, figsize=(W, 3.9), sharex=True)
for ax, key, title in [(axs[0], "post3_cheby", "(a) 3rd-order post filter"), (axs[1], "iris3_cheby", "(b) 3rd-order iris filter")]:
    f, s11, s21 = load(f"{key}/sparams.npz"); band(ax)
    ax.plot(f, s21, "k-", label=r"$|S_{21}|$ openEMS"); ax.plot(f, s11, "k--", lw=0.9, label=r"$|S_{11}|$ openEMS")
    pr = PAPER_RESULTS[key]; fx = [9.75, 10.0, 10.25]
    ax.plot(fx, [-v for v in pr["IL"]], "o", ms=3.6, mfc="white", mec="k", mew=0.8, label=r"$|S_{21}|$ [1] (CST)")
    ax.plot(fx, [-v for v in pr["RL"]], "s", ms=3.6, mfc="white", mec="k", mew=0.8, label=r"$|S_{11}|$ [1] (CST)")
    ax.set(ylim=(-50, 2), ylabel="dB"); ax.grid(alpha=0.3)
    ax.text(0.02, 0.06, title, transform=ax.transAxes, fontsize=7.5)
axs[1].set(xlim=(9.0, 11.0), xlabel="Frequency (GHz)")
axs[0].legend(loc="lower right", ncol=1)
fig.tight_layout(h_pad=0.4)
save(fig, "fig_validation.pdf")

# Fig. 3: extracted inverter value K(d) and phase phi(d) of a centred post
tab = json.load(open(os.path.join(ROOT, "04_Results", "tables", "post_K_extraction.json")))
d = np.array([t["d"] for t in tab]); K = np.array([t["K"] for t in tab]); ph = np.degrees([t["phi"] for t in tab])
fig, ax = plt.subplots(figsize=(W, 2.3))
ax.semilogy(d, K, "ko-", ms=3, label=r"$K/Z_0$ (openEMS)")
need = [0.3656, 0.1267]; paper_d = [0.7056, 2.2498]; paper_K = [0.3791, 0.1343]
dd = np.linspace(d.min(), d.max(), 400); KK = np.exp(np.interp(dd, d, np.log(K)))
for i, (pd_, pk, nk) in enumerate(zip(paper_d, paper_K, need)):
    dn = float(np.interp(-np.log(nk), -np.log(KK), dd))
    ax.plot(pd_, pk, "x", ms=6, mew=1.3, color="k", label="posts of [1]" if i == 0 else None)
    ax.plot(dn, nk, "^", ms=5, mfc="white", mec="k", mew=0.9, label="required by synthesis" if i == 0 else None)
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
ax.yaxis.set_major_locator(FixedLocator([0.1, 0.2, 0.3, 0.5])); ax.yaxis.set_major_formatter(FixedFormatter(["0.1", "0.2", "0.3", "0.5"]))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.set(xlabel="Post diameter $d$ (mm)", ylabel=r"$K/Z_0$"); ax.grid(alpha=0.3, which="major")
ax2 = ax.twinx(); ax2.plot(d, ph, color="0.5", ls="--", lw=1.0, label=r"$\varphi$ (right axis)")
ax2.set_ylabel(r"$\varphi$ (deg)", color="0.35"); ax2.tick_params(axis="y", colors="0.35")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper right")
fig.tight_layout(); save(fig, "fig_K.pdf")

# Fig. 4: published design vs. improved 4th-order design (waveguide ports)
fp, s11p, s21p = load("post3_cheby/sparams.npz")
z = np.load(os.path.join(SIM, "sim_data", "improved_final.npz"))
fi, s11i, s21i = z["freq"]/1e9, db(z["s11"]), db(z["s21"])
fig, ax = plt.subplots(figsize=(W, 2.5)); band(ax)
ax.plot(fp, s21p, color="0.55", ls="--", lw=1.0, label=r"$|S_{21}|$ design of [1]")
ax.plot(fp, s11p, color="0.55", ls=":", lw=1.0, label=r"$|S_{11}|$ design of [1]")
ax.plot(fi, s21i, "k-", label=r"$|S_{21}|$ proposed")
ax.plot(fi, s11i, "k-", lw=0.8, alpha=0.75, label=r"$|S_{11}|$ proposed")
ax.set(xlim=(9.0, 11.0), ylim=(-55, 2), xlabel="Frequency (GHz)", ylabel="dB"); ax.grid(alpha=0.3)
ax.legend(loc="lower left", ncol=1)
fig.tight_layout(); save(fig, "fig_improved.pdf")

# Fig. 6: complete boards with microstrip ports
fig, ax = plt.subplots(figsize=(W, 2.4)); band(ax)
for key, col, lab, lw in [("board_paper_post3", "0.55", "design of [1]", 1.0), ("board_improved_post3", "k", "proposed", 1.1)]:
    f, s11, s21 = load(f"{key}/sparams.npz")
    ls = "--" if col != "k" else "-"
    ax.plot(f, s21, color=col, ls=ls, lw=lw, label=r"$|S_{21}|$ " + lab)
    ax.plot(f, s11, color=col, ls=":" if col != "k" else "-", lw=0.8, alpha=0.85, label=r"$|S_{11}|$ " + lab)
ax.set(xlim=(9.0, 11.0), ylim=(-45, 2), xlabel="Frequency (GHz)", ylabel="dB"); ax.grid(alpha=0.3)
ax.legend(loc="lower left")
fig.tight_layout(); save(fig, "fig_board.pdf")
