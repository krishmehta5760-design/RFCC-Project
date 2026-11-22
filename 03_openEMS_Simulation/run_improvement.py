"""
Step F - IMPROVED DESIGN of the 3rd-order SIW post filter.

Problem in the base paper: the 0.1 dB Chebyshev post filter only reaches RL = 14 dB / 10.7 dB
and IL = 1.23 / 1.33 dB at the band edges (9.75 / 10.25 GHz), so the specified 500 MHz band is
not covered with a good match. The posts were sized by eye from Marcuvitz's chart (paper Fig. 3).

Method used here:
  1. openEMS full-wave characterisation of ONE centred post in the SIW for a set of diameters
     (lossless): de-embed S-parameters to the post plane and extract the impedance-inverter
     value K/Z0 and the phase phi of the equivalent T-network (Matthaei / Uher-Bornemann):
         jXs = (1 - S21 + S11)/(1 - S11 + S21),   jXp = 2 S21/((1 - S11)^2 - S21^2)
         phi = -atan(2Xp + Xs) - atan(Xs),        K = |tan(phi/2 + atan(Xs))|
  2. Re-synthesise with a 0.02 dB-ripple Chebyshev prototype (RL >= 23 dB in-band) and a slightly
     wider ripple bandwidth (9.70-10.30 GHz), so that the full 9.75-10.25 GHz spec has margin.
  3. Interpolate post diameters from the extracted K(d) curve, compute spacings with the extracted
     phases (paper Eqs. 8-10).
  4. Full-wave verification and a short automatic tuning loop (centre-frequency scaling of the
     spacings and fine adjustment of the outer posts).
"""
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "02_Design_Calculations"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from siw_model import build_and_run, metrics, write_s2p, SIW, SUB, expand_dims
from openEMS.physical_constants import C0

ROOT = os.path.join(HERE, "sim_data")
RES = os.path.abspath(os.path.join(HERE, "..", "04_Results"))
os.makedirs(os.path.join(RES, "plots"), exist_ok=True)
er, a_eff = SUB["er"], SIW["a_eff"]
F0 = 10e9


def beta(f):
    k = 2*np.pi*f*np.sqrt(er)/C0
    return np.sqrt(k**2 - (np.pi/(a_eff*1e-3))**2)


def lam_g(f):
    return 2*np.pi/beta(f)*1e3      # mm


# ------------------------------------------------------------------ 1. post characterisation
def extract_post(d_list, L_siw=30.0):
    out = []
    for d in d_list:
        name = f"xpost_d{d:.3f}"
        fn = os.path.join(ROOT, name, "sparams.npz")
        if os.path.exists(fn):
            z = np.load(fn); f, s11, s21 = z["freq"], z["s11"], z["s21"]
        else:
            r = build_and_run(dict(name=name, kind="post", feed="wg", d_full=[d], L_full=[],
                                   L_siw=L_siw, lossless=True), ROOT)
            f, s11, s21 = r["freq"], r["s11"], r["s21"]
        # de-embed: measurement planes are 5 mm inside the domain ends, feed length 9 mm
        l = (L_siw/2 + 9.0 - 5.0)*1e-3
        b = beta(f)
        S11 = s11*np.exp(2j*b*l); S21 = s21*np.exp(2j*b*l)
        jXs = (1 - S21 + S11)/(1 - S11 + S21)
        jXp = 2*S21/((1 - S11)**2 - S21**2)
        Xs, Xp = np.imag(jXs), np.imag(jXp)
        phi = -np.arctan(2*Xp + Xs) - np.arctan(Xs)
        K = np.abs(np.tan(phi/2 + np.arctan(Xs)))
        i0 = np.argmin(abs(f - F0))
        out.append(dict(d=d, K=float(K[i0]), phi=float(phi[i0]), Xs=float(Xs[i0]), Xp=float(Xp[i0]),
                        S21_dB=float(20*np.log10(abs(s21[i0])))))
        print(f"post d = {d:.3f} mm: K/Z0 = {K[i0]:.4f}, phi = {np.degrees(phi[i0]):.2f} deg", flush=True)
    return out


