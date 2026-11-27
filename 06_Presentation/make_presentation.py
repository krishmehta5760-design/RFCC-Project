"""Builds SIW_Filter_Presentation.pptx (10 slides, ~7 min talk + ~3 min live demo) with speaker notes.
Run:  python make_presentation.py      (needs python-pptx; figures from make_presentation_figures.py)"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
FIG = os.path.join(HERE, "figs")
PLOTS = os.path.join(ROOT, "04_Results", "plots")
OUT = os.path.join(HERE, "SIW_Filter_Presentation.pptx")

NAVY, NAVY2, COPPER = "14213D", "24365C", "B5651D"
INK, MUTED, PANEL, ICE = "1B2430", "5B6573", "F1F3F6", "C9D4E8"
GREEN, RED, WHITE, COPPERLT = "2E8B57", "C0392B", "FFFFFF", "F7ECE2"
HEAD, BODY, MONO = "Cambria", "Calibri", "Consolas"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
rgb = lambda h: RGBColor.from_string(h)


def bg(slide, color):
    f = slide.background.fill
    f.solid(); f.fore_color.rgb = rgb(color)


def box(slide, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, line=None, name=None):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    if fill is None:
        s.fill.background()
    else:
        s.fill.solid(); s.fill.fore_color.rgb = rgb(fill)
    if line:
        s.line.color.rgb = rgb(line); s.line.width = Pt(1.25)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    if name:
        s.name = name
    return s


def text(slide, x, y, w, h, paras, size=16, color=INK, font=BODY, bold=False, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, margin=0.0, spacing=4, name=None):
    """paras: str | list of paragraphs; each paragraph is str or list of (text, {opts}) runs."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, Inches(margin))
    if isinstance(paras, str):
        paras = [paras]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(spacing)
        runs = [(para, {})] if isinstance(para, str) else para
        for t, o in runs:
            r = p.add_run(); r.text = t
            r.font.name = o.get("font", font); r.font.size = Pt(o.get("size", size))
            r.font.bold = o.get("bold", bold); r.font.italic = o.get("italic", False)
            r.font.color.rgb = rgb(o.get("color", color))
    if name:
        tb.name = name
    return tb


def circle_num(slide, x, y, n, d=0.48, fill=COPPER, color=WHITE, size=16):
    c = box(slide, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    for side in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, side, 0)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(n)
    r.font.name = HEAD; r.font.bold = True; r.font.size = Pt(size); r.font.color.rgb = rgb(color)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    return c


def title(slide, t, dark=False):
    text(slide, 0.6, 0.38, 12.1, 0.85, t, size=32, font=HEAD, bold=True, color=WHITE if dark else NAVY,
         anchor=MSO_ANCHOR.MIDDLE, name="Title")


def page(slide, n, dark=False):
    text(slide, 12.2, 7.0, 0.6, 0.3, str(n), size=11, color=ICE if dark else MUTED, align=PP_ALIGN.RIGHT)


