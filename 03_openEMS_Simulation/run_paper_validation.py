"""
Steps C-E: simulate every filter of the base paper in openEMS and compare with the paper's
Tables 3 and 4.  Results -> ../04_Results
Usage:  python run_paper_validation.py [key1 key2 ...]     (default: all)
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from siw_model import build_and_run, metrics, write_s2p
from paper_designs import PAPER, PAPER_RESULTS, LABELS, make_cfg

ROOT = os.path.join(HERE, "sim_data")
RES = os.path.abspath(os.path.join(HERE, "..", "04_Results"))
for sub in ("plots", "touchstone", "tables"):
    os.makedirs(os.path.join(RES, sub), exist_ok=True)
FREQS = (9.75e9, 10.0e9, 10.25e9)


def load_or_run(key, **over):
    fn = os.path.join(ROOT, key, "sparams.npz")
    if os.path.exists(fn) and not over.get("force"):
        d = np.load(fn)
        return d["freq"], d["s11"], d["s21"]
    over.pop("force", None)
    r = build_and_run(make_cfg(key, **over), ROOT)
    return r["freq"], r["s11"], r["s21"]


def db(x): return 20*np.log10(np.abs(x) + 1e-15)


def value_near(freq, arr_db, f, tol=50e6, target=None):
    """value of arr_db within +/-tol of f that is closest to target (frequency-tolerant check)"""
    m = (freq >= f - tol) & (freq <= f + tol)
    v = arr_db[m]
    return float(v[np.argmin(np.abs(v - target))])


def check(sim, paper, kind):
    if paper is None: return None
    if kind == "IL":
        return abs(sim - paper) <= 0.5 or abs(sim - paper) <= 0.3*paper
    return abs(sim - paper) <= 3.0 or (sim >= 20 and paper >= 20) or abs(sim - paper) <= 0.3*paper


def main(keys):
    data, rows = {}, []
    for k in keys:
        print("=== running", k, flush=True)
        f, s11, s21 = load_or_run(k)
        data[k] = (f, s11, s21)
        write_s2p(os.path.join(RES, "touchstone", f"{k}.s2p"), f, s11, s21, LABELS[k] + " (base-paper dimensions)")
        m = metrics(f, s11, s21)
        pr = PAPER_RESULTS[k]
        S11, S21 = db(s11), db(s21)
        for i, fx in enumerate(FREQS):
            for q, arr in (("IL", -S21), ("RL", -S11)):
                p = pr[q][i]
                if p is None: continue
                sim = float(np.interp(fx, f, arr))
                near = value_near(f, arr, fx, target=p)
                rows.append(dict(case=k, label=LABELS[k], quantity=q, f_GHz=fx/1e9, paper=p,
                                 openEMS=round(sim, 2), strict_ok=check(sim, p, q),
                                 openEMS_within_50MHz=round(near, 2), tolerant_ok=check(near, p, q)))
        with open(os.path.join(RES, "tables", f"metrics_{k}.json"), "w") as fh:
            json.dump(m, fh, indent=1)
        # individual plot
        fig, ax = plt.subplots(figsize=(7, 4.2))
        ax.plot(f/1e9, S11, "b-", lw=1.8, label="S11 (openEMS)")
        ax.plot(f/1e9, S21, "r-", lw=1.8, label="S21 (openEMS)")
        for i, fx in enumerate(FREQS):
            if pr["IL"][i] is not None:
                ax.plot(fx/1e9, -pr["IL"][i], "rs", mfc="none", ms=8, label="paper IL (Table)" if i == 0 or pr["IL"][0] is None else None)
                ax.plot(fx/1e9, -pr["RL"][i], "bs", mfc="none", ms=8, label="paper RL (Table)" if i == 0 or pr["RL"][0] is None else None)
        ax.axvspan(9.75, 10.25, color="0.9", zorder=0)
        ax.set(xlim=(8, 12), ylim=(-60, 2), xlabel="Frequency (GHz)", ylabel="S-parameters (dB)", title=LABELS[k])
        ax.grid(alpha=.4); ax.legend(loc="lower left", fontsize=8)
        fig.tight_layout(); fig.savefig(os.path.join(RES, "plots", f"{k}.png"), dpi=150); plt.close(fig)

    # combined figures in the style of the paper
    def combo(keys2, title, fn):
        ks = [k for k in keys2 if k in data]
        if not ks: return
        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        sty = {"post": "--", "iris": "-", "iris_via": "-."}
        for k in ks:
            f, s11, s21 = data[k]; ls = sty[PAPER[k]["kind"]]
            ax.plot(f/1e9, db(s11), "b"+ls if "post" in k else "c"+ls, lw=1.6, label=f"S11 {LABELS[k]}")
            ax.plot(f/1e9, db(s21), "r"+ls if "post" in k else "m"+ls, lw=1.6, label=f"S21 {LABELS[k]}")
        ax.set(xlim=(8, 12), ylim=(-60, 2), xlabel="Frequency (GHz)", ylabel="S-parameters (dB)", title=title)
        ax.grid(alpha=.4); ax.legend(fontsize=7, loc="lower left")
        fig.tight_layout(); fig.savefig(os.path.join(RES, "plots", fn), dpi=150); plt.close(fig)
    combo(["post3_butter", "iris3_butter"], "openEMS: 3rd-order post & iris, Butterworth (cf. paper Fig. 8a)", "Fig8a_3rd_butterworth.png")
    combo(["post3_cheby", "iris3_cheby"], "openEMS: 3rd-order post & iris, Chebyshev (cf. paper Fig. 8b)", "Fig8b_3rd_chebyshev.png")
    combo(["post5_cheby", "iris5_cheby"], "openEMS: 5th-order post & iris, Chebyshev (cf. paper Fig. 9)", "Fig9_5th_chebyshev.png")
    combo(["iris3_cheby", "iris3_cheby_vias"], "openEMS: iris with copper walls vs small vias (cf. paper Fig. 11)", "Fig11_iris_walls_vs_vias.png")

    # validation table
    if rows:
        allrows = rows
        tfn = os.path.join(RES, "tables", "validation_table.json")
        if os.path.exists(tfn) and len(keys) < len(PAPER):
            old = [r for r in json.load(open(tfn)) if r["case"] not in keys]
            allrows = old + rows
        json.dump(allrows, open(tfn, "w"), indent=1)
        n = len(allrows)
        ns = sum(bool(r["strict_ok"]) for r in allrows); nt = sum(bool(r["tolerant_ok"]) for r in allrows)
        with open(os.path.join(RES, "tables", "validation_table.md"), "w", encoding="utf-8") as fh:
            fh.write("| Filter | Qty | f (GHz) | Paper (dB) | openEMS (dB) | OK | openEMS best within ±50 MHz | OK |\n|---|---|---|---|---|---|---|---|\n")
            for r in allrows:
                fh.write(f"| {r['label']} | {r['quantity']} | {r['f_GHz']:.2f} | {r['paper']} | {r['openEMS']} | {'YES' if r['strict_ok'] else 'no'} | {r['openEMS_within_50MHz']} | {'YES' if r['tolerant_ok'] else 'no'} |\n")
            fh.write(f"\n**Strict (same frequency): {ns}/{n} = {100*ns/n:.0f} % validated.  "
                     f"Frequency-tolerant (±50 MHz = ±0.5 %): {nt}/{n} = {100*nt/n:.0f} % validated.**\n")
        print(f"strict {ns}/{n}, tolerant {nt}/{n}")


if __name__ == "__main__":
    keys = sys.argv[1:] or list(PAPER.keys())
    main(keys)

