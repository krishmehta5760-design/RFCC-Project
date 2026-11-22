"""Step B: plain SIW line (no resonators) - checks the TE10 cut-off, port set-up and loss."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from siw_model import build_and_run, SIW

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sim_data")
cfg = dict(name="siw_line", kind="line", feed="wg")
r = build_and_run(cfg, ROOT, verbose=1)
f, s11, s21 = r["freq"], r["s11"], r["s21"]
print(r["info"])
for fx in (8e9, 9e9, 10e9, 11e9, 12e9):
    i = np.argmin(abs(f - fx))
    print(f"{fx/1e9:5.1f} GHz  S11 = {20*np.log10(abs(s11[i])):7.2f} dB   S21 = {20*np.log10(abs(s21[i])):7.3f} dB")
