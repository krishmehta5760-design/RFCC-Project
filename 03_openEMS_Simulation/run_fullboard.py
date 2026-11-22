"""
Step G - microstrip-to-SIW tapered transition and the complete 96.4 mm x 20 mm board.

1. Back-to-back transition (50-ohm microstrip -> linear taper -> plain SIW -> taper -> microstrip)
   for several taper widths; the taper length is fixed by the paper's board length
   (96.4 mm - 59.421 mm SIW) / 2 = 18.49 mm  = 5 mm feed line + 13.49 mm taper.
2. Complete boards (microstrip ports, 50 ohm reference) for
     (a) the paper's 3rd-order Chebyshev post filter   (cf. paper Fig. 15a, simulated vs. measured)
     (b) the improved 3rd-order post filter
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from siw_model import build_and_run, metrics, write_s2p, expand_dims
from paper_designs import PAPER

ROOT = os.path.join(HERE, "sim_data")
RES = os.path.abspath(os.path.join(HERE, "..", "04_Results"))
db = lambda x: 20*np.log10(np.abs(x) + 1e-15)


def run(cfg):
    fn = os.path.join(ROOT, cfg["name"], "sparams.npz")
    if os.path.exists(fn):
        z = np.load(fn); return z["freq"], z["s11"], z["s21"]
    r = build_and_run(cfg, ROOT)
    return r["freq"], r["s11"], r["s21"]


def main():
    out = {}
    # ---------------------------------------------------------------- 1. transition sweep
    widths = [float(w) for w in os.environ.get("TAPER_WIDTHS", "5.5 6.5 7.5 8.5").split()]
    trans = {}
    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    for wt in widths:
        f, s11, s21 = run(dict(name=f"trans_wt{wt:.2f}", kind="line", feed="msl", w_taper=wt))
        band = (f >= 9.0e9) & (f <= 11.0e9)
        trans[wt] = dict(S11_max_9_11=float(db(s11)[band].max()), IL_10GHz=float(-np.interp(10e9, f, db(s21))))
        ax.plot(f/1e9, db(s11), lw=1.5, label=f"S11, taper width {wt} mm")
        print("taper", wt, trans[wt], flush=True)
    ax.set(xlim=(8, 12), ylim=(-50, 0), xlabel="Frequency (GHz)", ylabel="|S11| (dB)",
           title="Back-to-back microstrip-SIW transition (taper length 13.49 mm)")
    ax.grid(alpha=.4); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "plots", "transition_sweep.png"), dpi=150); plt.close(fig)
    best_wt = min(trans, key=lambda w: trans[w]["S11_max_9_11"])
    out["transition"] = dict(sweep=trans, best_w_taper=best_wt)
    f, s11, s21 = run(dict(name=f"trans_wt{best_wt:.2f}", kind="line", feed="msl", w_taper=best_wt))
    write_s2p(os.path.join(RES, "touchstone", "transition_back_to_back.s2p"), f, s11, s21,
              f"Back-to-back MSL-SIW transition, taper width {best_wt} mm")

    # ---------------------------------------------------------------- 2. complete boards
    boards = {}
    p = PAPER["post3_cheby"]
    d_full, L_full = expand_dims(p["d"], p["L"], 3)
    boards["board_paper_post3"] = dict(d_full=d_full, L_full=L_full, label="Paper post filter (Table 1) on full board")
    imp = os.path.join(ROOT, "improved_final.npz")
    if os.path.exists(imp):
        z = np.load(imp)
        d_full, L_full = expand_dims(list(z["d"]), list(z["L"]), int(z["n"]))
        boards["board_improved_post3"] = dict(d_full=d_full, L_full=L_full, label="Improved post filter on full board")
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for name, b in boards.items():
        f, s11, s21 = run(dict(name=name, kind="post", feed="msl", w_taper=best_wt,
                               d_full=b["d_full"], L_full=b["L_full"]))
        m = metrics(f, s11, s21)
        out[name] = m
        write_s2p(os.path.join(RES, "touchstone", f"{name}.s2p"), f, s11, s21, b["label"])
        ls = "--" if "paper" in name else "-"
        ax.plot(f/1e9, db(s11), "b"+ls, lw=1.6, label="S11 " + b["label"])
        ax.plot(f/1e9, db(s21), "r"+ls, lw=1.6, label="S21 " + b["label"])
        print(name, {k: round(v, 3) for k, v in m.items()}, flush=True)
    ax.axvspan(9.75, 10.25, color="0.9", zorder=0)
    ax.set(xlim=(8, 12), ylim=(-60, 2), xlabel="Frequency (GHz)", ylabel="S-parameters (dB)",
           title="Complete 96.4 mm x 20 mm boards with 50-ohm microstrip ports (openEMS)")
    ax.grid(alpha=.4); ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "plots", "full_board_comparison.png"), dpi=150); plt.close(fig)
    json.dump(out, open(os.path.join(RES, "tables", "full_board_results.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