def picture(slide, path, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return slide.shapes.add_picture(path, Inches(x), Inches(y), **kw)


def stat(slide, x, y, w, h, big, label, color=NAVY, fill=PANEL, big_size=34, label_size=14):
    box(slide, x, y, w, h, fill)
    text(slide, x + 0.25, y + 0.15, w - 0.5, 0.75, big, size=big_size, font=HEAD, bold=True, color=color,
         anchor=MSO_ANCHOR.MIDDLE)
    text(slide, x + 0.25, y + 0.92, w - 0.5, h - 1.0, label, size=label_size, color=INK)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def siw_drawing(slide, x0, y0, w, h):
    """Stylised drawing of the improved filter: substrate, two via rows, five posts (sizes to scale)."""
    box(slide, x0, y0, w, h, NAVY2, radius=0.12)
    pitch, dv = 0.30, 0.13
    nv = int((w - 0.3) / pitch)
    xs = x0 + (w - (nv - 1) * pitch) / 2
    for row_y in (y0 + 0.14, y0 + h - 0.14 - dv):
        for i in range(nv):
            box(slide, xs + i * pitch - dv / 2, row_y, dv, dv, COPPER, shape=MSO_SHAPE.OVAL)
    mm = w / 62.0                                   # inches per mm along the filter
    L = [11.1515, 12.8709, 12.8709, 11.1515]
    d = [0.5731, 2.1243, 2.5149, 2.1243, 0.5731]
    pos = [-sum(L) / 2]
    for l in L:
        pos.append(pos[-1] + l)
    cx, cy = x0 + w / 2, y0 + h / 2
    for p, dd in zip(pos, d):
        dia = max(dd * mm * 1.6, 0.08)
        box(slide, cx + p * mm - dia / 2, cy - dia / 2, dia, dia, COPPER, shape=MSO_SHAPE.OVAL)


# =============================== 1. Title ===============================
s = prs.slides.add_slide(BLANK); bg(s, NAVY)
text(s, 0.8, 0.85, 8, 0.4, "RFCC COURSE PROJECT", size=14, bold=True, color=COPPER)
text(s, 0.8, 1.3, 11.5, 1.8, "Substrate Integrated Waveguide Band-Pass Filter at X-Band",
     size=40, font=HEAD, bold=True, color=WHITE, name="Title")
text(s, 0.8, 3.05, 11.5, 0.6, "Validating a published design in openEMS – and improving it",
     size=20, color=ICE)
siw_drawing(s, 0.8, 4.0, 11.75, 1.25)
text(s, 0.8, 5.35, 11.75, 0.35, "Our improved 4th-order filter: 5 metal posts inside a waveguide formed by two rows of vias",
     size=12, color=ICE)
text(s, 0.8, 6.0, 11.75, 0.45, "Krish Mehta (241EC224)   ·   Vishva Chavada (241EC212)   ·   NITK Surathkal", size=18, color=WHITE)
text(s, 0.8, 6.5, 11.75, 0.4, "Base paper: H. Bandar & N. Türker Tokan, Sigma J. Eng. Nat. Sci. 40(1), 45–56, 2022",
     size=12, color=ICE)
notes(s, """[Member 1 · 20 s]
Good morning. Our project is a substrate integrated waveguide band-pass filter for X-band, at 10 GHz.
We took a published paper, rebuilt all of its filters in the free 3-D electromagnetic simulator openEMS to validate it, and then improved the design.
The drawing shows our final filter: a waveguide made inside a circuit board by two rows of metal vias, with five metal posts inside it.""")

# =============================== 2. Why SIW + specs ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "Why a substrate integrated waveguide?")
rows = [("Metal waveguide", "Very low loss – but bulky, expensive and hard to connect to chips", PANEL, INK),
        ("Microstrip line", "Cheap and flat – but too lossy for a sharp filter at 10 GHz", PANEL, INK),
        ("SIW (this project)", "A waveguide built inside a PCB with two rows of plated vias: low loss and cheap", COPPERLT, INK)]
for i, (h_, b_, fill, col) in enumerate(rows):
    y = 1.5 + i * 1.45
    box(s, 0.6, y, 6.6, 1.25, fill)
    circle_num(s, 0.85, y + 0.38, i + 1, fill=COPPER if i == 2 else MUTED)
    text(s, 1.55, y + 0.14, 5.45, 0.42, h_, size=18, bold=True, color=NAVY)
    text(s, 1.55, y + 0.55, 5.45, 0.65, b_, size=14, color=col)
text(s, 7.75, 1.45, 5.0, 0.4, "Specification (from the base paper)", size=16, bold=True, color=COPPER)
tiles = [("10 GHz", "centre frequency, X-band (radar, satellite links)"),
         ("500 MHz", "pass band 9.75–10.25 GHz (5 %)"),
         ("εr = 2.33", "RT/Duroid 5870 board, 1.57 mm, low loss"),
         ("7 filters", "post & iris, Chebyshev & Butterworth, 3rd & 5th order")]
for i, (b_, l_) in enumerate(tiles):
    x = 7.75 + (i % 2) * 2.55; y = 1.95 + (i // 2) * 2.3
    stat(s, x, y, 2.35, 2.05, b_, l_, big_size=28, label_size=13)
page(s, 2)
notes(s, """[Member 1 · 50 s]
At 10 GHz there are two classic options. A metal waveguide has very low loss but is bulky and expensive. A microstrip line is cheap and flat but too lossy for a sharp filter.
A substrate integrated waveguide gets the best of both: the top and bottom copper of a normal circuit board are the waveguide walls, and two rows of plated vias form the side walls.
Our specifications come from the base paper: centre 10 GHz, 500 MHz bandwidth from 9.75 to 10.25 GHz, on Rogers RT/Duroid 5870 with permittivity 2.33.
The paper designs seven filters – post and iris types, Chebyshev and Butterworth, 3rd and 5th order – and gives every dimension, so we could rebuild all of them exactly.""")

# =============================== 3. How it works ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "How an SIW post filter works")
picture(s, os.path.join(PLOTS, "geom_post3_cheby.png"), 1.05, 1.25, w=11.2)
cols = [("Via walls = waveguide sides", "Effective width 14.98 mm → cut-off 6.56 GHz, so only one mode travels across the whole X-band"),
        ("Posts = partial reflectors", "Each post reflects part of the wave (an impedance inverter K). Small outer posts couple strongly to the ports, big inner posts weakly"),
        ("Gaps = resonators", "About half a guide wavelength (≈ 12 mm). 3 resonators = 3rd order. Our hand calculation matches the paper's spacings to 0.013 mm")]
for i, (h_, b_) in enumerate(cols):
    x = 0.6 + i * 4.1
    box(s, x, 4.65, 3.85, 2.25, PANEL)
    circle_num(s, x + 0.25, 4.85, i + 1)
    text(s, x + 0.9, 4.85, 2.8, 0.5, h_, size=16, bold=True, color=NAVY, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.25, 5.45, 3.4, 1.4, b_, size=14)
page(s, 3)
notes(s, """[Member 1 · 1 min]
This is the paper's 3rd-order post filter as we modelled it, seen from above.
(1) The two long rows of black dots are the vias – they are the side walls. The effective width is 14.98 mm, which puts the cut-off at 6.56 GHz, so a single mode travels through the whole X-band.
(2) The four dots in the middle are metal posts. Each post reflects part of the wave; in filter theory it acts as an impedance inverter. The small outer posts give strong coupling to the input and output, the big inner posts weak coupling between resonators.
(3) The spaces between posts – about 12 mm, half a guide wavelength – are resonators. Three resonators make a 3rd-order filter.
We first did the design by hand with the paper's equations; our resonator spacings match the paper's to 13 micrometres.""")

# =============================== 4. Method ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "Method: full-wave simulation in openEMS")
steps = [("Python builds the 3-D model", "substrate with losses, copper, vias, posts or irises, waveguide ports"),
         ("openEMS solves Maxwell's equations", "FDTD: one 8–12 GHz pulse, ~200 000 cells, 1–2 min per filter"),
         ("Python reads the result", "S11 and S21 at 801 frequencies → IL, RL, bandwidth, plots")]
for i, (h_, b_) in enumerate(steps):
    x = 0.6 + i * 4.2
    box(s, x, 1.5, 3.7, 2.0, NAVY)
    circle_num(s, x + 0.25, 1.72, i + 1)
    text(s, x + 0.9, 1.68, 2.65, 0.6, h_, size=16, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.25, 2.4, 3.25, 1.0, b_, size=14, color=ICE)
    if i < 2:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 3.78), Inches(2.3), Inches(0.35), Inches(0.4))
        a.fill.solid(); a.fill.fore_color.rgb = rgb(COPPER); a.line.fill.background()
