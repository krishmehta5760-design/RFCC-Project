"""
Analytical design of the X-band SIW band-pass filters (base paper Eqs. 1-12).

Base paper: H. Bandar, N. Turker Tokan, "Comparison of post and iris substrate
integrated waveguide band-pass filters for X-Band applications",
Sigma J. Eng. Nat. Sci. 40(1), 45-56, 2022.

Run:  python siw_design_calc.py      (writes design_calculations.txt)
"""
import os
import numpy as np

C0 = 299792458.0
out_lines = []
def P(s=""):
    print(s); out_lines.append(s)

# ---------------- specifications from the paper ----------------
er, tand, h = 2.33, 0.0012, 1.57          # RT/Duroid 5870, h in mm
f0, BW = 10.0e9, 0.5e9
f1, f2 = f0 - BW/2, f0 + BW/2
a_RW = 22.86                              # WR-90 width (mm)
d_via, p_via, a_s = 1.3205, 1.9807, 15.9028   # SIW via diameter, pitch, row spacing (mm)

P("="*72)
P(" SIW BAND-PASS FILTER - ANALYTICAL DESIGN (base paper Eqs. 1-12)")
P("="*72)
P(f" Substrate RT/Duroid 5870: er = {er}, tan d = {tand}, h = {h} mm")
P(f" f0 = {f0/1e9:.3f} GHz, BW = {BW/1e6:.0f} MHz -> f1 = {f1/1e9:.3f} GHz, f2 = {f2/1e9:.3f} GHz")

# ---------------- SIW geometry ----------------
a_eq_dielectric = a_RW/np.sqrt(er)                      # dielectric-filled RW of same cutoff
a_eff_desl = a_s - d_via**2/(0.95*p_via)                # Deslandes & Wu (2002)
fc = C0/(2*a_eff_desl*1e-3*np.sqrt(er))
fc_WR90 = C0/(2*a_RW*1e-3)
P("\n--- 1. SIW dimensions ---")
P(f" WR-90 width a = {a_RW} mm -> dielectric-filled width a/sqrt(er) = {a_eq_dielectric:.4f} mm")
P(f" SIW via-row spacing a_s = {a_s} mm, via d = {d_via} mm, pitch p = {p_via} mm")
P(f" a_eff = a_s - d^2/(0.95 p) = {a_eff_desl:.4f} mm  (matches a/sqrt(er) within "
  f"{abs(a_eff_desl-a_eq_dielectric)/a_eq_dielectric*100:.2f} %)")
P(f" TE10 cut-off: SIW fc = {fc/1e9:.3f} GHz   (WR-90 air: {fc_WR90/1e9:.3f} GHz)")
P(f" TE20 cut-off: {2*fc/1e9:.3f} GHz -> single-mode band {fc/1e9:.2f}-{2*fc/1e9:.2f} GHz covers 8-12 GHz")

def lam_g(f, a_mm=a_eff_desl):
    lam = C0/f/np.sqrt(er)*1e3
    return lam/np.sqrt(1-(lam/(2*a_mm))**2)

lg1, lg2, lg0f = lam_g(f1), lam_g(f2), lam_g(f0)
lg0 = 0.5*(lg1+lg2)
P(f" Guide wavelength lg(f1) = {lg1:.3f} mm, lg(f2) = {lg2:.3f} mm, lg(f0) = {lg0f:.3f} mm")
P(f" Paper's definition lg0 = (lg1+lg2)/2 = {lg0:.3f} mm")
P("\n Via design rules (Deslandes/Wu, paper ref. [25,32]):")
P(f"   d < lg/5      : {d_via} < {lg2/5:.3f} mm  -> {'OK' if d_via < lg2/5 else 'VIOLATED'}")
P(f"   p <= 2d       : {p_via} <= {2*d_via:.3f} mm -> {'OK' if p_via <= 2*d_via else 'VIOLATED'}")
P(f"   d/a_s         : {d_via/a_s:.3f} (< 0.4 recommended)")
P(f"   p/lambda_c    : {p_via/(2*a_eff_desl):.3f} (< 0.25 for negligible leakage)")

# ---------------- low-pass prototype g-values ----------------
def g_cheby(n, ripple_dB):
    beta = np.log(1/np.tanh(ripple_dB/17.37))
    gam = np.sinh(beta/(2*n))
    a = [np.sin((2*k-1)*np.pi/(2*n)) for k in range(1, n+1)]
    b = [gam**2 + np.sin(k*np.pi/n)**2 for k in range(1, n+1)]
    g = [1.0, 2*a[0]/gam]
    for k in range(2, n+1):
        g.append(4*a[k-2]*a[k-1]/(b[k-2]*g[-1]))
    g.append(1.0 if n % 2 else 1/np.tanh(beta/4)**2)
    return np.array(g)

def g_butter(n):
    return np.array([1.0]+[2*np.sin((2*k-1)*np.pi/(2*n)) for k in range(1, n+1)]+[1.0])

# ---------------- inverters (Eqs. 2-7) ----------------
w = (f2-f1)/f0
wl = (lg1-lg2)/lg0
P("\n--- 2. Fractional bandwidths (Eqs. 2-3) ---")
P(f" w = {w:.4f},  w_lambda = (lg1-lg2)/lg0 = {wl:.4f},  w*(lg0/l0)^2 = "
  f"{w*(lg0/(C0/f0/np.sqrt(er)*1e3))**2:.4f}")

