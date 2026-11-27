"""Builds the project thesis (Word .docx, then PDF through MS Word) from the saved openEMS results.
Run with the openEMS Python (it has python-docx):   & $py make_thesis.py"""
import os, sys, json, subprocess
import numpy as np
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(BASE, "04_Results"); PL = os.path.join(RES, "plots"); TB = os.path.join(RES, "tables")
J = lambda fn: json.load(open(os.path.join(TB, fn), encoding="utf-8"))
f2 = lambda x: f"{x:.2f}"

# ------------------------------------------------------------------ data
val = J("validation_table.json"); imp = J("improved_design.json"); FB = J("full_board_results.json")
conv = J("mesh_convergence.json"); Kx = J("post_K_extraction.json")
KEYS = ["post3_butter", "post3_cheby", "iris3_butter", "iris3_cheby", "post5_cheby", "iris5_cheby", "iris3_cheby_vias"]
M = {k: J(f"metrics_{k}.json") for k in KEYS}
n_all = len(val); n_strict = sum(bool(r["strict_ok"]) for r in val); n_tol = sum(bool(r["tolerant_ok"]) for r in val)
V4, V3, V2 = (imp["variants"][k] for k in ("n4r003", "n3r003", "n3r002"))
m4, m3, m2, mp = V4["final"], V3["final"], V2["final"], M["post3_cheby"]
bp, bi = FB["board_paper_post3"], FB["board_improved_post3"]
calc_txt = open(os.path.join(BASE, "02_Design_Calculations", "design_calculations.txt"), encoding="utf-8").read()

NAVY = RGBColor(0x14, 0x21, 0x3D)


# ------------------------------------------------------------------ document helpers
def field(par, instr, placeholder=""):
    """Insert a Word field (PAGE, TOC ...) into a paragraph."""
    r = par.add_run()
    b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); r._r.append(b)
    r2 = par.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = instr; r2._r.append(it)
    r3 = par.add_run(); s = OxmlElement("w:fldChar"); s.set(qn("w:fldCharType"), "separate"); r3._r.append(s)
    par.add_run(placeholder)
    r5 = par.add_run(); e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); r5._r.append(e)


def page_format(section, fmt, start=None):
    pg = section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType"); section._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    if start is not None:
        pg.set(qn("w:start"), str(start))


class Thesis:
    def __init__(self):
        self.doc = d = Document()
        st = d.styles["Normal"]; st.font.name = "Times New Roman"; st.font.size = Pt(12)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        st.paragraph_format.line_spacing = 1.5; st.paragraph_format.space_after = Pt(6)
        for name, size, before, after in [("Heading 1", 18, 0, 18), ("Heading 2", 14, 12, 6), ("Heading 3", 12, 10, 4)]:
            h = d.styles[name]; h.font.name = "Times New Roman"; h.font.size = Pt(size); h.font.bold = True
            h.font.color.rgb = NAVY
            rf = h.element.rPr.rFonts; rf.set(qn("w:ascii"), "Times New Roman"); rf.set(qn("w:hAnsi"), "Times New Roman")
            for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
                if rf.get(qn(a)) is not None: del rf.attrib[qn(a)]
            h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(after)
            h.paragraph_format.keep_with_next = True; h.paragraph_format.line_spacing = 1.15
        for name in ("FigCaption", "TabCaption"):
            s = d.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH); s.base_style = d.styles["Normal"]
            s.font.size = Pt(10.5); s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            s.paragraph_format.line_spacing = 1.0; s.paragraph_format.space_after = Pt(10)
        d.styles["TabCaption"].paragraph_format.keep_with_next = True
        d.styles["TabCaption"].paragraph_format.space_before = Pt(6); d.styles["TabCaption"].paragraph_format.space_after = Pt(4)
        sec = d.sections[0]; sec.page_width, sec.page_height = Cm(21.0), Cm(29.7)
        sec.left_margin = Cm(3.0); sec.right_margin = Cm(2.5); sec.top_margin = Cm(2.5); sec.bottom_margin = Cm(2.5)
        sec.different_first_page_header_footer = True
        page_format(sec, "lowerRoman", 1)
        fp = sec.footer.paragraphs[0]; fp.alignment = WD_ALIGN_PARAGRAPH.CENTER; field(fp, "PAGE", "i")
        self.ch = 0; self.nfig = 0; self.ntab = 0; self.neq = 0
        self.textw = 15.5

    # --- text
    def center(self, text, size=12, bold=False, italic=False, after=6, color=None):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text); r.font.size = Pt(size); r.bold = bold; r.italic = italic
        if color: r.font.color.rgb = color
        p.paragraph_format.space_after = Pt(after); p.paragraph_format.line_spacing = 1.15
        return p

    def p(self, text, bold_prefix=None, italic=False, align="justify", size=None, after=6):
        par = self.doc.add_paragraph()
        if bold_prefix:
            rb = par.add_run(bold_prefix); rb.bold = True
        r = par.add_run(text); r.italic = italic
        if size: r.font.size = Pt(size)
        par.alignment = {"justify": WD_ALIGN_PARAGRAPH.JUSTIFY, "center": WD_ALIGN_PARAGRAPH.CENTER,
                         "left": WD_ALIGN_PARAGRAPH.LEFT}[align]
        par.paragraph_format.space_after = Pt(after)
        return par

    def bullets(self, items, style="List Bullet"):
        for it in items:
            par = self.doc.add_paragraph(style=style); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            par.paragraph_format.space_after = Pt(3)
            if isinstance(it, tuple):
                rb = par.add_run(it[0]); rb.bold = True; par.add_run(it[1])
            else:
                par.add_run(it)

    def numbered(self, items):
        for i, it in enumerate(items, 1):
            par = self.doc.add_paragraph(); par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            pf = par.paragraph_format; pf.space_after = Pt(3); pf.left_indent = Cm(0.75); pf.first_line_indent = Cm(-0.75)
            pf.tab_stops.add_tab_stop(Cm(0.75))
            par.add_run(f"{i}.\t{it}")

    def eq(self, text):
        self.neq += 1
        par = self.doc.add_paragraph(); tsx = par.paragraph_format.tab_stops
        tsx.add_tab_stop(Cm(self.textw / 2), WD_TAB_ALIGNMENT.CENTER); tsx.add_tab_stop(Cm(self.textw), WD_TAB_ALIGNMENT.RIGHT)
        par.add_run("\t")
        r = par.add_run(text); r.italic = True; r.font.name = "Cambria Math"; r.font.size = Pt(11)
        par.add_run(f"\t({self.ch}.{self.neq})")
        return f"({self.ch}.{self.neq})"

    def mono(self, text, size=8.5):
        for line in text.rstrip().splitlines():
            par = self.doc.add_paragraph(); par.paragraph_format.space_after = Pt(0); par.paragraph_format.line_spacing = 1.0
            r = par.add_run(line if line else " "); r.font.name = "Consolas"; r.font.size = Pt(size)

    # --- structure
    def chapter(self, title):
        self.ch += 1; self.nfig = self.ntab = self.neq = 0
        self.page_break()
        h = self.doc.add_heading(f"Chapter {self.ch}:  {title}", level=1)
        return h

    def front(self, title):
        self.page_break()
        h = self.doc.add_heading(title, level=1); h.alignment = WD_ALIGN_PARAGRAPH.CENTER

    def h2(self, text):
        return self.doc.add_heading(text, level=2)

    def h3(self, text):
        return self.doc.add_heading(text, level=3)

    def page_break(self):
        if len(self.doc.paragraphs):
            self.doc.paragraphs[-1].add_run().add_break(WD_BREAK.PAGE)

    def table(self, header, rows, caption, widths=None, font=10):
        self.ntab += 1; num = f"{self.ch}.{self.ntab}"
        if self.ch != 0:
            self.doc.add_paragraph(f"Table {num}: {caption}", style="TabCaption")
        t = self.doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, hc in enumerate(header):
            c = t.rows[0].cells[i]; c.text = ""
            r = c.paragraphs[0].add_run(str(hc)); r.bold = True; r.font.size = Pt(font)
            shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "D9E2F3")
            c._tc.get_or_add_tcPr().append(shd)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""; r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(font)
        if not widths:
            lens = []
            for i in range(len(header)):
                col = [str(header[i])] + [str(r_[i]) for r_ in rows]
                lens.append(min(max(max(len(w) for w in s.split()) if s.split() else 1 for s in col) * 0.6 + 0.4,
                                1.0 + 0.5 * max(len(s) for s in col) ** 0.75))
            tot = sum(lens); widths = [self.textw * x / tot for x in lens]
        scale = min(1.0, self.textw / sum(widths)); widths = [w * scale for w in widths]
        t.autofit = False
        tblPr = t._tbl.tblPr
        tw = tblPr.find(qn("w:tblW"))
        if tw is None:
            tw = OxmlElement("w:tblW"); tblPr.append(tw)
        tw.set(qn("w:w"), str(int(sum(widths) * 567))); tw.set(qn("w:type"), "dxa")
        lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblPr.append(lay)
        for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
            gc.set(qn("w:w"), str(int(w * 567)))
        for row in t.rows:
            for i, c in enumerate(row.cells):
                for par in c.paragraphs:
                    par.paragraph_format.line_spacing = 1.0; par.paragraph_format.space_after = Pt(1)
                c.width = Cm(widths[i])
        sp = self.doc.add_paragraph(); sp.paragraph_format.space_after = Pt(2); sp.paragraph_format.line_spacing = 1.0
        return f"Table {num}"

    def fig(self, path, caption, width_cm=15.0):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.nfig += 1; num = f"{self.ch}.{self.nfig}"
        self.doc.add_picture(path, width=Cm(width_cm))
        pic = self.doc.paragraphs[-1]; pic.alignment = WD_ALIGN_PARAGRAPH.CENTER
        pic.paragraph_format.keep_with_next = True; pic.paragraph_format.line_spacing = 1.0; pic.paragraph_format.space_after = Pt(2)
        self.doc.add_paragraph(f"Figure {num}: {caption}", style="FigCaption")
        return f"Figure {num}"

    def toc(self, instr):
        par = self.doc.add_paragraph(); field(par, instr, "Right-click and choose Update Field to build this list.")

    def main_matter(self):
        """Start the numbered chapters on a new section with Arabic page numbers starting at 1."""
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        sec.different_first_page_header_footer = False
        page_format(sec, "decimal", 1)

    def save(self, fn):
        self.doc.save(fn)


