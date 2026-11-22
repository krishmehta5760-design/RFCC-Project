"""Turns ../PRESENTATION_GUIDE.md into a Word file (PRESENTATION_GUIDE.docx) with the plots embedded.
Every line that starts with "Show" gets the .png files it names inserted below it."""
import os, re
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.join(ROOT, "PRESENTATION_GUIDE.md")
OUT = os.path.join(HERE, "PRESENTATION_GUIDE.docx")
PLOTS = os.path.join(ROOT, "04_Results", "plots")

doc = Document()
st = doc.styles["Normal"]; st.font.name = "Calibri"; st.font.size = Pt(11)
for s in doc.sections:
    s.left_margin = s.right_margin = Cm(2.0); s.top_margin = s.bottom_margin = Cm(2.0)

INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|(?<![\w*])\*[^*\s][^*]*?\*(?![\w*]))")


def add_runs(par, text):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            add_runs_bold(par, part[2:-2])
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1]); r.font.name = "Consolas"; r.font.size = Pt(10)
            r.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            par.add_run(part[1:-1]).italic = True
        else:
            par.add_run(part)


def add_runs_bold(par, text):
    start = len(par.runs)
    add_runs(par, text)
    for r in par.runs[start:]:
        r.bold = True


def add_table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    ncol = max(len(r) for r in cells)
    t = doc.add_table(rows=len(cells), cols=ncol)
    t.style = "Light Grid Accent 1"
    for i, r in enumerate(cells):
        for j in range(ncol):
            p = t.cell(i, j).paragraphs[0]
            add_runs(p, r[j] if j < len(r) else "")
            for run in p.runs:
                run.font.size = Pt(9.5)
                if i == 0:
                    run.bold = True
    doc.add_paragraph()


def add_figures(text):
    for name in re.findall(r"`([\w.\-]+\.png)`", text):
        fn = os.path.join(PLOTS, name)
        if os.path.exists(fn):
            doc.add_picture(fn, width=Cm(16.5))
            doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap = doc.add_paragraph(name); cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap.runs[0].italic = True; cap.runs[0].font.size = Pt(9)


lines = open(SRC, encoding="utf-8").read().splitlines()
i = 0
while i < len(lines):
    ln = lines[i]
    s = ln.strip()
    if s.startswith("```"):                       # code block
        i += 1; code = []
        while i < len(lines) and not lines[i].strip().startswith("```"):
            code.append(lines[i]); i += 1
        p = doc.add_paragraph()
        r = p.add_run("\n".join(code)); r.font.name = "Consolas"; r.font.size = Pt(9.5)
        p.paragraph_format.left_indent = Cm(0.8)
        i += 1; continue
    if s.startswith("|"):                          # table
        rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            rows.append(lines[i]); i += 1
        add_table(rows); continue
    if s == "---" or not s.lstrip(">").strip():
        i += 1; continue
    m = re.match(r"^(#{1,3})\s+(.*)", s)
    if m:
        lvl = len(m.group(1))
        if lvl == 1:
            h = doc.add_heading(m.group(2), 0)
        else:
            h = doc.add_heading(m.group(2), lvl - 1)
        i += 1; continue
    indent = len(ln) - len(ln.lstrip())
    if re.match(r"^[*-]\s+", s):                   # bullet
        p = doc.add_paragraph(style="List Bullet" if indent < 2 else "List Bullet 2")
        add_runs(p, re.sub(r"^[*-]\s+", "", s))
    elif re.match(r"^\d+\.\s+", s):                # numbered item (keep the number as text)
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6 + 0.6*(indent >= 2))
        add_runs(p, s)
    elif s.startswith(">"):                        # quote / formula
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(1.0)
        add_runs(p, s.lstrip("> ").strip())
        for r in p.runs:
            r.italic = True
    else:
        p = doc.add_paragraph(); add_runs(p, s)
    if re.sub(r"^[*-]\s+", "", s).startswith(("Show ", "Look at ")):
        add_figures(s)
    i += 1

from docx_helpers import save_docx
save_docx(doc, OUT)
print("saved", OUT)