# ------------------------------------------------------------------ 2. synthesis
def g_cheby(n, ripple_dB):
    beta_ = np.log(1/np.tanh(ripple_dB/17.37)); gam = np.sinh(beta_/(2*n))
    a = [np.sin((2*k-1)*np.pi/(2*n)) for k in range(1, n+1)]
    b = [gam**2 + np.sin(k*np.pi/n)**2 for k in range(1, n+1)]
    g = [1.0, 2*a[0]/gam]
    for k in range(2, n+1): g.append(4*a[k-2]*a[k-1]/(b[k-2]*g[-1]))
    g.append(1.0 if n % 2 else 1/np.tanh(beta_/4)**2)
    return np.array(g)


def synthesize(tab, n=3, ripple=0.02, f1=9.70e9, f2=10.30e9):
    lg1, lg2 = lam_g(f1), lam_g(f2)
    lg0 = 0.5*(lg1 + lg2)
    wl = (lg1 - lg2)/lg0
    g = g_cheby(n, ripple)
    K = [np.sqrt(np.pi*wl/(2*g[0]*g[1]))]
    for j in range(1, n): K.append(np.pi*wl/2/np.sqrt(g[j]*g[j+1]))
    K.append(np.sqrt(np.pi*wl/(2*g[n]*g[n+1])))
    K = np.array(K)
    dK = np.array([t["d"] for t in tab]); KK = np.array([t["K"] for t in tab]); PH = np.array([t["phi"] for t in tab])
    order = np.argsort(KK)
    d_of_K = lambda k: float(np.interp(np.log(k), np.log(KK[order]), dK[order]))
    ph_of_d = lambda d: float(np.interp(d, dK, PH))
    d = [d_of_K(k) for k in K]
    phi = [ph_of_d(x) for x in d]
    theta = [np.pi + 0.5*(phi[j] + phi[j+1]) for j in range(n)]
    L = [lg0*t/(2*np.pi) for t in theta]
    return dict(g=g.tolist(), K=K.tolist(), d=d, phi=phi, L=L, lg0=lg0)


def main():
    # --- 1. characterisation sweep
    d_list = [0.40, 0.55, 0.70, 0.85, 1.00, 1.40, 1.80, 2.20, 2.60, 3.00]
    tab = extract_post(d_list)
    json.dump(tab, open(os.path.join(RES, "tables", "post_K_extraction.json"), "w"), indent=1)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    ax[0].semilogy([t["d"] for t in tab], [t["K"] for t in tab], "o-")
    ax[0].set(xlabel="post diameter d (mm)", ylabel="K/Z0 at 10 GHz", title="openEMS-extracted inverter value")
    ax[1].plot([t["d"] for t in tab], [np.degrees(t["phi"]) for t in tab], "s-r")
    ax[1].set(xlabel="post diameter d (mm)", ylabel="phase phi (deg)", title="openEMS-extracted inverter phase")
    for a in ax: a.grid(alpha=.4, which="both")
    fig.tight_layout(); fig.savefig(os.path.join(RES, "plots", "post_K_phi_extraction.png"), dpi=150); plt.close(fig)

    # also report what the extraction says about the paper's posts
    paper_d = [0.7056, 2.2498]
    dK = np.array([t["d"] for t in tab]); KK = np.array([t["K"] for t in tab])
    paper_K = [float(np.exp(np.interp(x, dK, np.log(KK)))) for x in paper_d]

    summary = {}
    for tag, (n, ripple, f1, f2) in VARIANTS.items():
        summary[tag] = design_variant(tab, tag, n, ripple, f1, f2)
    json.dump(dict(paper_post_K_from_extraction=dict(d=paper_d, K=paper_K), variants=summary),
              open(os.path.join(RES, "tables", "improved_design.json"), "w"), indent=1, default=float)