def inverters(g, wl, w1=1.0):
    n = len(g)-2
    K = [np.sqrt(np.pi*wl/(2*g[0]*g[1]*w1))]
    for j in range(1, n):
        K.append(np.pi*wl/(2*w1)/np.sqrt(g[j]*g[j+1]))
    K.append(np.sqrt(np.pi*wl/(2*g[n]*g[n+1]*w1)))
    K = np.array(K)
    X = K/(1-K**2)                       # Eq. 7 (normalised shunt reactance)
    phi = -np.arctan(2*X)                # ideal thin shunt inductance (Xa = 0)
    theta = np.pi + 0.5*(phi[:-1]+phi[1:])   # Eqs. 8/11
    L = lg0*theta/(2*np.pi)              # Eqs. 10/12
    return K, X, theta, L

cases = {
    "3rd-order Butterworth":       g_butter(3),
    "3rd-order Chebyshev 0.1 dB":  g_cheby(3, 0.1),
    "5th-order Chebyshev 0.1 dB":  g_cheby(5, 0.1),
}
results = {}
for name, g in cases.items():
    K, X, th, L = inverters(g, wl)
    results[name] = (g, K, X, th, L)
    P(f"\n--- 3. {name} ---")
    P(" g = [" + ", ".join(f"{x:.4f}" for x in g) + "]")
    for j in range(len(K)):
        P(f"   K{j},{j+1}/Z0 = {K[j]:.4f}   X{j},{j+1}/Z0 = {X[j]:.4f}")
    for j in range(len(L)):
        P(f"   theta{j+1} = {np.degrees(th[j]):7.2f} deg   L{j+1} = {L[j]:.3f} mm (thin-iris model)")

P("\n--- 4. Comparison with the paper's final SIW dimensions (Tables 1-2) ---")
paper = {
  "Post, Butterworth":    dict(d=[0.6839, 2.6092], L=[11.8278, 13.4635]),
  "Post, Chebyshev":      dict(d=[0.7056, 2.2498], L=[11.5898, 12.9377]),
  "Iris, Butterworth":    dict(d=[6.5529, 3.6342], L=[11.1705, 12.2438]),
  "Iris, Chebyshev":      dict(d=[6.5046, 4.0802], L=[11.0723, 12.0042]),
  "Post, 5th Chebyshev":  dict(d=[0.7821, 2.4461, 2.8122], L=[11.8161, 13.4868, 13.7464]),
  "Iris, 5th Chebyshev":  dict(d=[6.3682, 3.8539, 3.4179], L=[11.2304, 12.2704, 12.3769]),
}
for k, v in paper.items():
    P(f" {k:22s} d = {v['d']} mm,  L = {v['L']} mm")
L3c = results["3rd-order Chebyshev 0.1 dB"][4]
P(f"\n Thin-iris theory L1,L2 (3rd Cheb.) = {L3c[0]:.3f}, {L3c[1]:.3f} mm; paper iris = 11.072, 12.004 mm"
  f" (diff {abs(L3c[0]-11.0723):.2f}, {abs(L3c[1]-12.0042):.2f} mm)")
P(" Post lengths are longer because a post also has a series reactance Xa (Fig. 3 of the paper),")
P(" which the thin-iris formula ignores. This is the reason for the full-wave extraction in the")
P(" improvement step.")

# dielectric loss / unloaded Q estimates
Qd = 1/tand
sigma = 5.8e7; mu0 = 4e-7*np.pi
Rs = np.sqrt(np.pi*f0*mu0/sigma)
eta = 376.73/np.sqrt(er)
a, b = a_eff_desl*1e-3, h*1e-3
k = 2*np.pi*f0*np.sqrt(er)/C0; beta = np.sqrt(k**2-(np.pi/a)**2)
# TE101 cavity conductor Q (Pozar 6.46) with cavity length lg/2
dlen = np.pi/beta
Qc = ((k*a*dlen)**3*b*eta)/(2*np.pi**2*Rs) / (2*a**3*b+2*b*dlen**3+a**3*dlen+a*dlen**3)
Qu = 1/(1/Qc+1/Qd)
P("\n--- 5. Loss estimate ---")
P(f" Rs(10 GHz) = {Rs*1e3:.2f} mOhm, cavity Qc = {Qc:.0f}, Qd = 1/tan d = {Qd:.0f}, Qu = {Qu:.0f}")
gC = results["3rd-order Chebyshev 0.1 dB"][0]
IL0 = 4.343*sum(gC[1:-1])/(w*Qu)
P(f" Predicted mid-band IL of the 3rd-order 0.1 dB Chebyshev (Cohn): {IL0:.2f} dB")
gC5 = results["5th-order Chebyshev 0.1 dB"][0]
P(f" Predicted mid-band IL of the 5th-order 0.1 dB Chebyshev (Cohn): {4.343*sum(gC5[1:-1])/(w*Qu):.2f} dB")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "design_calculations.txt"), "w") as fh:
    fh.write("\n".join(out_lines))
