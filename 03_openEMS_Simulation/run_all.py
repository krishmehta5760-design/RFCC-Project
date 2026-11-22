"""Runs the whole project in order. Finished simulations are cached in sim_data/ and are not re-run.
Delete a sub-folder of sim_data/ to force that simulation to run again.
Total run time from scratch: about 1.5 h on a 4-core laptop."""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
steps = [
    os.path.join(HERE, "..", "02_Design_Calculations", "siw_design_calc.py"),  # A analytical design
    os.path.join(HERE, "run_line_test.py"),            # B plain SIW line
    os.path.join(HERE, "run_paper_validation.py"),     # C-E paper filters + validation table
    os.path.join(HERE, "run_improvement.py"),          # F K-extraction + improved designs
    os.path.join(HERE, "run_fullboard.py"),            # G transition + complete boards
    os.path.join(HERE, "run_mesh_convergence.py"),     # mesh convergence check
    os.path.join(HERE, "make_comparison_plots.py"),
    os.path.join(HERE, "make_geometry_plots.py"),
    os.path.join(HERE, "..", "05_Report", "make_report.py"),  # Word report
    os.path.join(HERE, "..", "05_Report", "make_presentation_guide_docx.py"),  # presentation guide (Word)
]
for s in steps:
    print("\n########", os.path.basename(s), flush=True)
    subprocess.run([PY, s], cwd=os.path.dirname(s), check=True)