T = Thesis()
STUDENTS = "Krish Mehta (241EC224)   ·   Vishva Chavada (241EC212)"
SUPERVISOR = "Dr. Nagavel B"
DEPT = "Department of Electronics and Communication Engineering"
INST = "National Institute of Technology Karnataka, Surathkal"

# ================================================================== title page
for _ in range(2):
    T.center("", after=0)
T.center("DESIGN, FULL-WAVE MODELLING AND IMPROVEMENT OF A SUBSTRATE INTEGRATED WAVEGUIDE BAND-PASS FILTER "
         "FOR X-BAND APPLICATIONS USING openEMS", 18, bold=True, after=18, color=NAVY)
T.center("A thesis submitted in partial fulfilment of the requirements of the course", 12, italic=True, after=0)
T.center("RF Components and Circuits (RFCC) – Course Project", 13, bold=True, after=30)
T.center("Submitted by", 12, after=4)
T.center(STUDENTS, 12, bold=True, after=24)
T.center("Under the guidance of", 12, after=4)
T.center(SUPERVISOR, 12, bold=True, after=40)
T.center(DEPT, 13, bold=True, after=2)
T.center(INST, 13, bold=True, after=2)
T.center("November 2026", 12, after=0)

# ================================================================== certificate / declaration / acknowledgement
T.front("Certificate")
T.p("This is to certify that the thesis entitled “Design, Full-Wave Modelling and Improvement of a Substrate "
    "Integrated Waveguide Band-Pass Filter for X-Band Applications using openEMS”, submitted by "
    f"{STUDENTS}, is a record of the work carried out by them under my supervision as the course project of "
    "RF Components and Circuits (RFCC). The work presented here has not been submitted elsewhere for any other "
    "course or degree.")
T.p(""); T.p(""); T.p(SUPERVISOR, align="left"); T.p(DEPT + ", " + INST, align="left"); T.p("Date: ____________", align="left")

T.front("Declaration")
T.p("We declare that this thesis is our own work. All simulations were set up, run and post-processed by us with "
    "the open-source solver openEMS. The base design was taken from the published paper cited as [1], and every "
    "idea, equation, figure or result taken from other sources is acknowledged and referenced. The improved "
    "design, the full-wave inverter extraction, the transition design and all numerical results in this thesis "
    "were produced by us.")
T.p(""); T.p(""); T.p(STUDENTS, align="left"); T.p("Date: ____________", align="left")

T.front("Acknowledgement")
T.p(f"We thank {SUPERVISOR.split(',')[0]} for guiding this course project and for the freedom to choose an "
    "open-source tool. We thank the developers of openEMS and CSXCAD, Thorsten Liebig and contributors, for making a "
    "full-wave electromagnetic solver freely available, and the authors of the base paper, H. Bandar and "
    "N. Türker Tokan, for publishing complete design data, which made an independent validation possible.")

# ================================================================== abstract
T.front("Abstract")
T.p("Substrate integrated waveguide (SIW) technology builds a dielectric-filled rectangular waveguide inside an "
    "ordinary printed circuit board, with two rows of plated via holes as its side walls. It combines the low loss "
    "and shielding of metal waveguides with the low cost and planar integration of microstrip. This thesis "
    "presents the design, full-wave modelling, validation and improvement of an SIW band-pass filter for X-band "
    "radar and satellite applications, centred at 10 GHz with a 500 MHz pass band (9.75–10.25 GHz) on "
    "RT/Duroid 5870 (εr = 2.33, h = 1.57 mm).")
T.p("The work is carried out entirely with the free, open-source finite-difference time-domain (FDTD) solver "
    "openEMS, scripted in Python. A published design study comparing centred-post and inductive-iris SIW filters "
    "is first reproduced: seven filters (3rd-order Butterworth and Chebyshev post and iris filters, 5th-order "
    "Chebyshev post and iris filters, and an iris filter built from small vias) are rebuilt from their published "
    f"dimensions and simulated without tuning. Of the {n_all} values tabulated in the paper, {n_tol} "
    f"({100*n_tol/n_all:.0f} %) are reproduced within a ±0.5 % frequency tolerance, and all qualitative conclusions "
    "are confirmed. One inconsistency is identified: the 0.2 dB insertion loss reported for the 5th-order filters "
    "cannot be reached with the stated substrate loss; Cohn's formula predicts 1.05 dB and openEMS gives about "
    "1.1 dB.")
T.p("The validation reveals that the published 3rd-order Chebyshev post filter is poorly matched at the band edges "
    f"(return loss down to {mp['RL_min_band']:.1f} dB in openEMS). The cause is traced to post diameters read from a "
    "handbook chart. The impedance-inverter value and phase of a centred post are therefore extracted from "
    "full-wave simulations, and a new filter is synthesised from these data with a lower ripple and one more "
    "resonator. The resulting 4th-order filter fits in the same 59.4 mm SIW and achieves a return loss of at least "
    f"{m4['RL_min_band']:.1f} dB and an insertion loss of at most {m4['IL_max_band']:.2f} dB over the whole "
    f"specified band, with stop-band rejection improved from {mp['rej_9GHz']:.0f}/{mp['rej_11GHz']:.0f} dB to "
    f"{m4['rej_9GHz']:.0f}/{m4['rej_11GHz']:.0f} dB at 9/11 GHz. A parametric study explains how resonator "
    "length, coupling size, substrate permittivity, losses and filter order shape the response. Finally, a 50 Ω "
    "microstrip-to-SIW taper is designed and the complete 96.4 mm × 20 mm board is simulated: the improved board "
    f"keeps the insertion loss below {bi['IL_max_band']:.2f} dB with a return loss of {bi['RL_min_band']:.1f} dB or "
    f"better, against {bp['IL_max_band']:.2f} dB and {bp['RL_min_band']:.1f} dB for the published design.")
T.p("Keywords: substrate integrated waveguide, band-pass filter, X-band, inductive post, inductive iris, "
    "impedance inverter, FDTD, openEMS, microstrip-to-SIW transition.", italic=True)

# ================================================================== lists
T.front("Table of Contents")
T.toc('TOC \\o "1-3" \\h \\z \\u')
T.front("List of Figures")
T.toc('TOC \\h \\z \\t "FigCaption,1"')
T.front("List of Tables")
T.toc('TOC \\h \\z \\t "TabCaption,1"')
T.front("List of Abbreviations and Symbols")
T.table(["Abbreviation", "Meaning"], [
    ["SIW", "Substrate integrated waveguide"], ["RW", "Rectangular waveguide"], ["BPF", "Band-pass filter"],
    ["FDTD / EC-FDTD", "Finite-difference time-domain / equivalent-circuit FDTD"],
    ["FIT", "Finite integration technique (used by CST)"], ["PML", "Perfectly matched layer"],
    ["PEC", "Perfect electric conductor"], ["TE10", "Fundamental transverse-electric waveguide mode"],
    ["IL, RL", "Insertion loss (−|S21| in dB), return loss (−|S11| in dB)"], ["FBW", "Fractional bandwidth"],
    ["VNA", "Vector network analyser"], ["TRL", "Thru-reflect-line calibration"]], "Abbreviations", widths=[4, 11.5])
T.table(["Symbol", "Meaning", "Value in this work"], [
    ["f0", "Centre frequency", "10 GHz"], ["f1, f2", "Band edges", "9.75, 10.25 GHz"],
    ["εr, tan δ", "Substrate permittivity, loss tangent", "2.33, 0.0012"], ["h", "Substrate thickness", "1.57 mm"],
    ["d, p, as", "Via diameter, via pitch, row spacing", "1.3205, 1.9807, 15.9028 mm"],
    ["a_eff", "Equivalent waveguide width", "14.976 mm"], ["fc", "TE10 cut-off frequency", "6.557 GHz"],
    ["λg", "Guide wavelength", "26.013 mm at 10 GHz"], ["gk", "Low-pass prototype element values", "Table 4.2"],
    ["K/Z0", "Normalised impedance-inverter value", "Table 4.2"], ["φ", "Phase of a discontinuity", "Section 8.2"],
    ["Qu", "Unloaded quality factor of a resonator", "≈ 582"], ["n", "Filter order (number of resonators)", "3, 4, 5"]],
    "Symbols", widths=[2.6, 7.4, 5.5])

# ================================================================== CHAPTER 1
T.main_matter()
T.ch = 0
T.doc.add_heading("Chapter 1:  Introduction", level=1); T.ch = 1; T.nfig = T.ntab = T.neq = 0
T.h2("1.1 Background")
T.p("Microwave filters select a band of frequencies and reject the rest. They are found in every radio front end, "
    "where they keep strong out-of-band signals away from sensitive receivers and remove harmonics and noise from "
    "transmitters. X-band (8–12 GHz) is used by weather and marine radar, air-traffic control, synthetic-aperture "
    "radar and satellite links. Filters for these systems need a low pass-band insertion loss, a good match, steep "
    "skirts and, increasingly, a planar form that can be manufactured cheaply and integrated with the rest of the "
    "circuit.")
T.p("Two classic technologies sit at opposite ends of this trade-off. A metal rectangular waveguide (RW) filter has "
    "a very high unloaded quality factor (Q ≈ 5 000–10 000) and handles high power, but it is bulky, expensive to "
    "machine and hard to connect to planar circuits. A microstrip filter is cheap, small and planar, but its Q is "
    "only about 50–100 at X-band, so narrow-band microstrip filters are lossy and radiate.")