# tag: (order, ripple dB, ripple-band lower edge, upper edge)
VARIANTS = {
    "n3r002": (3, 0.02, 9.70e9, 10.30e9),   # 3rd order, deep match, wide skirt
    "n3r003": (3, 0.03, 9.72e9, 10.28e9),   # 3rd order, closer to the paper's selectivity
    "n4r003": (4, 0.03, 9.72e9, 10.28e9),   # 4th order on the same SIW length -> best overall
}
FINAL_TAG = "n4r003"


def design_variant(tab, tag, n, ripple, f1, f2):
    # --- 2. synthesis
    syn = synthesize(tab, n=n, ripple=ripple, f1=f1, f2=f2)
    print(f"[{tag}] synthesis:", json.dumps(syn), flush=True)

    # --- 3/4. full-wave verification + tuning loop
    nd, nl = (n + 2)//2, (n + 1)//2
    d_half = list(syn["d"][:nd])
    L_half = list(syn["L"][:nl])
    history = []
    for it in range(6):
        d_full, L_full = expand_dims(d_half, L_half, n)
        name = f"improved_{tag}_it{it}"
        fn = os.path.join(ROOT, name, "sparams.npz")
        if os.path.exists(fn):
            z = np.load(fn); f, s11, s21 = z["freq"], z["s11"], z["s21"]
        else:
            r = build_and_run(dict(name=name, kind="post", feed="wg", d_full=d_full, L_full=L_full), ROOT)
            f, s11, s21 = r["freq"], r["s11"], r["s21"]
        m = metrics(f, s11, s21)
        # centre of the RL>=20 dB band (where reflection zeros are)
        f_c = 0.5*(m["RL20_lo_GHz"] + m["RL20_hi_GHz"]) if np.isfinite(m["RL20_lo_GHz"]) else m["f0_3dB_GHz"]
        bw20 = (m["RL20_hi_GHz"] - m["RL20_lo_GHz"]) if np.isfinite(m["RL20_lo_GHz"]) else 0
        history.append(dict(it=it, d=list(d_half), L=list(L_half), f_c=f_c, bw20=bw20, **m))
        print(f"it {it}: d={np.round(d_half,4)} L={np.round(L_half,4)}  fc={f_c:.4f}  RL20 band="
              f"{m['RL20_lo_GHz']:.3f}-{m['RL20_hi_GHz']:.3f}  RLmin(spec)={m['RL_min_band']:.2f}  ILmax(spec)={m['IL_max_band']:.2f}", flush=True)
        if m["RL_min_band"] >= 20 and abs(f_c - 10.0) < 0.02:
            break
        # centre-frequency correction: resonator spacing scales ~ with guide wavelength
        # (response too low in frequency -> resonators too long -> shorten them)
        ratio = lam_g(10e9)/lam_g(f_c*1e9)
        L_half = [x*ratio for x in L_half]
        # bandwidth / matching correction of the outer posts:
        # if the RL>=20 dB band is narrower than needed, open the outer coupling (smaller d1)
        if bw20 < 0.52:
            d_half[0] *= 0.96
        elif bw20 > 0.70:
            d_half[0] *= 1.03
    best = history[-1]
    write_s2p(os.path.join(RES, "touchstone", f"improved_{tag}.s2p"), f, s11, s21,
              f"Improved SIW post filter {tag}: order {n}, ripple {ripple} dB")
    np.savez(os.path.join(ROOT, f"improved_{tag}.npz"), freq=f, s11=s11, s21=s21, d=d_half, L=L_half, n=n)
    if tag == FINAL_TAG:
        np.savez(os.path.join(ROOT, "improved_final.npz"), freq=f, s11=s11, s21=s21, d=d_half, L=L_half, n=n)
    print(f"[{tag}] FINAL", best, flush=True)
    return dict(n=n, ripple=ripple, f1=f1, f2=f2, synthesis=syn, history=history, final=best, last_sim=name)


if __name__ == "__main__":
    main()
