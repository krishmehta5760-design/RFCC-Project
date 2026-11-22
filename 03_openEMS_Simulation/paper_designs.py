"""Dimensions of every filter in the base paper (Tables 1 and 2), in mm."""
from siw_model import expand_dims

PAPER = {
    # 3rd order (Table 1)
    "post3_butter": dict(kind="post", n=3, d=[0.6839, 2.6092], L=[11.8278, 13.4635]),
    "post3_cheby":  dict(kind="post", n=3, d=[0.7056, 2.2498], L=[11.5898, 12.9377]),
    "iris3_butter": dict(kind="iris", n=3, d=[6.5529, 3.6342], L=[11.1705, 12.2438]),
    "iris3_cheby":  dict(kind="iris", n=3, d=[6.5046, 4.0802], L=[11.0723, 12.0042]),
    # 5th order Chebyshev (Table 2)
    "post5_cheby":  dict(kind="post", n=5, d=[0.7821, 2.4461, 2.8122], L=[11.8161, 13.4868, 13.7464]),
    "iris5_cheby":  dict(kind="iris", n=5, d=[6.3682, 3.8539, 3.4179], L=[11.2304, 12.2704, 12.3769]),
    # Fig. 11: 3rd-order Chebyshev iris built from small vias (0.2 mm, 0.6 mm spacing)
    "iris3_cheby_vias": dict(kind="iris_via", n=3, d=[6.5046, 4.0802], L=[11.0723, 12.0042]),
}

# Paper simulated results, Tables 3 and 4: (IL, RL) at (lower edge, centre, upper edge)
PAPER_RESULTS = {
    "post3_butter": dict(IL=[3.5, 0.68, 6.15], RL=[5.16, 45.0, 2.0]),
    "post3_cheby":  dict(IL=[1.23, 0.78, 1.33], RL=[14.0, 23.0, 10.7]),
    "iris3_butter": dict(IL=[6.88, 0.52, 5.4], RL=[4.5, 20.0, 2.8]),
    "iris3_cheby":  dict(IL=[2.33, 0.89, 1.43], RL=[8.79, 21.23, 10.11]),
    "post5_cheby":  dict(IL=[5.75, 0.2, 5.55], RL=[10.5, 32.0, 7.14]),
    "iris5_cheby":  dict(IL=[6.95, 0.21, 7.67], RL=[8.92, 28.0, 4.8]),
    "iris3_cheby_vias": dict(IL=[None, 0.81, None], RL=[None, 30.0, None]),
}

LABELS = {
    "post3_butter": "3rd-order post, Butterworth",
    "post3_cheby": "3rd-order post, Chebyshev 0.1 dB",
    "iris3_butter": "3rd-order iris, Butterworth",
    "iris3_cheby": "3rd-order iris, Chebyshev 0.1 dB",
    "post5_cheby": "5th-order post, Chebyshev 0.1 dB",
    "iris5_cheby": "5th-order iris, Chebyshev 0.1 dB",
    "iris3_cheby_vias": "3rd-order iris (small vias), Chebyshev",
}


def make_cfg(key, **over):
    p = PAPER[key]
    d_full, L_full = expand_dims(p["d"], p["L"], p["n"])
    total = sum(L_full)
    L_siw = max(59.421, round(total + 2*11.5, 3))     # 5th-order needs a longer SIW
    cfg = dict(name=key, kind=p["kind"], feed="wg", d_full=d_full, L_full=L_full, L_siw=L_siw)
    cfg.update(over)
    return cfg
