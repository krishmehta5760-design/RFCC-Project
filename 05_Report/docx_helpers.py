"""Small helpers around python-docx used by make_report.py"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


class Report:
    def __init__(self):
        self.doc = Document()
        st = self.doc.styles["Normal"]
        st.font.name = "Times New Roman"; st.font.size = Pt(12)
        st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
        for s in self.doc.sections:
            s.left_margin = s.right_margin = Cm(2.2); s.top_margin = s.bottom_margin = Cm(2.0)
        self.fig_no = 0; self.tab_no = 0

    def title(self, text, size=20, bold=True, space=6):
        p = self.doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(text); r.bold = bold; r.font.size = Pt(size)
        p.paragraph_format.space_after = Pt(space)
        return p

    def h(self, text, level=1):
        hd = self.doc.add_heading(text, level=level)
        for r in hd.runs:
            r.font.name = "Times New Roman"; r.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        return hd

    def p(self, text, bold_prefix=None, italic=False, align="justify", size=None):
        para = self.doc.add_paragraph()
        if bold_prefix:
            rb = para.add_run(bold_prefix); rb.bold = True
        r = para.add_run(text); r.italic = italic
        if size: r.font.size = Pt(size)
        if align == "justify": para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        elif align == "center": para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.space_after = Pt(6)
        return para

    def bullets(self, items):
        for it in items:
            para = self.doc.add_paragraph(style="List Bullet")
            if isinstance(it, tuple):
                rb = para.add_run(it[0]); rb.bold = True; para.add_run(it[1])
            else:
                para.add_run(it)

    def eq(self, text):
        para = self.doc.add_paragraph(); para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = para.add_run(text); r.italic = True; r.font.name = "Cambria Math"

    def table(self, header, rows, caption, widths=None, font=10):
        self.tab_no += 1
        cp = self.doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc = cp.add_run(f"Table {self.tab_no}. {caption}"); rc.bold = True; rc.font.size = Pt(10)
        t = self.doc.add_table(rows=1, cols=len(header)); t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for i, hcell in enumerate(header):
            c = t.rows[0].cells[i]; c.text = ""
            r = c.paragraphs[0].add_run(str(hcell)); r.bold = True; r.font.size = Pt(font)
            shd = OxmlElement("w:shd"); shd.set(qn("w:val"), "clear"); shd.set(qn("w:fill"), "D9E2F3")
            c._tc.get_or_add_tcPr().append(shd)
        for row in rows:
            cells = t.add_row().cells
            for i, v in enumerate(row):
                cells[i].text = ""
                r = cells[i].paragraphs[0].add_run(str(v)); r.font.size = Pt(font)
        if widths:
            for row in t.rows:
                for i, w in enumerate(widths):
                    row.cells[i].width = Cm(w)
        self.doc.add_paragraph()
        return self.tab_no

    def fig(self, path, caption, width_cm=15.5):
        if not os.path.exists(path):
            self.p(f"[missing figure: {os.path.basename(path)}]", italic=True); return None
        self.fig_no += 1
        self.doc.add_picture(path, width=Cm(width_cm))
        self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp = self.doc.add_paragraph(); cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        rc = cp.add_run(f"Figure {self.fig_no}. {caption}"); rc.italic = True; rc.font.size = Pt(10)
        return self.fig_no

    def page_break(self):
        self.doc.add_page_break()

    def save(self, fn):
        self.doc.save(fn)


def docx_to_doc(docx_path, doc_path):
    """Convert .docx -> Word 97-2003 .doc using the installed MS Word (COM)."""
    import subprocess
    ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"$d = $w.Documents.Open('{docx_path}'); $d.SaveAs2('{doc_path}', 0); $d.Close(); try {{ $w.Quit() }} catch {{}}")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=False)