T.p("The substrate integrated waveguide (SIW), introduced by Deslandes and Wu [4], [5], bridges this gap. Two rows "
    "of metallised via holes are drilled through a printed circuit board (PCB); together with the top and bottom "
    "copper layers they form a dielectric-filled waveguide. An SIW keeps most of the low loss and the self-shielding "
    "of a waveguide (Q ≈ 500–1 000 at X-band) while being produced with a standard PCB process and connected "
    "directly to microstrip lines.")
T.h2("1.2 Motivation")
T.p("SIW filters are normally designed with classical waveguide filter theory and then tuned with a commercial "
    "full-wave solver such as CST Microwave Studio or Ansys HFSS. These tools need expensive licences, which limits "
    "independent checking of published designs. This project uses openEMS [12], a free and open-source FDTD solver "
    "driven by Python scripts. Two questions motivate the work: (i) can a free tool reproduce a published, "
    "commercially simulated SIW filter design, and (ii) can the same tool be used to find and correct weaknesses in "
    "that design?")
T.h2("1.3 Problem statement")
T.p("Design, model and analyse an SIW band-pass filter for X-band with centre frequency 10 GHz and 500 MHz bandwidth "
    "on RT/Duroid 5870, using a software tool learned during the course. Validate the published reference design "
    "[1] with this tool, identify its shortcomings, and propose an improved design that meets a return loss of 20 dB "
    "across the full 9.75–10.25 GHz band on the same substrate and board size.")
T.h2("1.4 Objectives")
T.numbered([
    "Learn the openEMS full-wave solver and build a parameterised Python model of an SIW with posts and irises.",
    "Verify the model on a plain SIW line before simulating any filter.",
    "Reproduce all seven filters of the base paper from their published dimensions and compare every tabulated "
    "result.",
    "Identify the cause of any disagreement or weakness in the published design.",
    "Design an improved filter with full-wave data and show that it meets the specification.",
    "Design the microstrip-to-SIW transition and simulate the complete, fabrication-ready board.",
    "Study how the main design parameters change the response, so that the design can be adjusted with "
    "confidence."])
T.h2("1.5 Contributions")
T.bullets([
    ("Independent validation: ", f"{n_tol} of {n_all} published values reproduced within ±0.5 % in frequency with a "
     "different numerical method (FDTD instead of FIT)."),
    ("Error found: ", "the 0.2 dB 5th-order insertion loss of the paper is shown to be physically implausible."),
    ("Full-wave design chart: ", "the inverter value K(d) and phase φ(d) of a centred SIW post were extracted, "
     "replacing the hand-read Marcuvitz chart."),
    ("Improved filter: ", f"a 4th-order design with RL ≥ {m4['RL_min_band']:.1f} dB and IL ≤ {m4['IL_max_band']:.2f} dB "
     "across the band, in the same 59.4 mm SIW."),
    ("Complete board: ", "a designed 50 Ω taper and a 96.4 mm × 20 mm board model, which the paper does not specify."),
    ("Open, reproducible workflow: ", "every result is produced by Python scripts that run with free software.")])
T.h2("1.6 Organisation of the thesis")
T.p("Chapter 2 reviews SIW technology, SIW filters and the base paper. Chapter 3 gives the theory of waveguides, "
    "SIW, filter synthesis and losses. Chapter 4 applies it to the analytical design. Chapter 5 describes the FDTD "
    "method and the openEMS model, including its verification. Chapter 6 validates the published filters. "
    "Chapter 7 is a parametric study. Chapter 8 presents the improved design, and Chapter 9 the transition and the "
    "complete board. Chapter 10 concludes and lists future work. The appendices give the design-calculation output "
    "and instructions to reproduce every result.")

# ================================================================== CHAPTER 2
T.chapter("Literature Review")
T.h2("2.1 Waveguide filters")
T.p("Direct-coupled waveguide filters, in which half-wavelength resonators are separated by inductive obstacles, "
    "were developed in the 1950s and are described in detail by Matthaei, Young and Jones [3]. The obstacles are "
    "modelled as impedance (K) inverters; their values follow from a low-pass prototype, and the resonator lengths "
    "are corrected for the phase of each obstacle. Marcuvitz's Waveguide Handbook [9] gives the equivalent circuits "
    "of posts and irises in chart form. Cohn [13] derived the dissipation loss of such filters in terms of the "
    "prototype values and the unloaded Q. Modern treatments are given by Hong and Lancaster [10] and by Cameron, "
    "Kudsia and Mansour [11].")
T.h2("2.2 Substrate integrated waveguide")
T.p("Deslandes and Wu presented the integrated microstrip-to-rectangular-waveguide structure in 2001 [4] and "
    "single-substrate waveguide filters in 2003 [5]. Cassivi et al. [6] showed that an SIW behaves like a "
    "rectangular waveguide of an equivalent width and gave an empirical formula for it. Xu and Wu [7] analysed the "
    "guided-wave and leakage characteristics and derived the via design rules d < λg/5 and p ≤ 2d that keep leakage "
    "between the vias negligible. Deslandes and Wu [8] later gave accurate design considerations for the SIW, and "
    "Deslandes [16] gave design equations for the tapered microstrip-to-SIW transition. Bozzi, Georgiadis and Wu "
    "[14] reviewed the wide range of SIW circuits and antennas that followed.")
T.h2("2.3 SIW filters")
T.p("Because an SIW supports the TE10 mode, all classical waveguide filter topologies can be transferred to it. "
    "Inductive posts are the simplest: a single extra via drilled in the centre of the guide. Inductive irises are "
    "made of two short via walls from the side rows. Cavity filters with cross couplings, dual-mode cavities and "
    "multilayer structures extend the selectivity further. Chen and Wu [15] reviewed SIW filter design techniques "
    "and structure innovations. Most published designs are tuned with commercial full-wave solvers.")
T.h2("2.4 The base paper")
T.p("Bandar and Türker Tokan [1] designed and compared post and iris SIW band-pass filters for X-band. They "
    "used RT/Duroid 5870, a 10 GHz centre frequency and a 500 MHz bandwidth, and designed 3rd-order Butterworth "
    "and Chebyshev (0.1 dB) filters and 5th-order Chebyshev filters, each with posts and with irises. They obtained "
    "the post diameters from Marcuvitz's chart, simulated all designs in CST Microwave Studio, compared an iris made "
    "of copper walls with one made of small vias, and fabricated and measured two prototypes. The paper publishes "
    "every dimension (Tables 1 and 2) and the simulated insertion and return loss at 9.75, 10 and 10.25 GHz "
    "(Tables 3 and 4). These complete data make it suitable for independent validation.")
T.h2("2.5 Electromagnetic simulation tools")
T.p("Full-wave solvers fall into frequency-domain methods (finite elements in HFSS, method of moments) and "
    "time-domain methods (FDTD [17], [18], and the finite integration technique in CST). Time-domain methods give "
    "a broadband response from a single run with a short pulse. openEMS [12] is an equivalent-circuit FDTD solver "
    "released under the GPL licence; geometry is described with the CSXCAD library from Python or MATLAB, and "
    "results are post-processed with standard scientific libraries.")
T.h2("2.6 Research gap")
T.bullets([
    "Published SIW filter designs are rarely checked independently, because the commercial solvers used to design "
    "them are expensive.",
    "The base paper reads post diameters from a chart by eye. The effect of this step on the final match is not "
    "studied.",
    "The base paper does not give the dimensions of its microstrip-to-SIW transition, so its complete board cannot "
    "be reproduced from the paper alone.",
    "This thesis addresses all three points with a free, scripted full-wave workflow."])

# ================================================================== CHAPTER 3
T.chapter("Theory")
T.h2("3.1 Rectangular waveguide and the TE10 mode")
T.p("A rectangular waveguide of width a filled with a dielectric of permittivity εr supports transverse-electric "
    "modes. The fundamental TE10 mode has its electric field across the narrow dimension and a half-sine variation "
    "across the width. It propagates only above the cut-off frequency")
T.eq("fc = c / (2 a √εr)")
T.p("Above cut-off, the guide wavelength and the propagation constant are")
T.eq("λg = λ / √(1 − (fc / f)²),    β = 2π / λg = √(k0² εr − (π / a)²)")
T.p("where λ = c/(f√εr) is the wavelength in the dielectric and k0 = 2πf/c. The wave impedance of the TE10 mode, "
    "used to normalise the S-parameters at a waveguide port, is")
T.eq("Z_TE = ω μ0 / β")
T.h2("3.2 Substrate integrated waveguide")
T.p("In an SIW the narrow walls are replaced by rows of vias of diameter d and pitch p, a distance as apart. The "
    "fields leak slightly between the vias, so the SIW behaves like a solid-wall waveguide that is a little "
    "narrower. A widely used equivalent width is [6], [7]")
T.eq("a_eff = as − d² / (0.95 p)")
T.p("Leakage between the vias stays negligible when d < λg/5 and p ≤ 2d [7]. As long as the via rows are "
    "continuous along the propagation direction, only TE(m0) modes exist; TM modes and TE modes with variation "
    "across the thickness are not supported because the side walls cannot carry longitudinal currents. The "
    "single-mode band therefore extends from the TE10 cut-off to the TE20 cut-off at 2fc.")
T.h2("3.3 Scattering parameters and filter specifications")
T.p("A two-port filter is described by its scattering parameters: S11 is the ratio of reflected to incident wave at "
    "port 1, and S21 is the ratio of transmitted to incident wave. In decibels")
T.eq("IL = −20 log10 |S21|,    RL = −20 log10 |S11|")
T.p("A good pass band has a small insertion loss (IL), well below 1 dB, and a large return loss (RL), usually at "
    "least 20 dB, which means that less than 1 % of the incident power is reflected. Outside the pass band, |S21| "
    "should be as small as possible; this is the rejection or selectivity. For a lossless filter |S11|² + |S21|² = 1, "
    "so a return loss of 20 dB corresponds to a mismatch loss of only 0.04 dB.")
