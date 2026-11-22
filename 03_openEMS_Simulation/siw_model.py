"""
openEMS model library for the X-band SIW band-pass filters.

Coordinate system (drawing unit = 1 mm):
    x : propagation direction, filter centred at x = 0
    y : transverse (SIW width), via rows at y = +/- a_s/2
    z : substrate thickness, bottom copper at z = 0, top copper at z = h

Supported structures (cfg['kind']):
    'line'      plain SIW line (no resonators)
    'post'      centred inductive-post filter      cfg['d'] = post diameters, cfg['L'] = post spacings
    'iris'      inductive-iris filter, thin copper walls   cfg['d'] = window widths, cfg['L'] = spacings
    'iris_via'  inductive-iris filter, walls made of small vias (0.2 mm, 0.6 mm pitch)

Feeding (cfg['feed']):
    'wg'   TE10 rectangular-waveguide ports on short solid-wall feed sections (paper CST set-up)
    'msl'  50-ohm microstrip + linear taper transition (complete board, 96.4 mm x 20 mm)
"""
import os, sys, time, json
import numpy as np

OPENEMS_DIR = r"C:\Users\KRISH MEHTA\openEMS_install\openEMS"
if os.path.isdir(OPENEMS_DIR):
    os.add_dll_directory(OPENEMS_DIR)
    os.environ["PATH"] = OPENEMS_DIR + ";" + os.environ["PATH"]

from CSXCAD import ContinuousStructure
from openEMS import openEMS
from openEMS.physical_constants import C0, EPS0, Z0

# ---------------------------------------------------------------- base-paper data
SUB = dict(er=2.33, tand=0.0012, h=1.57, t_cu=35e-6, sigma=5.8e7)
SIW = dict(d=1.3205, p=1.9807, a_s=15.9028, L=59.421, W=20.0)
SIW["a_eff"] = SIW["a_s"] - SIW["d"]**2/(0.95*SIW["p"])
F0 = 10e9
F_START, F_STOP = 8e9, 12e9

def sym(v):
    """[v1, v2, ... vk] -> symmetric list v1..vk..v1 (for n posts: given half list)."""
    return list(v) + list(v[::-1][1:]) if len(v) else []

def expand_dims(d_half, L_half, n_order):
    """paper gives d1..dm and L1..Lm (symmetric). Return full lists of n+1 discontinuities
    and n spacings."""
    n_disc = n_order + 1
    d_full = list(d_half) + list(d_half[::-1]) if n_disc % 2 == 0 else list(d_half) + list(d_half[-2::-1])
    L_full = list(L_half) + list(L_half[-2::-1]) if n_order % 2 == 1 else list(L_half) + list(L_half[::-1])
    assert len(d_full) == n_disc and len(L_full) == n_order, (d_full, L_full)
    return d_full, L_full


def tand_copper_equiv(f):
    """Equivalent loss tangent that gives the same TE10 attenuation as copper walls
    (Pozar eq. 3.96): tan_d_c = 2*beta*alpha_c/k^2."""
    er, b = SUB["er"], SUB["h"]*1e-3
    a = SIW["a_eff"]*1e-3
    mu0 = 4e-7*np.pi
    Rs = np.sqrt(np.pi*f*mu0/SUB["sigma"])
    k = 2*np.pi*f*np.sqrt(er)/C0
    beta = np.sqrt(k**2 - (np.pi/a)**2)
    eta = Z0/np.sqrt(er)
    alpha_c = Rs/(a**3*b*beta*k*eta)*(2*b*np.pi**2 + a**3*k**2)
    return 2*beta*alpha_c/k**2


class SoftLine(float):
    """a mesh line that only refines the mesh (may be dropped); plain floats are 'hard'
    lines that lie on metal edges / sheets / port planes and are never moved."""


def merge_lines(lines, min_gap):
    """Return sorted mesh lines without cells smaller than min_gap (tiny FDTD cells force a
    tiny time step). Hard lines (metal edges, thin sheets, ports) are kept exactly; soft
    refinement lines closer than min_gap to a kept line are dropped."""
    # NOTE: no rounding - zero-thickness sheets and port planes must lie EXACTLY on a line
    hard = np.unique([float(x) for x in lines if not isinstance(x, SoftLine)])
    soft = np.sort([float(x) for x in lines if isinstance(x, SoftLine)])
    # merge hard lines that are practically identical (< 5 um)
    hk = [hard[0]]
    for x in hard[1:]:
        if x - hk[-1] > 0.005: hk.append(x)
    hk = np.array(hk)
    out = list(hk)
    for x in soft:
        if np.min(np.abs(np.array(out) - x)) >= min_gap:
            out.append(x)
    return np.sort(out)