text(s, 0.6, 3.95, 12, 0.45, "Checked before trusting any filter result", size=18, bold=True, color=COPPER)
checks = [("< −40 dB", "reflection of an empty SIW line: ports and via walls are modelled correctly"),
          ("3.0 vs 3.05", "dB/m loss of the empty line: openEMS vs theory"),
          ("0.1 %", "shift in centre frequency on a 2.5× finer mesh: results are converged")]
for i, (b_, l_) in enumerate(checks):
    stat(s, 0.6 + i * 4.2, 4.5, 3.7, 1.95, b_, l_, color=GREEN)
page(s, 4)
notes(s, """[Member 1 · 50 s]
We used openEMS, a free and open-source 3-D field solver – the paper used the commercial tool CST.
openEMS has no graphical design window: a Python script builds the model – substrate with its losses, copper, vias, posts and ports – openEMS solves Maxwell's equations on a grid of about 200 000 cells by sending one short pulse covering 8 to 12 GHz, and Python then turns the signals into S11 (reflected) and S21 (transmitted).
Before trusting any filter we checked the model: an empty SIW reflects less than −40 dB, its loss is 3.0 dB per metre against 3.05 from theory, and a 2.5 times finer mesh moved the frequency by only 0.1 %.
(Hand over to Member 2.)""")