T.h2("3.4 Low-pass prototype: Butterworth and Chebyshev")
T.p("Filter synthesis starts from a normalised low-pass prototype with element values g0, g1, …, gn+1. A Butterworth "
    "(maximally flat) response places all reflection zeros at the centre frequency: the pass band is smooth, but "
    "the response rolls off slowly. A Chebyshev response spreads the n reflection zeros across the pass band and "
    "allows a small equal ripple LAr in the pass band in exchange for steeper skirts. The ripple fixes the minimum "
    "return loss in the pass band:")
T.eq("RL_min = −10 log10 (1 − 10^(−LAr/10))")
T.p("A 0.1 dB ripple gives RL_min = 16.4 dB, a 0.03 dB ripple gives 21.6 dB, and a 0.02 dB ripple gives 23.4 dB. "
    "This relation is central to the improvement in Chapter 8: a filter designed for 0.1 dB ripple cannot reach a "
    "20 dB return loss over its full ripple band even if it is built perfectly.")
T.p("The selectivity grows with the order n: far from the pass band the attenuation of an n-th order filter "
    "increases by about 20n dB per decade of normalised frequency. Higher order therefore means steeper skirts, "
    "but also more resonators and more loss.")
T.h2("3.5 Impedance inverters and direct-coupled waveguide filters")
T.p("A band-pass waveguide filter is built from n half-wavelength resonators separated by n + 1 inductive "
    "obstacles. Each obstacle, together with short lengths of line on either side, acts as an impedance inverter K. "
    "With the guide-wavelength fractional bandwidth")
T.eq("wλ = (λg1 − λg2) / λg0,    λg0 = (λg1 + λg2) / 2")
T.p("the normalised inverter values follow from the prototype [3]:")
T.eq("K01/Z0 = √(π wλ / (2 g0 g1)),    Kj,j+1/Z0 = (π wλ / 2) / √(gj gj+1)")
T.p("A shunt inductive reactance X realises an inverter K when")
T.eq("X/Z0 = (K/Z0) / (1 − (K/Z0)²)")
T.p("and the obstacle adds a phase φ = −atan(2X/Z0). The electrical length of resonator j is then")
T.eq("θj = π + ½ (φj−1,j + φj,j+1),    Lj = λg0 θj / (2π)")
T.p("Strong coupling (large K) needs a weak obstacle: a thin post or a wide iris window. Weak coupling needs a "
    "strong obstacle: a thick post or a narrow window. The outer couplings K01 are the strongest, so the outer posts "
    "are the thinnest and the outer windows the widest.")
T.h2("3.6 Inductive posts and irises")
T.p("A centred metal post is not a pure shunt inductance: its equivalent circuit is a T-network with a shunt "
    "reactance Xp and two series reactances Xs. From its S-parameters, referred to the post plane, [3], [19]")
T.eq("jXs = (1 − S21 + S11) / (1 − S11 + S21),    jXp = 2 S21 / ((1 − S11)² − S21²)")
T.p("and the equivalent inverter and its phase are")
T.eq("φ = −atan(2Xp + Xs) − atan(Xs),    K/Z0 = |tan(φ/2 + atan Xs)|")
T.p("The base paper reads the post diameter for a required K from Marcuvitz's chart [9]. Chapter 8 replaces this "
    "step by evaluating the two equations above with full-wave S-parameters. An inductive iris is a thin wall with a "
    "window of width w; for thin irises the series reactance is negligible and the simple shunt model of Section "
    "3.5 holds.")
T.h2("3.7 Losses and quality factor")
T.p("The loss of an SIW resonator has a dielectric part and a conductor part. The dielectric quality factor is "
    "Qd = 1/tan δ, and the conductor quality factor Qc follows from the surface resistance Rs = √(ωμ0/2σ) of the "
    "copper. The unloaded quality factor is")
T.eq("1/Qu = 1/Qd + 1/Qc")
T.p("Cohn's formula [13] estimates the mid-band insertion loss of an n-resonator filter from the prototype values "
    "and the fractional bandwidth w:")
T.eq("IL0 ≈ 4.343 Σ gk / (w Qu)   dB")
T.p("Loss therefore grows with the order (more terms in the sum) and with a narrower bandwidth.")
T.h2("3.8 Microstrip-to-SIW transition")
T.p("A 50 Ω microstrip line has a quasi-TEM field concentrated under the strip, while the SIW has the TE10 field "
    "spread across its width. A linear taper widens the strip gradually so that the field changes shape smoothly "
    "[16]. The taper width at the SIW and the taper length are chosen to minimise the reflection over the band. The "
    "50 Ω strip width follows from Hammerstad's formulas [20].")

# ================================================================== CHAPTER 4
T.chapter("Analytical Design")
T.h2("4.1 Specifications")
T.table(["Parameter", "Value (from the base paper [1])"], [
    ["Centre frequency f0", "10 GHz"], ["Bandwidth", "500 MHz (9.75–10.25 GHz), FBW = 5 %"],
    ["Responses", "Chebyshev 0.1 dB ripple and Butterworth"], ["Orders", "3rd and 5th"],
    ["Substrate", "Rogers RT/Duroid 5870, εr = 2.33, tan δ = 0.0012, h = 1.57 mm, 35 µm Cu"],
    ["SIW", "via d = 1.3205 mm, pitch p = 1.9807 mm, row spacing as = 15.9028 mm, L = 59.421 mm, W = 20 mm"],
    ["Iris made of vias", "via diameter 0.2 mm, 0.6 mm spacing"], ["Board size (with feeds)", "96.4 mm × 20 mm"],
    ["Target of this work", "RL ≥ 20 dB and IL ≤ 1 dB over 9.75–10.25 GHz"]],
    "Design specifications", widths=[5, 10.5])
T.h2("4.2 SIW dimensions")
T.p("The equivalent X-band waveguide is WR-90 with a = 22.86 mm. Filled with εr = 2.33, the same cut-off is "
    "obtained with a = 22.86/√2.33 = 14.976 mm. With the paper's vias, Eq. (3.4) gives a_eff = 14.976 mm, so the SIW "
    "is equivalent to a dielectric-filled WR-90. Its TE10 cut-off is fc = 6.557 GHz and the TE20 mode cuts off at "
    "13.11 GHz, so the SIW is single-mode over the whole X-band. The via rules are satisfied: d = 1.32 mm < "
    "λg/5 = 4.99 mm and p = 1.98 mm < 2d = 2.64 mm.")
T.h2("4.3 Prototype values and inverters")
T.p("At the band edges and centre the guide wavelengths are λg(9.75 GHz) = 27.218 mm, λg(10 GHz) = 26.013 mm and "
    "λg(10.25 GHz) = 24.930 mm, which gives wλ = 0.0878 for the 5 % bandwidth. Table 4.2 lists the prototype and "
    "inverter values for the 3rd-order Chebyshev design; the full output of the design script is in Appendix A.")
T.table(["Quantity", "Value"], [
    ["w, wλ", "0.050, 0.0878"], ["g (Chebyshev 0.1 dB, n = 3)", "g0 … g4 = 1, 1.0316, 1.1474, 1.0316, 1"],
    ["K01/Z0, K12/Z0", "0.3656, 0.1267"],
    ["L1, L2 from the thin-iris model", "11.059, 11.991 mm"],
    ["L1, L2 of the paper's iris filter", "11.072, 12.004 mm (difference 0.013 mm)"]],
    "Analytical design of the 3rd-order Chebyshev filter", widths=[7, 8.5])
T.p("The analytical iris spacings agree with the paper's Table 1 to 13 µm, which confirms that the design equations "
    "were read correctly. The post spacings of the paper are longer than these values because a post also has the "
    "series reactance Xs of Section 3.6.")
T.h2("4.4 Published filter dimensions")
T.table(["Filter", "d1", "d2", "d3", "L1", "L2", "L3"], [
    ["Post, Butterworth (3rd)", "0.6839", "2.6092", "–", "11.8278", "13.4635", "–"],
    ["Post, Chebyshev (3rd)", "0.7056", "2.2498", "–", "11.5898", "12.9377", "–"],
    ["Iris, Butterworth (3rd)", "6.5529", "3.6342", "–", "11.1705", "12.2438", "–"],
    ["Iris, Chebyshev (3rd)", "6.5046", "4.0802", "–", "11.0723", "12.0042", "–"],
    ["Post, Chebyshev (5th)", "0.7821", "2.4461", "2.8122", "11.8161", "13.4868", "13.7464"],
    ["Iris, Chebyshev (5th)", "6.3682", "3.8539", "3.4179", "11.2304", "12.2704", "12.3769"]],
    "Filter dimensions from the base paper in mm (post: d = diameter; iris: d = window width; L = spacing). The "
    "filters are symmetric, so only half of the values are listed.", font=9)
T.h2("4.5 Quality factor and loss estimate")
T.p("For a half-wavelength SIW cavity on this substrate the design script gives Qc ≈ 1 935 for the copper walls "
    "and Qd = 833 for the dielectric, so Qu ≈ 582. Cohn's formula (3.14) then predicts a mid-band insertion loss of "
    "0.48 dB for the 3rd-order and 1.05 dB for the 5th-order Chebyshev filter. These estimates are used in Chapter 6 "
    "to judge the published loss values.")

# ================================================================== CHAPTER 5
T.chapter("Full-Wave Modelling in openEMS")
T.h2("5.1 The FDTD method")
T.p("The finite-difference time-domain method [17], [18] solves Maxwell's curl equations directly in time. Space "
    "is divided into a rectilinear grid of cells. In Yee's scheme the electric-field components are placed on the "
    "cell edges and the magnetic-field components on the face centres, so that every curl is a simple difference "
    "of neighbouring values. The E- and H-fields are updated alternately, half a time step apart (leapfrog). The "
    "scheme is explicit and stable only if the time step obeys the Courant limit")
T.eq("Δt ≤ 1 / ( c √(1/Δx² + 1/Δy² + 1/Δz²) )")
T.p("so the smallest cell sets the time step. In our models Δt ≈ 0.27 ps and a run needs 25 000–50 000 steps. "
    "openEMS uses the equivalent-circuit formulation of FDTD (EC-FDTD), which handles graded meshes and lossy "
    "materials well. Because the excitation is a short pulse, one run gives the response over the whole band; the "
    "frequency-domain S-parameters are obtained by Fourier transforming the port voltages and currents.")