def _fine(lines, c, half, res):
    """add uniformly spaced refinement (soft) lines, spacing ~res, over [c-half, c+half]."""
    n = max(2, int(np.ceil(2*half/res))+1)
    lines.extend(SoftLine(v) for v in np.linspace(c-half, c+half, n))


def build_and_run(cfg, sim_root, run=True, threads=4, verbose=0):
    """Build the CSX model for cfg, run openEMS and return dict with freq, S11, S21."""
    name = cfg["name"]
    sim_path = os.path.join(sim_root, name)
    os.makedirs(sim_path, exist_ok=True)

    h, er = SUB["h"], SUB["er"]
    a_s, dv, pv, Ls, W = SIW["a_s"], SIW["d"], SIW["p"], cfg.get("L_siw", SIW["L"]), SIW["W"]
    a_eff = SIW["a_eff"]
    feed = cfg.get("feed", "wg")
    kind = cfg["kind"]
    res_max = cfg.get("res_max", 0.30)       # coarse cell (mm)  ~ lambda_d/55 at 12 GHz
    res_post = cfg.get("res_post", 0.06)     # fine cell at posts / iris edges
    res_via = cfg.get("res_via", 0.2)       # cell around via rows

    # ---------------- discontinuity positions ----------------
    disc_x = []
    if kind != "line":
        d_full, L_full = cfg["d_full"], cfg["L_full"]
        total = sum(L_full)
        disc_x = list(-total/2 + np.concatenate([[0], np.cumsum(L_full)]))

    # ---------------- x extent ----------------
    if feed == "wg":
        Lf = 9.0
        x_min, x_max = -Ls/2 - Lf, Ls/2 + Lf
    else:
        Lmsl, Ltap = cfg.get("L_msl", 5.0), cfg.get("L_taper", 13.49)
        Lboard = Ls + 2*(Lmsl+Ltap)
        x_min, x_max = -Lboard/2, Lboard/2
    margin_y = 3.0

    # "pec_plates": the top/bottom copper are the z-boundaries of the domain (fast model,
    # copper loss of the broad walls folded into an equivalent loss tangent).
    pec_plates = (feed == "wg") and cfg.get("pec_plates", True)
    if feed == "wg" and not pec_plates:
        margin_y = 3.0
    elif feed == "wg":
        margin_y = 0.0

    FDTD = openEMS(NrTS=cfg.get("NrTS", 400000), EndCriteria=cfg.get("EndCriteria", 1e-4))
    FDTD.SetGaussExcite(0.5*(F_START+F_STOP), 0.5*(F_STOP-F_START)*1.1)
    if pec_plates:
        FDTD.SetBoundaryCond(["PML_8", "PML_8", "MUR", "MUR", "PEC", "PEC"])
    elif feed == "msl":
        # bottom ground plane = PEC boundary at z = 0, open (MUR) air above the board
        FDTD.SetBoundaryCond(["PML_8", "PML_8", "MUR", "MUR", "PEC", "MUR"])
    else:
        FDTD.SetBoundaryCond(["PML_8", "PML_8", "MUR", "MUR", "MUR", "MUR"])

    CSX = ContinuousStructure()
    FDTD.SetCSX(CSX)
    mesh = CSX.GetGrid()
    mesh.SetDeltaUnit(1e-3)

    tand = SUB["tand"]
    if pec_plates and not cfg.get("lossless", False):
        tand = tand + tand_copper_equiv(F0)
    elif feed == "msl" and not cfg.get("lossless", False):
        tand = tand + 0.5*tand_copper_equiv(F0)      # loss of the (PEC-boundary) ground plane
    if cfg.get("lossless", False):
        tand = 0.0
    kappa = 2*np.pi*F0*EPS0*er*tand
    sub = CSX.AddMaterial("RT5870", epsilon=er, kappa=kappa)
    if cfg.get("lossless", False):
        cu = CSX.AddMetal("PEC_plate")
    else:
        cu = CSX.AddConductingSheet("copper", conductivity=SUB["sigma"], thickness=SUB["t_cu"])
    pec = CSX.AddMetal("PEC")

    xl, yl, zl = [], [], []

    # substrate + plates
    y_sub = W/2 + (5 if feed == "wg" else 0)
    sub.AddBox([x_min - 1, -y_sub, 0], [x_max + 1, y_sub, h], priority=1)
    if pec_plates:
        pass
    elif feed == "wg":
        cu.AddBox([x_min - 1, -W/2, 0], [x_max + 1, W/2, 0], priority=10)
        cu.AddBox([x_min - 1, -W/2, h], [x_max + 1, W/2, h], priority=10)
    else:
        # bottom ground = PEC boundary, top: SIW section + taper + microstrip
        cu.AddBox([-Ls/2, -W/2, h], [Ls/2, W/2, h], priority=10)
        w50, wt = cfg.get("w_msl", 4.66), cfg.get("w_taper", 6.5)
        for s in (-1, 1):
            xa, xb = s*Ls/2, s*(Ls/2 + Ltap)
            pts_x = [xa, xb, xb, xa]
            pts_y = [-wt/2, -w50/2, w50/2, wt/2]
            cu.AddLinPoly(points=[pts_x, pts_y], norm_dir="z", elevation=h, length=0, priority=10)
            xc, xd = s*(Ls/2 + Ltap), s*(Ls/2 + Ltap + Lmsl + 1)
            cu.AddBox([min(xc, xd), -w50/2, h], [max(xc, xd), w50/2, h], priority=10)
            yl += [-wt/2, wt/2, -w50/2, w50/2]
            _fine(yl, w50/2, 0.3, 0.15); _fine(yl, -w50/2, 0.3, 0.15)
            xl += [xa, xb]
        cfg["_msl"] = dict(w50=w50, wt=wt, Lmsl=Lmsl, Ltap=Ltap)

    # ---------------- SIW side walls (via rows) ----------------
    nv = int(np.floor(Ls/pv)) + 1
    via_x = (np.arange(nv) - (nv-1)/2)*pv
    via_x = via_x[np.abs(via_x) <= Ls/2 - dv/2 + 1e-9]
    for yr in (-a_s/2, a_s/2):
        for xv in via_x:
            pec.AddCylinder([xv, yr, 0], [xv, yr, h], dv/2, priority=20)
        _fine(yl, yr, dv/2 + 0.3, res_via)
    for xv in via_x:
        xl += [SoftLine(xv - dv/2), SoftLine(xv + dv/2)]

    # waveguide-port feed sections (solid walls at a_eff)
    if feed == "wg":
        for s in (-1, 1):
            xa, xb = s*(Ls/2 - pv/2), s*(Ls/2 + Lf + 1)
            for yw in (-a_eff/2, a_eff/2):
                pec.AddBox([min(xa, xb), yw, 0], [max(xa, xb), yw, h], priority=20)
        yl += [-a_eff/2, a_eff/2]

    # ---------------- resonator discontinuities ----------------
    geo = dict(vias=[(float(x), float(y)) for y in (-a_s/2, a_s/2) for x in via_x],
               via_d=dv, posts=[], irises=[], Ls=Ls, a_s=a_s, W=W, x_min=x_min, x_max=x_max)
    if kind == "post":
        for xp, dp in zip(disc_x, d_full):
            pec.AddCylinder([xp, 0, 0], [xp, 0, h], dp/2, priority=30)
            xl += [xp - dp/2, xp + dp/2]
            _fine(xl, xp, dp/2 + 0.25, res_post)
            geo["posts"].append((float(xp), float(dp)))
        maxdp = max(d_full)
        yl += [-maxdp/2, maxdp/2]
        _fine(yl, 0, maxdp/2 + 0.25, res_post)
        for dp in set(np.round(d_full, 6)):
            yl += [-dp/2, dp/2]
    elif kind in ("iris", "iris_via"):
        for xi, wi in zip(disc_x, d_full):
            geo["irises"].append((float(xi), float(wi)))
            if kind == "iris":
                for s in (-1, 1):
                    y0, y1 = s*wi/2, s*a_s/2
                    pec.AddBox([xi, min(y0, y1), 0], [xi, max(y0, y1), h], priority=30)
                xl.append(xi)
                _fine(xl, xi, 0.4, res_post*1.5)
            else:
                pitch, dsv = cfg.get("iris_via_pitch", 0.6), cfg.get("iris_via_d", 0.2)
                for s in (-1, 1):
                    ys = np.arange(wi/2 + dsv/2, a_s/2 - dv/2 + 1e-6, pitch)
                    for yv in ys:
                        pec.AddCylinder([xi, s*yv, 0], [xi, s*yv, h], dsv/2, priority=30)
                        yl.append(s*yv)
                xl += [xi - dsv/2, xi, xi + dsv/2]
                _fine(xl, xi, 0.4, 0.05)
            yl += [-wi/2, wi/2]
            _fine(yl, wi/2, 0.3, res_post*1.5); _fine(yl, -wi/2, 0.3, res_post*1.5)

    # ---------------- ports ----------------
    ports = []
    if feed == "wg":
        xp1a, xp1b = x_min + 4.0, x_min + 5.0
        xp2a, xp2b = x_max - 4.0, x_max - 5.0
        p1 = FDTD.AddRectWaveGuidePort(1, [xp1a, -a_eff/2, 0], [xp1b, a_eff/2, h], "x",
                                       a_eff*1e-3, h*1e-3, "TE10", 1)
        p2 = FDTD.AddRectWaveGuidePort(2, [xp2a, -a_eff/2, 0], [xp2b, a_eff/2, h], "x",
                                       a_eff*1e-3, h*1e-3, "TE10", 0)
        for p in (p1, p2):
            p.ref_index = np.sqrt(er)
        ports = [p1, p2]
        xl += [xp1a, xp1b, xp2a, xp2b]
    else:
        # (microstrip ports are created after the mesh exists - see below)
        w50 = cfg["_msl"]["w50"]
        xs, xe = x_min, x_min + Lmsl
        xl += [xs, xe, x_max, x_max - Lmsl]
        _fine(xl, xs + Lmsl/2, Lmsl/2, 0.25); _fine(xl, x_max - Lmsl/2, Lmsl/2, 0.25)

    # ---------------- mesh ----------------
    xl += [x_min, x_max, -Ls/2, Ls/2]
    yl += [-W/2 - margin_y, W/2 + margin_y, -W/2, W/2, 0]
    nz = cfg.get("nz", 4)
    zl += list(np.linspace(0, h, nz+1))
    if feed == "msl":
        zl += [h + 6.0]
    elif not pec_plates:
        zl += [-2.0, h + 2.0]
    min_gap = cfg.get("min_gap", 0.05)
    mesh.AddLine("x", merge_lines(xl, min_gap))
    mesh.AddLine("y", merge_lines(yl, min_gap))
    mesh.AddLine("z", merge_lines(zl, min_gap))
    mesh.SmoothMeshLines("x", res_max, ratio=1.4)
    mesh.SmoothMeshLines("y", cfg.get("res_max_y", 0.4), ratio=1.4)
    mesh.SmoothMeshLines("z", 0.5, ratio=1.4)
    if feed == "msl":
        p1 = FDTD.AddMSLPort(1, cu, [xs, -w50/2, h], [xe, w50/2, 0], "x", "z",
                             excite=-1, FeedShift=1.0, MeasPlaneShift=Lmsl - 0.5, priority=30)
        p2 = FDTD.AddMSLPort(2, cu, [x_max, -w50/2, h], [x_max - Lmsl, w50/2, 0], "x", "z",
                             MeasPlaneShift=Lmsl - 0.5, priority=30)
        ports = [p1, p2]
    ncell = [len(mesh.GetLines(d)) for d in "xyz"]
    dmin = [float(np.min(np.diff(mesh.GetLines(d)))) for d in "xyz"]
    print(f"[{name}] mesh {ncell} = {np.prod(ncell)/1e6:.2f} Mcells, min cell {np.round(dmin,3)} mm", flush=True)

    freq = np.linspace(F_START, F_STOP, 801)
    info = dict(name=name, ncells=ncell, total_cells=int(np.prod(ncell)))
    if cfg.get("view_only"):          # only write the 3-D model for AppCSXCAD, do not solve
        xml = os.path.join(sim_path, "geometry.xml")
        CSX.Write2XML(xml)
        return dict(xml=xml, info=info)
    if run:
        if cfg.get("debug_geom"):
            CSX.Write2XML(os.path.join(sim_path, "geometry.xml"))
        t0 = time.time()
        FDTD.Run(sim_path, cleanup=True, verbose=verbose, numThreads=threads)
        info["runtime_s"] = round(time.time() - t0, 1)

    # ---------------- post-processing ----------------
    if feed == "wg":
        k0 = 2*np.pi*freq/C0
        kc = np.pi/(a_eff*1e-3)
        beta = np.sqrt(k0**2*er - kc**2 + 0j)
        Zte = np.real(k0*Z0/beta)
        for p in ports:
            p.CalcPort(sim_path, freq, ref_impedance=Zte)
    else:
        for p in ports:
            p.CalcPort(sim_path, freq, ref_impedance=50)
    s11 = ports[0].uf_ref/ports[0].uf_inc
    s21 = ports[1].uf_ref/ports[0].uf_inc
    out = dict(freq=freq, s11=s11, s21=s21, info=info, geo=geo, cfg={k: v for k, v in cfg.items() if not k.startswith("_")})
    np.savez(os.path.join(sim_path, "sparams.npz"), freq=freq, s11=s11, s21=s21)
    with open(os.path.join(sim_path, "info.json"), "w") as fh:
        json.dump(dict(info=info, cfg=out["cfg"], geo=geo), fh, indent=1, default=float)
    return out


