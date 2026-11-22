"""Clean, large-font figures for the presentation slides (from the saved openEMS results).
Run with the openEMS Python:  & $py make_presentation_figures.py   ->  06_Presentation/figs/*.png"""
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
OUT = os.path.join(HERE, "figs")
os.makedirs(OUT, exist_ok=True)

NAVY, COPPER, GREY, GREEN, RED = "#14213D", "#B5651D", "#8A8F98", "#2E8B57", "#C0392B"
plt.rcParams.update({"font.size": 14, "axes.titlesize": 15, "axes.labelsize": 14, "legend.fontsize": 11.5,
                     "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)


def load(rel):
    d = np.load(os.path.join(SIM, "sim_data", rel))
    return d["freq"]/1e9, db(d["s11"]), db(d["s21"])


def spec(ax, top=True):
    ax.axvspan(9.75, 10.25, color=GREEN, alpha=0.10, lw=0)
    ax.axhline(-20, color=GREEN, ls="--", lw=1.2)
    if top:
        ax.text(10.0, 1.2, "pass band 9.75–10.25 GHz", ha="center", va="bottom", color=GREEN, fontsize=11)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=200)
    plt.close(fig)
    print("saved", name)


# 1) validation: openEMS curves + the paper's tabulated values (markers)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
for ax, key, title in [(axs[0], "post3_cheby", "3rd-order post filter"), (axs[1], "iris3_cheby", "3rd-order iris filter")]:
    f, s11, s21 = load(f"{key}/sparams.npz")
    ax.plot(f, s21, color=NAVY, lw=2.4, label="S21 openEMS")
    ax.plot(f, s11, color=COPPER, lw=2.0, label="S11 openEMS")
    pr = PAPER_RESULTS[key]
    fx = [9.75, 10.0, 10.25]
    ax.plot(fx, [-v for v in pr["IL"]], "o", ms=9, mfc="white", mec=NAVY, mew=2, label="S21 paper (CST)")
    ax.plot(fx, [-v for v in pr["RL"]], "s", ms=9, mfc="white", mec=COPPER, mew=2, label="S11 paper (CST)")
    spec(ax, top=False)
    ax.set(xlim=(9.0, 11.0), ylim=(-50, 3), xlabel="Frequency (GHz)", title=title)
    ax.set_xticks([9.0, 9.5, 10.0, 10.5, 11.0])
    ax.grid(alpha=0.25)
axs[0].set_ylabel("dB")
axs[1].legend(loc="lower right", framealpha=0.95)
save(fig, "fig_validation.png")

# 2) K(d) extraction with the paper's posts and the required values
tab = json.load(open(os.path.join(ROOT, "04_Results", "tables", "post_K_extraction.json")))
d = np.array([t["d"] for t in tab]); K = np.array([t["K"] for t in tab])
fig, ax = plt.subplots(figsize=(6.4, 4.8))
ax.semilogy(d, K, "o-", color=NAVY, lw=2.2, ms=7, label="openEMS-measured K(d)")
need = [0.3656, 0.1267]
paper_d = [0.7056, 2.2498]; paper_K = [0.3791, 0.1343]
dd = np.linspace(d.min(), d.max(), 400); KK = np.exp(np.interp(dd, d, np.log(K)))
for i, (pd_, pk, nk) in enumerate(zip(paper_d, paper_K, need)):
    dn = float(np.interp(-np.log(nk), -np.log(KK), dd))
    ax.plot(pd_, pk, "X", ms=13, color=RED, label="paper's posts" if i == 0 else None)
    ax.plot(dn, nk, "*", ms=17, color=GREEN, label="size actually needed" if i == 0 else None)
    ax.annotate("", xy=(dn, nk), xytext=(pd_, pk), arrowprops=dict(arrowstyle="->", color=GREY, lw=1.5))
ax.set(xlabel="post diameter d (mm)", ylabel="coupling K / Z0 (log scale)", title="Measured post coupling vs. diameter")
from matplotlib.ticker import FixedLocator, FixedFormatter, NullFormatter
ax.yaxis.set_major_locator(FixedLocator([0.1, 0.2, 0.3, 0.4])); ax.yaxis.set_major_formatter(FixedFormatter(["0.1", "0.2", "0.3", "0.4"]))
ax.yaxis.set_minor_formatter(NullFormatter())
ax.grid(alpha=0.25, which="major"); ax.legend(loc="upper right")
save(fig, "fig_K_extraction.png")

# 3) paper design vs improved design (TE10-port model)
fp, s11p, s21p = load("post3_cheby/sparams.npz")
z = np.load(os.path.join(SIM, "sim_data", "improved_final.npz"))
fi, s11i, s21i = z["freq"]/1e9, db(z["s11"]), db(z["s21"])
fig, ax = plt.subplots(figsize=(10, 5.2))
spec(ax)
ax.plot(fp, s21p, color=GREY, lw=2, ls="--", label="S21 paper design")
ax.plot(fp, s11p, color=GREY, lw=1.6, ls=":", label="S11 paper design")
ax.plot(fi, s21i, color=NAVY, lw=2.6, label="S21 improved 4th order")
ax.plot(fi, s11i, color=COPPER, lw=2.4, label="S11 improved 4th order")
ax.annotate("paper: reflection rises\nto −5.8 dB at band edge", xy=(10.25, -5.8), xytext=(10.38, -33),
            fontsize=11.5, color="#444", arrowprops=dict(arrowstyle="->", color=GREY))
ax.annotate("improved: below −20 dB\nacross the whole band", xy=(10.15, -21.7), xytext=(10.38, -43),
            fontsize=11.5, color=COPPER, arrowprops=dict(arrowstyle="->", color=COPPER))
ax.set(xlim=(9.2, 10.9), ylim=(-50, 4), xlabel="Frequency (GHz)", ylabel="dB")
ax.grid(alpha=0.25); ax.legend(loc="lower left", framealpha=0.95, ncol=2)
save(fig, "fig_improved.png")

# 4) complete boards (microstrip ports)
fig, ax = plt.subplots(figsize=(7.2, 4.8))
spec(ax)
for key, col, lab, ls in [("board_paper_post3", GREY, "paper filter + taper", "--"),
                          ("board_improved_post3", NAVY, "improved filter + taper", "-")]:
    fn = os.path.join(SIM, "sim_data", key, "sparams.npz")
    if not os.path.exists(fn):
        continue
    f, s11, s21 = load(f"{key}/sparams.npz")
    ax.plot(f, s21, color=col, lw=2.3, ls=ls, label="S21 " + lab)
    ax.plot(f, s11, color=COPPER if key.startswith("board_imp") else "#B9A48F", lw=1.8, ls=ls, label="S11 " + lab)
ax.set(xlim=(9.2, 10.9), ylim=(-45, 4), xlabel="Frequency (GHz)", ylabel="dB", title="Complete 96.4 × 20 mm board")
ax.grid(alpha=0.25); ax.legend(loc="lower left", fontsize=10, framealpha=0.95)
save(fig, "fig_board.png")