T.h2("5.2 openEMS and CSXCAD")
T.p("openEMS v0.37.0 was used. The geometry is described with the CSXCAD library: materials (properties) are "
    "created and primitives (boxes, cylinders, polygons) are assigned to them. The mesh, the excitation, the ports "
    "and the boundary conditions are set from Python, the solver runs as a separate executable on four threads, and "
    "NumPy and Matplotlib are used for post-processing. AppCSXCAD shows the 3-D model.")
T.h2("5.3 Geometry")
T.bullets([
    ("Coordinates: ", "x is the propagation direction, y the SIW width and z the substrate thickness."),
    ("Substrate: ", "a box with εr = 2.33 and the loss of Section 5.4."),
    ("Vias and posts: ", "metal cylinders through the full substrate thickness."),
    ("Irises: ", "zero-thickness metal walls from the via rows to the edge of the window; for the paper's Fig. 11 case "
     "they are rows of 0.2 mm vias at 0.6 mm pitch."),
    ("Feeds: ", "short solid-wall waveguide sections of width a_eff with TE10 ports (as in the paper's CST set-up), "
     "or, for the complete board, 50 Ω microstrip lines with linear tapers.")])
T.fig(os.path.join(PL, "geom_post3_cheby.png"), "openEMS model of the paper's 3rd-order Chebyshev post filter (top "
      "view). The dashed boxes are the waveguide feed sections with the ports.")
T.fig(os.path.join(PL, "geom_iris3_cheby.png"), "openEMS model of the paper's 3rd-order Chebyshev iris filter")
T.h2("5.4 Materials and losses")
T.p("The dielectric loss is entered as a conductivity κ = 2πf0ε0εr tan δ. In the waveguide-port models the top and "
    "bottom copper layers are the z-boundaries of the computational domain (perfect conductors), which makes the "
    "models much faster. The loss of these broad walls (Rs = 26 mΩ at 10 GHz) is added as an equivalent loss tangent "
    "tan δc = 2βαc/k² = 4.6 × 10⁻⁴ [2]. In the complete-board model the top copper is a 35 µm conducting sheet "
    "with σ = 5.8 × 10⁷ S/m. Because the copper sheet is not drawn in the fast model, openEMS prints the warning "
    "“No primitives found in property: copper”, which is expected.")
T.h2("5.5 Mesh")
T.p("A graded rectilinear mesh is used: at most 0.30 mm along x (about λ/55 in the dielectric at 12 GHz), refined to "
    "0.06 mm around the posts and the iris edges and to 0.2 mm around the via rows, with four cells across the "
    "substrate. Mesh lines are placed exactly on every metal edge and sheet, which is essential for thin metal "
    "sheets in FDTD. The filter models contain 0.1–0.4 million cells; the complete board has about 1.1 million.")
T.h2("5.6 Excitation, ports and boundaries")
T.p("A Gaussian pulse covering 7.8–12.2 GHz excites the TE10 port. The waveguide ends are terminated by 8-cell "
    "perfectly matched layers [21]; Mur absorbing boundaries [22] are used elsewhere. The simulation stops when the "
    "energy left in the domain has fallen by 40 dB, i.e. to 0.01 % of its peak. The port impedance is corrected for "
    "the dielectric filling, Z_TE = ωμ0/β with β from Eq. (3.2).")
T.h2("5.7 Post-processing")
T.p("S11 and S21 are computed from the incident and reflected port waves at 801 frequencies from 8 to 12 GHz. From "
    "them the scripts extract the insertion and return loss at 9.75, 10 and 10.25 GHz, the 3 dB band and its centre, "
    "the band where RL ≥ 20 dB, the worst RL and IL inside 9.75–10.25 GHz, and the rejection at 9 and 11 GHz. "
    "Touchstone (.s2p) files are written for every design so that the results can be loaded into other RF tools.")
T.h2("5.8 Verification on a plain SIW line")
T.p("Before any filter was simulated, a plain SIW line with the paper's vias was modelled. |S11| stays below −40 dB "
    "from 8 to 12 GHz, which shows that the via-wall SIW and the solid-wall feed of width a_eff are equivalent and "
    "that the ports are set up correctly. |S21| is about −0.2 dB over 77 mm, a loss of about 3.0 dB/m, which matches "
    "the analytical αd + αc = 0.35 Np/m = 3.05 dB/m.")
T.fig(os.path.join(PL, "siw_line.png"), "openEMS result for the plain SIW line (no resonators)")
T.h2("5.9 Mesh convergence")
T.p(conv["text"])
T.h2("5.10 Software workflow")
T.table(["Script", "Purpose"], [
    ["02_Design_Calculations/siw_design_calc.py", "Analytical design (Chapter 4)"],
    ["03_openEMS_Simulation/siw_model.py", "Model library: geometry, mesh, ports, run, S-parameters, metrics"],
    ["run_line_test.py", "Plain SIW line (Section 5.8)"], ["run_mesh_convergence.py", "Mesh convergence (Section 5.9)"],
    ["run_paper_validation.py", "All seven published filters (Chapter 6)"],
    ["run_improvement.py", "K(d) extraction and improved designs (Chapter 8)"],
    ["run_fullboard.py", "Transition sweep and complete boards (Chapter 9)"],
    ["demo_live.py", "Single runs and parameter changes from the command line (Chapter 7)"],
    ["run_all.py", "Runs everything in order and rebuilds all plots and documents"]],
    "Scripts of the project", widths=[7.5, 8])

# ================================================================== CHAPTER 6
T.chapter("Validation of the Published Designs")
T.p("All seven filters of the base paper were built from the published dimensions and simulated in openEMS without "
    "any tuning. Figures 6.1–6.4 correspond to the paper's Figs. 8a, 8b, 9 and 11.")
T.fig(os.path.join(PL, "Fig8a_3rd_butterworth.png"), "3rd-order post and iris filters, Butterworth response (cf. paper Fig. 8a)", 14)
T.fig(os.path.join(PL, "Fig8b_3rd_chebyshev.png"), "3rd-order post and iris filters, Chebyshev response (cf. paper Fig. 8b)", 14)
T.fig(os.path.join(PL, "Fig9_5th_chebyshev.png"), "5th-order post and iris filters, Chebyshev response (cf. paper Fig. 9)", 14)
T.fig(os.path.join(PL, "Fig11_iris_walls_vs_vias.png"), "Iris filter with copper walls vs. small vias (cf. paper Fig. 11)", 14)
T.h2("6.1 Reading the responses")
T.p("Each plot shows |S21| (transmission) and |S11| (reflection). In the pass band |S21| is close to 0 dB and |S11| "
    "shows one reflection zero (dip) per resonator: three for the 3rd-order Chebyshev filters and five for the "
    "5th-order filters. The Butterworth filters show a single deep dip, because their reflection zeros all coincide "
    "at the centre frequency. Outside the pass band |S21| falls steeply; the 5th-order filters fall fastest.")
T.h2("6.2 Point-by-point comparison")
T.p("Each IL and RL value in the paper's Tables 3 and 4 is compared with openEMS at exactly the same frequency (strict "
    "check) and with the closest openEMS value within ±50 MHz (±0.5 %), which allows for the small frequency offset "
    "expected between two different solvers. A value is counted as validated when IL agrees within 0.5 dB (or 30 %) "
    "and RL within 3 dB (or 30 %, or both values above 20 dB).")
rows = [[r["label"], r["quantity"], f"{r['f_GHz']:.2f}", r["paper"], r["openEMS"], "✓" if r["strict_ok"] else "✗",
         r["openEMS_within_50MHz"], "✓" if r["tolerant_ok"] else "✗"] for r in val]
T.table(["Filter", "Qty", "f (GHz)", "Paper (dB)", "openEMS (dB)", "OK", "openEMS ±0.5 % (dB)", "OK"], rows,
        "Validation of every numerical result in Tables 3 and 4 of the base paper", font=8)
T.p(f"{n_strict} of {n_all} values ({100*n_strict/n_all:.0f} %) agree at exactly the same frequency, and {n_tol} of "
    f"{n_all} ({100*n_tol/n_all:.0f} %) agree within ±0.5 % in frequency.", bold_prefix="Validation score: ")
T.h2("6.3 Global characteristics")
rows = []
for k, lab in [("post3_butter", "Post 3rd Butterworth"), ("post3_cheby", "Post 3rd Chebyshev"),
               ("iris3_butter", "Iris 3rd Butterworth"), ("iris3_cheby", "Iris 3rd Chebyshev"),
               ("post5_cheby", "Post 5th Chebyshev"), ("iris5_cheby", "Iris 5th Chebyshev"),
               ("iris3_cheby_vias", "Iris 3rd (small vias)")]:
    m = M[k]
    rows.append([lab, f2(m["f0_3dB_GHz"]), f"{m['BW3dB_MHz']:.0f}", f2(m["IL_min"]), f2(m["IL_f0"]),
                 f2(m["RL_min_band"]), f"{m['rej_9GHz']:.1f}", f"{m['rej_11GHz']:.1f}"])
T.table(["Filter (openEMS)", "f0 (GHz)", "3 dB BW (MHz)", "min IL (dB)", "IL @10 GHz (dB)", "worst RL in band (dB)",
         "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"], rows, "Global characteristics of the published filters in openEMS", font=8.5)
T.p("The following conclusions of the base paper are confirmed:")
T.bullets([
    f"All filters are centred at 10 GHz: the 3 dB centre frequencies lie between {min(M[k]['f0_3dB_GHz'] for k in M):.2f} "
    f"and {max(M[k]['f0_3dB_GHz'] for k in M):.2f} GHz (offset at most 0.8 %).",
    "The responses have the designed orders and types.",
    "The mid-band IL of the 3rd-order filters (0.6–0.8 dB) and their mid-band RL agree with the paper.",
    f"For the 3rd-order Chebyshev designs the post filter has the wider bandwidth ({M['post3_cheby']['BW3dB_MHz']:.0f} MHz "
    f"against {M['iris3_cheby']['BW3dB_MHz']:.0f} MHz for the iris).",
    "Replacing the iris walls with small vias leaves the response essentially unchanged, so the iris can be "
    "manufactured with the normal via process.",
    "The 5th-order filters are much more selective, with more than 50 dB rejection at 9 and 11 GHz."])