def write_s2p(fn, freq, s11, s21, comment=""):
    with open(fn, "w") as fh:
        fh.write(f"! {comment}\n! openEMS v0.37 FDTD, reciprocal & symmetric: S22=S11, S12=S21\n")
        fh.write("# GHz S MA R 50\n")
        for f, a, b in zip(freq, s11, s21):
            fh.write(f"{f/1e9:.5f} {abs(a):.6e} {np.degrees(np.angle(a)):.4f} {abs(b):.6e} {np.degrees(np.angle(b)):.4f} "
                     f"{abs(b):.6e} {np.degrees(np.angle(b)):.4f} {abs(a):.6e} {np.degrees(np.angle(a)):.4f}\n")


def metrics(freq, s11, s21, f1=9.75e9, f0=10e9, f2=10.25e9):
    """IL/RL at band edges & centre, 3 dB band, RL>=20 dB band, centre frequency, rejection."""
    S11 = 20*np.log10(np.abs(s11) + 1e-15); S21 = 20*np.log10(np.abs(s21) + 1e-15)
    at = lambda arr, f: float(np.interp(f, freq, arr))
    m = {"IL_f1": -at(S21, f1), "IL_f0": -at(S21, f0), "IL_f2": -at(S21, f2),
         "RL_f1": -at(S11, f1), "RL_f0": -at(S11, f0), "RL_f2": -at(S11, f2)}
    imax = np.argmax(S21)
    m["IL_min"] = -float(S21[imax]); m["f_ILmin_GHz"] = float(freq[imax]/1e9)
    above = np.where(S21 >= S21[imax] - 3)[0]
    # contiguous region around the maximum
    lo = hi = imax
    while lo > 0 and S21[lo-1] >= S21[imax]-3: lo -= 1
    while hi < len(freq)-1 and S21[hi+1] >= S21[imax]-3: hi += 1
    m["f3dB_lo_GHz"], m["f3dB_hi_GHz"] = float(freq[lo]/1e9), float(freq[hi]/1e9)
    m["BW3dB_MHz"] = float((freq[hi]-freq[lo])/1e6)
    m["f0_3dB_GHz"] = float(0.5*(freq[hi]+freq[lo])/1e9)
    # RL >= 20 dB band (contiguous around f0 region)
    good = S11 <= -20
    idx = np.where(good & (freq > freq[lo]) & (freq < freq[hi]))[0]
    if len(idx):
        m["RL20_lo_GHz"], m["RL20_hi_GHz"] = float(freq[idx[0]]/1e9), float(freq[idx[-1]]/1e9)
    else:
        m["RL20_lo_GHz"] = m["RL20_hi_GHz"] = float("nan")
    band = (freq >= f1) & (freq <= f2)
    m["RL_min_band"] = float(-S11[band].max()); m["IL_max_band"] = float(-S21[band].min())
    m["rej_9GHz"] = -at(S21, 9.0e9); m["rej_11GHz"] = -at(S21, 11.0e9)
    return m