# =============================== 5. Validation ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "Validation: the paper's filters reproduced")
picture(s, os.path.join(FIG, "fig_validation.png"), 0.45, 1.35, w=8.6)
text(s, 0.6, 4.85, 8.3, 0.35, "Lines: openEMS.  Markers: the paper's Table 3 values (CST).  Green band: 9.75–10.25 GHz",
     size=12, color=MUTED)
box(s, 0.6, 5.4, 8.3, 1.45, COPPERLT)
text(s, 0.85, 5.52, 7.9, 1.25,
     [[("Finding: ", {"bold": True, "color": COPPER}),
       ("the paper's 0.2 dB loss for its 5th-order filters is not physically possible with this board – "
        "theory gives 1.05 dB and openEMS 1.13 dB.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE)
stat(s, 9.35, 1.4, 3.4, 1.75, "87 %", "of 38 paper values match within ±0.5 % in frequency", color=GREEN)
stat(s, 9.35, 3.3, 3.4, 1.75, "47 %", "at exactly the same frequency (band edges sit on steep skirts)", color=NAVY)
stat(s, 9.35, 5.2, 3.4, 1.65, "7 / 7", "filters rebuilt – every conclusion of the paper confirmed", color=COPPER)
page(s, 5)
notes(s, """[Member 2 · 1 min]
We rebuilt all seven of the paper's filters with its exact dimensions and no tuning. Here are the two 3rd-order Chebyshev filters: lines are openEMS, markers are the values printed in the paper.
Blue is S21, what gets through – near 0 dB in the green pass band. Copper is S11, what is reflected – three dips for three resonators.
87 % of the paper's 38 numbers match ours if we allow a 0.5 % frequency shift between the two solvers. At exactly the same frequency it is 47 %, because the band-edge values sit on very steep slopes, where 50 MHz changes the value by several dB. All of the paper's conclusions are confirmed.
We also found an error: the paper reports only 0.2 dB loss for its 5th-order filters. With this board material theory gives 1.05 dB, and openEMS 1.13 dB – a 5th-order filter cannot have less loss than a 3rd-order one.""")

# =============================== 6. Problem + fix ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "The paper's design is poorly matched at the band edges")
stat(s, 0.6, 1.45, 3.4, 1.85, "5.8 dB", "worst return loss in band – about 26 % of the power reflected (target ≥ 20 dB)", color=RED)
stat(s, 4.2, 1.45, 3.4, 1.85, "2.26 dB", "worst insertion loss inside the 9.75–10.25 GHz band", color=RED)
box(s, 0.6, 3.5, 7.0, 1.85, PANEL)
text(s, 0.85, 3.62, 6.55, 1.65,
     [[("Cause: ", {"bold": True, "color": NAVY}),
       ("the post sizes were read from an old handbook chart. We measured each post's real coupling K in openEMS: "
        "the paper's posts couple 4–6 % too strongly.", {})]], size=15, anchor=MSO_ANCHOR.MIDDLE)
picture(s, os.path.join(FIG, "fig_K_extraction.png"), 8.0, 1.35, w=4.8)
text(s, 0.6, 5.6, 4, 0.4, "Our fix", size=18, bold=True, color=COPPER)
fix = ["Measure K of a post for 10 diameters in openEMS", "Redesign with 0.03 dB ripple (RL 21.6 dB)",
       "Use 4 resonators instead of 3", "Auto-tune the centre frequency (2 runs)"]
for i, f_ in enumerate(fix):
    x = 0.6 + i * 3.1
    circle_num(s, x, 6.12, i + 1, d=0.44, size=14)
    text(s, x + 0.55, 6.05, 2.4, 0.85, f_, size=14, anchor=MSO_ANCHOR.MIDDLE)
page(s, 6)
notes(s, """[Member 2 · 50 s]
The paper's main post filter has a problem: inside the band, its return loss falls to 5.8 dB in our simulation – about a quarter of the power is reflected at the band edge – and the loss rises to 2.26 dB. Even the paper's own table gives only 10.7 dB there; 20 dB is the usual target.
The cause: the paper read its post sizes from an old handbook chart. We simulated a single post for ten diameters and measured its real coupling – the curve on the right. The red crosses are the paper's posts, the green stars the sizes actually needed: the couplings are 4 to 6 % too strong.
Our fix in four steps: use this measured curve, redesign with a smaller ripple of 0.03 dB, use four resonators instead of three, and let the script re-tune the centre frequency – it converged in two runs.""")

# =============================== 7. Improved result ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "Improved 4th-order filter meets the spec")
picture(s, os.path.join(FIG, "fig_improved.png"), 0.4, 1.3, w=8.4)
rowsr = [("Worst RL in band", "5.8", "21.7 dB"), ("Worst IL in band", "2.26", "0.82 dB"),
         ("Rejection 9 / 11 GHz", "33 / 24", "46 / 30 dB")]
text(s, 9.1, 1.35, 3.7, 0.4, "Paper design  →  improved", size=14, bold=True, color=MUTED)
for i, (lab, a_, b_) in enumerate(rowsr):
    y = 1.85 + i * 1.3
    box(s, 9.1, y, 3.7, 1.15, PANEL)
    text(s, 9.3, y + 0.08, 3.3, 0.35, lab, size=13, color=MUTED)
    text(s, 9.3, y + 0.42, 3.3, 0.65, [[(a_ + "  →  ", {"color": RED}), (b_, {"color": GREEN, "bold": True})]],
         size=24, font=HEAD, anchor=MSO_ANCHOR.MIDDLE)
picture(s, os.path.join(PLOTS, "geom_improved_post4.png"), 0.75, 5.75, w=4.3)
text(s, 5.25, 5.85, 7.5, 1.0, "Same 59.4 mm SIW and same board – only the post sizes and positions changed "
     "(posts 0.57 / 2.12 / 2.51 / 2.12 / 0.57 mm).", size=14, color=INK, anchor=MSO_ANCHOR.MIDDLE)
page(s, 7)
notes(s, """[Member 2 · 1 min]
This is the result. Grey is the paper's design, colour is ours. The green box is the specification: from 9.75 to 10.25 GHz the copper reflection curve must stay below the dashed −20 dB line.
The paper's grey dotted curve leaves the box and rises to −5.8 dB at the upper edge. Our copper curve has four dips – four resonators – and stays below −20 dB across the whole band.
In numbers: worst return loss from 5.8 to 21.7 dB, worst loss inside the band from 2.26 to 0.82 dB, and better rejection of unwanted signals at 9 and 11 GHz – 46 and 30 dB instead of 33 and 24.
It uses the same 59.4 mm waveguide on the same board – only the post sizes and positions changed.""")

# =============================== 8. Board + limits ===============================
s = prs.slides.add_slide(BLANK); bg(s, WHITE)
title(s, "Complete board, and what is still open")
picture(s, os.path.join(FIG, "fig_board.png"), 0.45, 1.3, w=6.7)
stat(s, 7.55, 1.4, 2.5, 1.9, "17.7 dB", "worst RL, improved board (paper board: 4.0 dB)", color=GREEN, big_size=28, label_size=13)
stat(s, 10.25, 1.4, 2.5, 1.9, "0.74 dB", "worst IL, improved board (paper board: 2.48 dB)", color=GREEN, big_size=28, label_size=13)
box(s, 7.55, 3.5, 5.2, 1.3, COPPERLT)
text(s, 7.8, 3.6, 4.75, 1.1, [[("Taper designed by us: ", {"bold": True, "color": COPPER}),
                                ("50 Ω microstrip → SIW, best width 7.5 mm. The paper does not give it.", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE)
box(s, 7.55, 5.0, 5.2, 1.85, PANEL)
text(s, 7.8, 5.1, 4.75, 1.65,
     [[("Limits: ", {"bold": True, "color": NAVY}), ("simulation only – nothing was fabricated or measured.", {})],
      [("On the full board RL dips to 17.7 dB at the upper edge (taper reflections). Next: tune taper and posts together.", {})]],
     size=14, anchor=MSO_ANCHOR.MIDDLE)
page(s, 8)
notes(s, """[Member 2 · 40 s]
The paper does not give its microstrip feed, so we designed the taper that connects a 50 ohm microstrip line to the SIW – the best width is 7.5 mm – and simulated the complete 96 by 20 mm board.
On the complete board our filter is still far better: worst return loss 17.7 dB against 4.0, worst loss 0.74 against 2.48 dB.
To be honest about the limits: this is simulation only, nothing was built or measured. And on the full board our return loss dips to 17.7 dB at the upper edge, because the tapers add their own small reflections – tuning the taper and the posts together is the next step.
Now we will show it running live in openEMS.""")

# =============================== 9. Live demo ===============================
s = prs.slides.add_slide(BLANK); bg(s, NAVY)
title(s, "Live demo in openEMS", dark=True)
demo = [("Show the 3-D model", ["& $py demo_live.py", "    improved --view"],
         "AppCSXCAD (openEMS's viewer) opens: rotate it, point at via walls, posts, ports", "~30 s"),
        ("Run the solver live", ["& $py demo_live.py", "    improved"],
         "Energy falls to −40 dB, then the plot opens: S11 stays below −20 dB in the green band", "~2 min"),
        ("Change something", ["& $py demo_live.py", "    iris3_cheby --L=11.6,12.6"],
         "Only if asked. Longer resonators move the filter down: 10.01 → 9.77 GHz", "~1 min")]
for i, (h_, cmd, what, t_) in enumerate(demo):
    x = 0.6 + i * 4.15
    box(s, x, 1.5, 3.9, 3.75, NAVY2)
    circle_num(s, x + 0.25, 1.72, i + 1)
    text(s, x + 0.9, 1.7, 2.2, 0.55, h_, size=17, bold=True, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 3.0, 1.7, 0.75, 0.55, t_, size=12, color=COPPER, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
    box(s, x + 0.25, 2.5, 3.4, 1.0, "0B1426", radius=0.06)
    text(s, x + 0.4, 2.55, 3.1, 0.9, cmd, size=12, font=MONO, color="F2C9A0", anchor=MSO_ANCHOR.MIDDLE, spacing=0)
    text(s, x + 0.25, 3.75, 3.4, 1.9, what, size=15, color=ICE)
text(s, 0.6, 6.15, 12.1, 0.4, [[("If anything fails: ", {"bold": True, "color": COPPER}),
     ("press Ctrl+C and show the saved plots in 04_Results/plots instead.", {})]], size=13, color=ICE)
text(s, 0.6, 5.55, 12.1, 0.5,
     [[("Before class: ", {"bold": True, "color": COPPER}),
       ('cd "$HOME\\Desktop\\SIW_Filter_Xband_openEMS\\03_openEMS_Simulation"   then   '
        '$py = "C:\\Users\\KRISH MEHTA\\openEMS_install\\py313\\tools\\python.exe"', {"font": MONO, "size": 11})]],
     size=13, color=ICE)
page(s, 9, dark=True)
notes(s, """[Both · about 3 min]
SETUP BEFORE CLASS: PowerShell open in 03_openEMS_Simulation, $py set, any Word files of the project closed.
1) Type:  & $py demo_live.py improved --view
   Say: "This is openEMS's own viewer, AppCSXCAD, showing the 3-D model we simulate: the substrate, the two via walls, the five posts and the waveguide ports at both ends." Rotate it with the mouse. Close it.
2) Type:  & $py demo_live.py improved
   Say while it runs: "openEMS has cut the structure into about 250 000 cells and is sending a pulse from 8 to 12 GHz through it. The 'Energy' number shows how much of the pulse is still inside; it stops at −40 dB, when only 0.01 % is left."
   When the plot opens: "Colour is the run we just did, black is our saved result – they lie on top of each other. The copper reflection curve stays below the green −20 dB line across the whole pass band."
3) Only if the professor asks to change something, e.g. longer resonators:
   & $py demo_live.py iris3_cheby --L=11.6,12.6
   Predict first: "Longer resonators resonate at a longer wavelength, so the filter should move down." Result: 10.01 → 9.77 GHz.
   Other quick ones: --d=7.0,4.6 (wider band), --er=2.2 (moves up to 10.30 GHz), --lossless (loss 0.59 → 0.01 dB).
If anything goes wrong: Ctrl+C, and show the saved plots in 04_Results/plots instead.""")

# =============================== 10. Conclusions ===============================
s = prs.slides.add_slide(BLANK); bg(s, NAVY)
title(s, "Conclusions", dark=True)
conc = ["Learned openEMS and scripted the complete SIW design flow in Python",
        "Validated the paper: 87 % of its values and all of its conclusions; found its 5th-order loss error",
        "Improved the filter: RL ≥ 21.7 dB and IL ≤ 0.82 dB over the whole band, on the same board",
        "Designed the microstrip taper and simulated the complete board"]
for i, c_ in enumerate(conc):
    y = 1.55 + i * 1.12
    circle_num(s, 0.6, y + 0.1, i + 1)
    text(s, 1.3, y, 6.6, 0.75, c_, size=17, color=WHITE, anchor=MSO_ANCHOR.MIDDLE)
box(s, 8.4, 1.55, 4.35, 2.2, NAVY2)
text(s, 8.65, 1.7, 3.9, 0.45, "Next steps", size=17, bold=True, color=COPPER)
text(s, 8.65, 2.2, 3.9, 2.2, [[("• ", {"color": COPPER}), ("Fabricate and measure with a VNA", {})],
                              [("• ", {"color": COPPER}), ("Tune taper and posts together", {})],
                              [("• ", {"color": COPPER}), ("Manufacturing-tolerance analysis", {})]],
     size=15, color=ICE, spacing=8)
text(s, 8.4, 4.35, 4.35, 0.9, "Thank you – questions?", size=26, font=HEAD, bold=True, color=WHITE)
text(s, 0.6, 6.45, 12, 0.4, "All scripts, results and the report: github.com/krishmehta5760-design/RFCC-Project",
     size=12, color=ICE)
page(s, 10, dark=True)
notes(s, """[Member 1 · 30 s]
To conclude: we learned openEMS and scripted the whole design flow; we validated the paper – 87 % of its numbers and all of its conclusions – and found an error in its 5th-order loss; and our improved filter meets the 20 dB matching target across the whole band with lower loss, on the same board.
Next steps would be to fabricate and measure it, tune the taper together with the posts, and check manufacturing tolerances.
Thank you – we are happy to take questions.""")

prs.save(OUT)
print("saved", OUT)