T.h2("6.4 Discussion of the differences")
T.bullets([
    ("Small frequency offset. ", "openEMS places the post filters about 0.6 % lower and the iris filters within 0.2 % "
     "of the paper. The mesh-convergence test moves f0 by only 0.1 %, so the offset is not a discretisation error. "
     "It comes from modelling differences: a different numerical method (FDTD vs. FIT), the paper's unknown CST "
     "settings (port de-embedding, wall thickness, termination of the via walls) and rounding of the published "
     "dimensions. Because the band edges lie on steep skirts, a 0.5 % shift changes the band-edge values by several "
     "dB, which explains most strict mismatches."),
    ("5th-order insertion loss. ", "The paper reports 0.2 dB at 10 GHz for its 5th-order filters, less than its own "
     "3rd-order filters (0.78–0.89 dB). This is physically implausible: with tan δ = 0.0012 and copper walls Cohn's "
     f"formula gives 1.05 dB, and openEMS gives {M['post5_cheby']['IL_f0']:.2f} dB (post) and "
     f"{M['iris5_cheby']['IL_f0']:.2f} dB (iris). The paper's 5th-order simulations were probably run with lower or "
     "no losses."),
    ("Measured results. ", "The paper's measured IL of about 4 dB is mostly cable, connector and fabrication loss, as "
     "the paper itself notes; it cannot be reproduced without fabrication.")])

# ================================================================== CHAPTER 7  parametric study
T.chapter("Parametric Study")
T.p("To understand how each design parameter shapes the response, the paper's 3rd-order Chebyshev iris filter was "
    "re-simulated with one parameter changed at a time, using the command-line tool demo_live.py. Each run takes "
    "about one minute. In the figures the coloured curves are the changed design and the black curves the original.")
T.table(["Change (iris3_cheby)", "Centre f (GHz)", "3 dB BW (MHz)", "IL @10 GHz (dB)", "worst RL in band (dB)",
         "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"], [
    ["Original design", "10.010", "660", "0.59", "12.8", "40.4", "25.9"],
    ["Longer resonators, L = 11.6, 12.6 mm", "9.773", "595", "1.34", "0.5", "33.9", "31.1"],
    ["Wider windows, d = 7.0, 4.6 mm", "9.877", "825", "0.59", "5.5", "27.7", "21.9"],
    ["Lower permittivity, εr = 2.2", "10.303", "675", "1.87", "0.3", "44.2", "18.2"],
    ["All losses switched off", "10.008", "665", "0.01", "12.2", "41.2", "25.6"]],
    "Effect of single parameter changes on the 3rd-order iris filter", font=8.5)
T.h2("7.1 Resonator length")
T.p("Increasing the spacings by about 0.5 mm lengthens each half-wavelength resonator, so it resonates at a longer "
    "wavelength, i.e. a lower frequency. The pass band moves from 10.01 to 9.77 GHz (−2.4 %), close to the "
    "first-order estimate ΔL/L ≈ 4 % scaled by the dispersion of the guide. The values in the specified band "
    "therefore degrade (RL 0.5 dB at the upper band edge): the resonator length is the main tool for setting the "
    "centre frequency.")
T.fig(os.path.join(PL, "parametric", "whatif_iris3_cheby_L_11.6_12.6.png"), "Longer resonators move the pass band down")
T.h2("7.2 Coupling strength")
T.p("Widening the iris windows weakens the obstacles and increases every inverter value K. The resonances split "
    "further apart and the 3 dB bandwidth grows from 660 to 825 MHz. The match degrades (worst RL 5.5 dB) because "
    "the couplings are no longer in the ratio required by the prototype. The coupling sizes therefore set the "
    "bandwidth and, together, the ripple level.")
T.fig(os.path.join(PL, "parametric", "whatif_iris3_cheby_d_7.0_4.6.png"), "Wider iris windows give stronger coupling and a wider band")
T.p("The same effect, in the opposite direction, is seen for the post filter: thicker posts (d = 0.85, 2.5 mm "
    "instead of 0.71, 2.25 mm) give weaker coupling, and the bandwidth shrinks from 700 to 615 MHz. The centre also "
    "moves up, from 9.94 to 10.10 GHz, because a thicker post adds a larger negative phase φ, which shortens the "
    "resonators electrically (Eq. 3.10).")
T.fig(os.path.join(PL, "parametric", "whatif_post3_cheby_d_0.85_2.5.png"), "Thicker posts give weaker coupling, a narrower band and a higher centre frequency")
T.h2("7.3 Substrate permittivity")
T.p("Lowering εr from 2.33 to 2.2 makes the wave faster. All electrical lengths become shorter and the filter moves "
    "up to 10.30 GHz. The ratio of the centre frequencies, 10.303/10.010 = 1.029, matches √(2.33/2.2) = 1.029. This "
    "shows why a tight permittivity tolerance of the substrate matters for narrow-band SIW filters.")
T.fig(os.path.join(PL, "parametric", "whatif_iris3_cheby_er_2.2.png"), "Lower substrate permittivity moves the pass band up")
T.h2("7.4 Losses")
T.p("With all losses switched off, the mid-band IL drops from 0.59 dB to 0.01 dB while the shape of the response "
    "is unchanged. The 0.6 dB of the real filter is therefore almost entirely dissipation in the dielectric and the "
    "copper, consistent with Cohn's estimate of 0.48 dB.")
T.fig(os.path.join(PL, "parametric", "whatif_iris3_cheby_lossless.png"), "Lossless and lossy responses of the iris filter")
T.h2("7.5 Filter order and response type")
T.p("Two published variants were also run with the same tool. The 5th-order Chebyshev iris filter shows five "
    "reflection zeros and much steeper skirts (rejection 54 dB at 9 GHz instead of 37–40 dB) at the price of a higher "
    "mid-band loss (1.19 dB). The 3rd-order Butterworth iris filter shows a single deep reflection zero at the centre; "
    "its 3 dB bandwidth is only 470 MHz, so it does not cover the specified band.")
T.fig(os.path.join(PL, "parametric", "demo_iris5_cheby.png"), "5th-order Chebyshev iris filter: five reflection zeros and steep skirts")
T.fig(os.path.join(PL, "parametric", "demo_iris3_butter.png"), "3rd-order Butterworth iris filter: a single, maximally flat reflection zero")
T.h2("7.6 Summary of the design rules")
T.table(["Parameter", "Increase it and …"], [
    ["Resonator length L", "the centre frequency goes down"],
    ["Coupling (wider window / thinner post)", "the bandwidth grows; ripple and match change if the ratios are wrong"],
    ["Substrate permittivity εr", "the centre frequency goes down as 1/√εr"],
    ["Loss tangent and copper loss", "the insertion loss grows; the shape stays the same"],
    ["Filter order n", "the skirts get steeper and the loss grows"],
    ["Chebyshev ripple", "the skirts get steeper and the in-band return loss falls"]],
    "Design rules confirmed by the parametric study", widths=[6, 9.5])

# ================================================================== CHAPTER 8 improvement
T.chapter("Improved Filter Design")
T.h2("8.1 Shortcoming of the published design")
T.p("The paper's 3rd-order Chebyshev post filter does not cover the specified 500 MHz with a good match. Its own "
    "Table 3 gives RL = 14 dB and 10.7 dB and IL = 1.23 dB and 1.33 dB at 9.75 and 10.25 GHz. In openEMS the band with "
    f"RL ≥ 20 dB runs only from {mp['RL20_lo_GHz']:.2f} to {mp['RL20_hi_GHz']:.2f} GHz, and inside the specified band "
    f"the RL falls to {mp['RL_min_band']:.1f} dB while the IL rises to {mp['IL_max_band']:.2f} dB.")
T.fig(os.path.join(PL, "post3_cheby.png"), "The paper's 3rd-order Chebyshev post filter in openEMS (squares: values from the paper's Table 3)", 14)
T.p("Two causes add up. First, a 0.1 dB ripple limits the in-band RL to 16.4 dB even for a perfect filter "
    "(Section 3.4). Second, the post diameters were read by eye from Marcuvitz's chart, so the realised inverter "
    "values differ from the required ones, as shown next.")
T.h2("8.2 Full-wave inverter extraction")
T.p("A single centred post in the SIW was simulated in openEMS (lossless) for ten diameters from 0.4 to 3.0 mm. The "
    "S-parameters were de-embedded to the post plane, and the T-network, inverter value and phase were extracted "
    "with Eqs. (3.11) and (3.12).")
T.table(["d (mm)"] + [f"{t['d']:.2f}" for t in Kx],
        [["K/Z0"] + [f"{t['K']:.3f}" for t in Kx], ["φ (deg)"] + [f"{np.degrees(t['phi']):.1f}" for t in Kx]],
        "Extracted inverter value and phase of a centred post at 10 GHz", font=8)
T.fig(os.path.join(PL, "post_K_phi_extraction.png"), "Full-wave inverter curves K(d) and φ(d): a digital replacement for the Marcuvitz chart")
pk = imp["paper_post_K_from_extraction"]["K"]
T.p(f"For the paper's posts the extraction gives K/Z0 = {pk[0]:.3f} and {pk[1]:.3f}, while the design requires "
    "0.366 and 0.127. The couplings are 4–6 % too strong, which widens the band and detunes the resonators enough "
    "to spoil the match at the band edges.")
