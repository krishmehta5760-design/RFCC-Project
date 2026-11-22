"""Top-view drawings of the simulated openEMS models (from the saved geometry in info.json)."""
import os, json, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Polygon

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "sim_data")
OUT = os.path.abspath(os.path.join(HERE, "..", "04_Results", "plots"))

def draw(name, title, fn):
    info = os.path.join(ROOT, name, "info.json")
    if not os.path.exists(info): return
    J = json.load(open(info)); g = J["geo"]; cfg = J["cfg"]
    fig, ax = plt.subplots(figsize=(11, 3.2))
    Ls, W, a_s = g["Ls"], g["W"], g["a_s"]
    feed = cfg.get("feed", "wg")
    ax.add_patch(Rectangle((g["x_min"], -W/2), g["x_max"]-g["x_min"], W, fc="#f3e3c3", ec="k", lw=.6))
    ax.add_patch(Rectangle((-Ls/2, -W/2), Ls, W, fc="#e8b04b", ec="k", lw=.6, alpha=.6))
    if feed == "msl":
        w50, wt = cfg.get("w_msl", 4.66), cfg.get("w_taper", 6.5)
        Lt, Lm = cfg.get("L_taper", 13.49), cfg.get("L_msl", 5.0)
        for s in (-1, 1):
            ax.add_patch(Polygon([[s*Ls/2, -wt/2], [s*(Ls/2+Lt), -w50/2], [s*(Ls/2+Lt), w50/2], [s*Ls/2, wt/2]], fc="#e8b04b", ec="k", lw=.6))
            ax.add_patch(Rectangle((min(s*(Ls/2+Lt), s*(Ls/2+Lt+Lm)), -w50/2), Lm, w50, fc="#e8b04b", ec="k", lw=.6))
    else:
        for s in (-1, 1):
            x0 = s*(Ls/2) if s > 0 else g["x_min"]
            ax.add_patch(Rectangle((min(s*Ls/2, s*(Ls/2+9)), -7.488), 9, 14.976, fc="none", ec="b", ls="--", lw=.8))
    for (x, y) in g["vias"]:
        ax.add_patch(Circle((x, y), g["via_d"]/2, fc="k"))
    for (x, d) in g["posts"]:
        ax.add_patch(Circle((x, 0), d/2, fc="k"))
        ax.annotate(f"d={d:.3f}", (x, d/2+0.3), ha="center", fontsize=7)
    for (x, w) in g["irises"]:
        ax.plot([x, x], [w/2, a_s/2], "k-", lw=2.5); ax.plot([x, x], [-a_s/2, -w/2], "k-", lw=2.5)
        ax.annotate(f"w={w:.2f}", (x, 0), ha="center", fontsize=7)
    xs = [p[0] for p in g["posts"]] or [p[0] for p in g["irises"]]
    for i in range(len(xs)-1):
        ax.annotate("", (xs[i], -a_s/2+1.6), (xs[i+1], -a_s/2+1.6), arrowprops=dict(arrowstyle="<->", lw=.7))
        ax.text(0.5*(xs[i]+xs[i+1]), -a_s/2+2.0, f"{xs[i+1]-xs[i]:.3f}", ha="center", fontsize=7)
    ax.set_aspect("equal"); ax.set_xlim(g["x_min"]-1, g["x_max"]+1); ax.set_ylim(-W/2-1, W/2+1)
    ax.set_xlabel("x (mm)"); ax.set_ylabel("y (mm)"); ax.set_title(title, fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, fn), dpi=150); plt.close(fig)

if __name__ == "__main__":
    draw("post3_cheby", "openEMS model: paper 3rd-order Chebyshev post SIW filter (waveguide-port model)", "geom_post3_cheby.png")
    draw("iris3_cheby", "openEMS model: paper 3rd-order Chebyshev iris SIW filter (waveguide-port model)", "geom_iris3_cheby.png")
    draw("iris3_cheby_vias", "openEMS model: iris filter with small-via walls", "geom_iris3_vias.png")
    imp = json.load(open(os.path.join(HERE, "..", "04_Results", "tables", "improved_design.json")))["variants"]
    draw(imp["n4r003"]["last_sim"], "openEMS model: IMPROVED 4th-order post SIW filter (same 59.4 mm SIW)", "geom_improved_post4.png")
    draw(imp["n3r003"]["last_sim"], "openEMS model: improved 3rd-order post SIW filter", "geom_improved_post3.png")
    draw("board_improved_post3", "Complete board (96.4 mm x 20 mm): microstrip + taper + improved SIW filter", "geom_full_board_improved.png")
    draw("board_paper_post3", "Complete board (96.4 mm x 20 mm): microstrip + taper + paper SIW post filter", "geom_full_board_paper.png")