T.h2("8.3 Re-synthesis")
T.numbered([
    "Ripple: lowered from 0.1 dB (RL 16.4 dB) to 0.03 dB (RL 21.6 dB), so that 20 dB can be met with margin.",
    "Ripple band: widened slightly to 9.72–10.28 GHz to leave room for tolerances.",
    "Post diameters: obtained by interpolating the extracted K(d) curve instead of reading a chart.",
    "Spacings: from Eqs. (3.9)–(3.10) with the extracted phases φ(d).",
    "Centring: a short automatic loop re-scales the spacings by λg(10 GHz)/λg(fc) until the response is centred at "
    "10.00 GHz; it converged in two full-wave runs."])
T.p("Three variants were synthesised to study the trade-off between ripple and order (Table 8.2).")
fmt = lambda xs: ", ".join(f"{x:.4f}" for x in xs)
T.table(["Design", "Order / ripple", "Post diameters (mm)", "Spacings (mm)", "Runs"], [
    ["Improved A", "3 / 0.02 dB", fmt(V2["final"]["d"]), fmt(V2["final"]["L"]), str(len(V2["history"]))],
    ["Improved B", "3 / 0.03 dB", fmt(V3["final"]["d"]), fmt(V3["final"]["L"]), str(len(V3["history"]))],
    ["Improved C (final)", "4 / 0.03 dB", fmt(V4["final"]["d"]), fmt(V4["final"]["L"]), str(len(V4["history"]))]],
    "Improved designs (symmetric; the 4th-order filter has five posts d1-d2-d3-d2-d1 and spacings L1-L2-L2-L1)", font=9)
T.fig(os.path.join(PL, "geom_improved_post4.png"), "openEMS model of the improved 4th-order post filter. It fits in the paper's 59.4 mm SIW.")
T.h2("8.4 Results")
T.fig(os.path.join(PL, "improved_vs_paper.png"), "Paper design vs. improved designs, all simulated under identical conditions. Green: specification (RL ≥ 20 dB from 9.75 to 10.25 GHz).", 15.5)
T.fig(os.path.join(PL, "improved_vs_paper_IL_zoom.png"), "Insertion loss across the specified band", 12.5)

def row(lab, m):
    return [lab, f2(m["RL_min_band"]), f2(m["IL_max_band"]), f2(m["IL_f0"]), f"{m['RL20_lo_GHz']:.2f}–{m['RL20_hi_GHz']:.2f}",
            f"{m['BW3dB_MHz']:.0f}", f"{m['rej_9GHz']:.1f}", f"{m['rej_11GHz']:.1f}"]
T.table(["Design", "worst RL in band (dB)", "worst IL in band (dB)", "IL @10 GHz (dB)", "RL ≥ 20 dB band (GHz)",
         "3 dB BW (MHz)", "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"],
        [["Paper, own Table 3 (CST)", "10.7", "1.33", "0.78", "n/a", "n/a", "n/a", "n/a"],
         row("Paper design (openEMS)", mp), row("Improved A, 3rd, 0.02 dB", m2), row("Improved B, 3rd, 0.03 dB", m3),
         row("Improved C, 4th, 0.03 dB", m4)],
        "Improvement summary (all openEMS rows use identical models)", font=8)
T.h2("8.5 Why a fourth resonator")
T.p("Variants A and B show that the corrected post sizes and the lower ripple alone fix the match: both 3rd-order "
    f"designs reach RL ≥ {min(m2['RL_min_band'], m3['RL_min_band']):.1f} dB across the band with an even lower IL. "
    "But to obtain such a deep match with only three resonators, the ripple band must be wide and the skirts become "
    f"gentle: the 3 dB bandwidth grows to {m3['BW3dB_MHz']:.0f}–{m2['BW3dB_MHz']:.0f} MHz and the rejection at 11 GHz "
    f"falls to {m2['rej_11GHz']:.0f}–{m3['rej_11GHz']:.0f} dB. A fourth resonator adds one more reflection zero, so "
    "the same match is obtained with much steeper skirts. Improved C keeps RL ≥ "
    f"{m4['RL_min_band']:.1f} dB and raises the rejection to {m4['rej_9GHz']:.0f} dB at 9 GHz and "
    f"{m4['rej_11GHz']:.0f} dB at 11 GHz. The cost is about 0.25 dB more mid-band loss ({m4['IL_f0']:.2f} dB), which "
    "is acceptable. A 5th order would add more loss (about 1.1 dB, Chapter 6) with no need for more selectivity, so "
    "the 4th order is the best balance.")
T.h2("8.6 Selected design")
T.bullets([
    f"Matching: RL ≥ {m4['RL_min_band']:.1f} dB over the whole specified band (paper: 10.7 dB in its own table, "
    f"{mp['RL_min_band']:.1f} dB in openEMS).",
    f"Loss: worst in-band IL {m4['IL_max_band']:.2f} dB (paper: 1.33 dB in its table, {mp['IL_max_band']:.2f} dB in openEMS).",
    f"Selectivity: {m4['rej_9GHz']:.0f}/{m4['rej_11GHz']:.0f} dB at 9/11 GHz (paper design: "
    f"{mp['rej_9GHz']:.0f}/{mp['rej_11GHz']:.0f} dB).",
    "Size and process: five posts in the same 59.4 mm SIW on the same 96.4 mm × 20 mm board, with the same "
    "plated-via process."])

# ================================================================== CHAPTER 9 board
T.chapter("Transition and Complete Board")
T.h2("9.1 Taper design")
T.p("The paper connects 50 Ω SMA connectors to the SIW through tapered microstrip lines but does not give the taper "
    "dimensions. The 50 Ω strip width on RT/Duroid 5870 with h = 1.57 mm is 4.66 mm (Hammerstad). The length "
    "available on each side follows from the board length: (96.4 − 59.421)/2 = 18.49 mm, split into a 5 mm feed "
    "line and a 13.49 mm linear taper. The taper width at the SIW was swept in a back-to-back model (two "
    "transitions joined by a plain SIW).")
tr = FB["transition"]
T.table(["Taper width at SIW (mm)", "max |S11|, 9–11 GHz (dB)", "IL @10 GHz, back-to-back (dB)"],
        [[f"{float(w):.1f}", f2(v["S11_max_9_11"]), f2(v["IL_10GHz"])] for w, v in tr["sweep"].items()],
        "Back-to-back transition sweep (taper length 13.49 mm)", widths=[5, 5.5, 5])
best = tr["sweep"][str(tr["best_w_taper"])]
T.p(f"The best width is {tr['best_w_taper']} mm, which keeps |S11| below {best['S11_max_9_11']:.1f} dB from 9 to "
    f"11 GHz with a back-to-back loss of {best['IL_10GHz']:.2f} dB at 10 GHz.")
T.fig(os.path.join(PL, "transition_sweep.png"), "Return loss of the back-to-back microstrip–SIW transition for several taper widths", 13)
T.h2("9.2 Complete boards")
T.fig(os.path.join(PL, "geom_full_board_improved.png"), "Complete 96.4 mm × 20 mm board with the improved 4th-order filter")
T.fig(os.path.join(PL, "full_board_comparison.png"), "Complete boards with 50 Ω microstrip ports: paper design vs. improved design", 14)
T.table(["Complete board", "worst RL in band (dB)", "worst IL in band (dB)", "IL @10 GHz (dB)", "3 dB BW (MHz)",
         "Rej. 9 GHz (dB)", "Rej. 11 GHz (dB)"],
        [["Paper filter + taper", f2(bp["RL_min_band"]), f2(bp["IL_max_band"]), f2(bp["IL_f0"]), f"{bp['BW3dB_MHz']:.0f}", f"{bp['rej_9GHz']:.1f}", f"{bp['rej_11GHz']:.1f}"],
         ["Improved filter + taper", f2(bi["RL_min_band"]), f2(bi["IL_max_band"]), f2(bi["IL_f0"]), f"{bi['BW3dB_MHz']:.0f}", f"{bi['rej_9GHz']:.1f}", f"{bi['rej_11GHz']:.1f}"]],
        "Complete-board results (openEMS, 50 Ω microstrip reference)", font=9)
T.p(f"With the transitions included, the improved board keeps IL ≤ {bi['IL_max_band']:.2f} dB and RL ≥ "
    f"{bi['RL_min_band']:.1f} dB across 9.75–10.25 GHz, against {bp['IL_max_band']:.2f} dB and {bp['RL_min_band']:.1f} dB "
    "for the paper's filter on the same board. The RL of the improved board drops below 20 dB near the upper band "
    "edge because the reflections of the two tapers (about −21 dB each) add to that of the filter. Re-tuning the "
    "outer posts together with the taper, or using a longer taper, would recover the margin.")
T.h2("9.3 Accuracy of the board model")
T.p("The microstrip-port model uses a perfectly conducting ground plane with an equivalent loss, and its port "
    "calibration has an error of about ±0.3 dB (out of band |S11| reaches +0.3 dB). Its absolute IL is therefore "
    "less accurate than that of the waveguide-port models. The comparison between the two boards is still fair, "
    "because both use exactly the same model.")

# ================================================================== CHAPTER 10
T.chapter("Conclusions and Future Work")
T.h2("10.1 Conclusions")
T.numbered([
    "openEMS, a free full-wave FDTD solver, was learned and used to build, mesh, excite and post-process SIW "
    "structures entirely from Python scripts.",
    "The SIW model was verified on a plain line (|S11| < −40 dB, loss 3.0 dB/m against 3.05 dB/m from theory) and "
    "by a mesh-convergence test (0.1 % change in f0).",
    f"All seven published filters were reproduced without tuning: {n_tol}/{n_all} tabulated values "
    f"({100*n_tol/n_all:.0f} %) agree within ±0.5 % in frequency and {n_strict}/{n_all} at exactly the same "
    "frequency. Every centre frequency, bandwidth, order and qualitative conclusion of the paper is confirmed.",
    "The 0.2 dB insertion loss reported for the 5th-order filters is physically implausible; theory gives 1.05 dB "
    "and openEMS about 1.1 dB.",
    "The parametric study confirmed the design rules: resonator length and permittivity set the centre frequency, "
    "coupling size sets the bandwidth, the order sets the selectivity and the losses set the insertion loss.",
    "The weak band-edge match of the published post filter was traced to the 0.1 dB ripple and to chart-read post "
    "sizes whose couplings are 4–6 % too strong.",
    f"A 4th-order filter synthesised from full-wave inverter data meets RL ≥ {m4['RL_min_band']:.1f} dB and "
    f"IL ≤ {m4['IL_max_band']:.2f} dB over 9.75–10.25 GHz with better rejection "
    f"({m4['rej_9GHz']:.0f}/{m4['rej_11GHz']:.0f} dB at 9/11 GHz) in the same 59.4 mm SIW.",
    f"A 50 Ω taper was designed and the complete board simulated: IL ≤ {bi['IL_max_band']:.2f} dB and RL ≥ "
    f"{bi['RL_min_band']:.1f} dB for the improved board, against {bp['IL_max_band']:.2f} dB and "
    f"{bp['RL_min_band']:.1f} dB for the published design."])
T.h2("10.2 Limitations")
T.bullets([
    "All results are simulations; no board was fabricated or measured.",
    "Connector and cable losses, surface roughness and manufacturing tolerances are not included.",
    "The improved board's RL dips to about 17.7 dB at the upper band edge because of the tapers."])
T.h2("10.3 Future work")
T.bullets([
    "Fabricate the improved board and measure it with a VNA after TRL calibration, to separate connector loss from "
    "filter loss.",
    "Tune the outer posts together with the taper to recover RL ≥ 20 dB on the complete board.",
    "Run a Monte-Carlo tolerance analysis of post diameter, post position and substrate permittivity.",
    "Add cross-coupled cavities to create transmission zeros and further improve the selectivity."])

# ================================================================== references
T.page_break()
T.doc.add_heading("References", level=1)
REFS = [
    "H. Bandar and N. Türker Tokan, “Comparison of post and iris substrate integrated waveguide band-pass filters for X-band applications,” Sigma J. Eng. Nat. Sci., vol. 40, no. 1, pp. 45–56, 2022, doi: 10.14744/sigma.2022.00004.",
    "D. M. Pozar, Microwave Engineering, 4th ed. Hoboken, NJ, USA: Wiley, 2011.",
    "G. L. Matthaei, L. Young, and E. M. T. Jones, Microwave Filters, Impedance-Matching Networks, and Coupling Structures. Dedham, MA, USA: Artech House, 1980.",
    "D. Deslandes and K. Wu, “Integrated microstrip and rectangular waveguide in planar form,” IEEE Microw. Wireless Compon. Lett., vol. 11, no. 2, pp. 68–70, Feb. 2001.",
    "D. Deslandes and K. Wu, “Single-substrate integration technique of planar circuits and waveguide filters,” IEEE Trans. Microw. Theory Techn., vol. 51, no. 2, pp. 593–596, Feb. 2003.",
    "Y. Cassivi, L. Perregrini, P. Arcioni, M. Bressan, K. Wu, and G. Conciauro, “Dispersion characteristics of substrate integrated rectangular waveguide,” IEEE Microw. Wireless Compon. Lett., vol. 12, no. 9, pp. 333–335, Sep. 2002.",
    "F. Xu and K. Wu, “Guided-wave and leakage characteristics of substrate integrated waveguide,” IEEE Trans. Microw. Theory Techn., vol. 53, no. 1, pp. 66–73, Jan. 2005.",
    "D. Deslandes and K. Wu, “Accurate modeling, wave mechanisms, and design considerations of a substrate integrated waveguide,” IEEE Trans. Microw. Theory Techn., vol. 54, no. 6, pp. 2516–2526, Jun. 2006.",
    "N. Marcuvitz, Waveguide Handbook. New York, NY, USA: McGraw-Hill, 1951.",
    "J.-S. Hong and M. J. Lancaster, Microstrip Filters for RF/Microwave Applications. New York, NY, USA: Wiley, 2001.",
    "R. J. Cameron, C. M. Kudsia, and R. R. Mansour, Microwave Filters for Communication Systems. Hoboken, NJ, USA: Wiley, 2007.",
    "T. Liebig, A. Rennings, S. Held, and D. Erni, “openEMS – a free and open source equivalent-circuit (EC) FDTD simulation platform supporting cylindrical coordinates suitable for the analysis of traveling wave MRI applications,” Int. J. Numer. Model., vol. 26, no. 6, pp. 680–696, 2013.",
    "S. B. Cohn, “Dissipation loss in multiple-coupled-resonator filters,” Proc. IRE, vol. 47, no. 8, pp. 1342–1348, Aug. 1959.",
    "M. Bozzi, A. Georgiadis, and K. Wu, “Review of substrate-integrated waveguide circuits and antennas,” IET Microw. Antennas Propag., vol. 5, no. 8, pp. 909–920, 2011.",
    "X.-P. Chen and K. Wu, “Substrate integrated waveguide filters: Design techniques and structure innovations,” IEEE Microw. Mag., vol. 15, no. 6, pp. 121–133, Sep. 2014.",
    "D. Deslandes, “Design equations for tapered microstrip-to-substrate integrated waveguide transitions,” in IEEE MTT-S Int. Microw. Symp. Dig., 2010, pp. 704–707.",
    "K. S. Yee, “Numerical solution of initial boundary value problems involving Maxwell's equations in isotropic media,” IEEE Trans. Antennas Propag., vol. 14, no. 3, pp. 302–307, May 1966.",
    "A. Taflove and S. C. Hagness, Computational Electrodynamics: The Finite-Difference Time-Domain Method, 3rd ed. Norwood, MA, USA: Artech House, 2005.",
    "J. Uher, J. Bornemann, and U. Rosenberg, Waveguide Components for Antenna Feed Systems: Theory and CAD. Norwood, MA, USA: Artech House, 1993.",
    "E. O. Hammerstad, “Equations for microstrip circuit design,” in Proc. 5th Eur. Microw. Conf., 1975, pp. 268–272.",
    "J.-P. Berenger, “A perfectly matched layer for the absorption of electromagnetic waves,” J. Comput. Phys., vol. 114, no. 2, pp. 185–200, 1994.",
    "G. Mur, “Absorbing boundary conditions for the finite-difference approximation of the time-domain electromagnetic-field equations,” IEEE Trans. Electromagn. Compat., vol. EMC-23, no. 4, pp. 377–382, Nov. 1981."]
for i, ref in enumerate(REFS, 1):
    par = T.p(f"[{i}]  {ref}", align="left", size=11, after=4)
    par.paragraph_format.line_spacing = 1.15
    par.paragraph_format.left_indent = Cm(0.9); par.paragraph_format.first_line_indent = Cm(-0.9)

# ================================================================== appendices
T.page_break(); T.ch = "A"; T.nfig = T.ntab = 0
T.doc.add_heading("Appendix A – Output of the Design Script", level=1)
T.p("Output of 02_Design_Calculations/siw_design_calc.py (analytical design of Chapter 4):")
T.mono(calc_txt)
T.page_break(); T.ch = "B"; T.nfig = T.ntab = 0
T.doc.add_heading("Appendix B – Reproducing the Results", level=1)
T.p("All results can be reproduced with free software on Windows. Inside the folder 03_openEMS_Simulation, open "
    "PowerShell and set the openEMS Python once:")
T.mono('$py = "<openEMS install folder>\\py313\\tools\\python.exe"', 10)
T.p("Then run:")
T.table(["Command", "What it does", "Time"], [
    ["& $py run_all.py", "Re-runs every simulation and rebuilds all plots, tables and documents", "≈ 1 h"],
    ["& $py demo_live.py", "One run of the paper's 3rd-order iris filter", "≈ 1 min"],
    ["& $py demo_live.py improved", "One run of the improved 4th-order filter", "≈ 2 min"],
    ["& $py demo_live.py improved --view", "Opens the 3-D model in AppCSXCAD (no simulation)", "5 s"],
    ["& $py demo_live.py iris3_cheby --L=11.6,12.6", "Parameter change: resonator lengths (mm)", "≈ 1 min"],
    ["& $py demo_live.py iris3_cheby --d=7.0,4.6", "Parameter change: iris windows / post diameters (mm)", "≈ 1 min"],
    ["& $py demo_live.py iris3_cheby --er=2.2", "Parameter change: substrate permittivity", "≈ 1 min"],
    ["& $py demo_live.py iris3_cheby --lossless", "All losses switched off", "≈ 1 min"],
    ["& $py demo_live.py iris5_cheby", "Any published design by name (here 5th order)", "≈ 2 min"]],
    "Commands to reproduce the results", widths=[6.3, 7.2, 2], font=9)
T.page_break(); T.ch = "C"; T.nfig = T.ntab = 0
T.doc.add_heading("Appendix C – Project Files", level=1)
T.table(["Folder / file", "Content"], [
    ["01_Base_Paper/", "Base paper [1] (PDF)"], ["02_Design_Calculations/", "Analytical design script and its output"],
    ["03_openEMS_Simulation/", "openEMS model library and all simulation scripts"],
    ["04_Results/plots, tables, touchstone", "All figures, result tables (JSON/Markdown) and .s2p files"],
    ["05_Report/", "Course-project report and its generator"], ["06_Presentation/", "Slides and presentation script"],
    ["07_Thesis/", "This thesis and its generator"], ["08_Research_Paper/", "IEEE-format research paper (LaTeX source and PDF)"]],
    "Project files", widths=[6.5, 9], font=10)

out = os.path.join(HERE, "SIW_Filter_Xband_Thesis.docx")
T.save(out)
print("saved", out)

# ------------------------------------------------------------------ fill the TOC fields and export a PDF with Word
pdf = out[:-5] + ".pdf"
ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; $d = $w.Documents.Open('{out}'); "
      "foreach ($t in $d.TablesOfContents) { $t.Update() }; $d.Fields.Update() | Out-Null; "
      "foreach ($t in $d.TablesOfContents) { $t.Update() }; $d.Save(); "
      f"$d.ExportAsFixedFormat('{pdf}', 17); $d.Close(); try {{ $w.Quit() }} catch {{}}")
r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
print("pdf:", os.path.exists(pdf), r.stderr.strip()[:500])
