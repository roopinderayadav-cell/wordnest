"""Wordnest - PDF helpers: page images for the reader, text view, buyer watermark, demo PDFs."""
import io

import streamlit as st
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A5
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import wn_db


def page_count(pdf_bytes):
    try:
        return len(PdfReader(io.BytesIO(pdf_bytes)).pages)
    except Exception:
        return 0


@st.cache_data(max_entries=300, show_spinner=False)
def render_page(book_id, stamp, page_no, scale=1.6):
    """Render one PDF page to PNG (keeps the exact layout, works for Hindi too)."""
    import pypdfium2 as pdfium
    pdf_bytes = wn_db.get_book_pdf(book_id)
    if not pdf_bytes:
        return None
    doc = pdfium.PdfDocument(pdf_bytes)
    try:
        page = doc[page_no]
        img = page.render(scale=scale).to_pil()
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()
    finally:
        doc.close()


@st.cache_data(max_entries=300, show_spinner=False)
def page_text(book_id, stamp, page_no):
    pdf_bytes = wn_db.get_book_pdf(book_id)
    if not pdf_bytes:
        return ""
    try:
        return PdfReader(io.BytesIO(pdf_bytes)).pages[page_no].extract_text() or ""
    except Exception:
        return ""


def first_pages_text(pdf_bytes, pages=15):
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        return "\n".join((p.extract_text() or "") for p in reader.pages[:pages])
    except Exception:
        return ""


def watermark(pdf_bytes, text):
    """Stamp the buyer's details on the footer of every page (discourages sharing)."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    overlays = {}
    for page in reader.pages:
        w = float(page.mediabox.width)
        h = float(page.mediabox.height)
        key = (round(w), round(h))
        if key not in overlays:
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=(w, h))
            c.setFont("Helvetica", 6.5)
            c.setFillGray(0.45)
            c.drawCentredString(w / 2, 10, text)
            c.save()
            buf.seek(0)
            overlays[key] = PdfReader(buf).pages[0]
        page.merge_page(overlays[key])
        writer.add_page(page)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def demo_book_pdf(title, author, color_hex, chapters=8, pages_per_chapter=3):
    """A clearly labelled placeholder book so the reader and downloads can be tried before real manuscripts are uploaded."""
    buf = io.BytesIO()
    W, H = A5
    c = canvas.Canvas(buf, pagesize=A5)
    c.setTitle(title)
    c.setAuthor(author)
    # cover
    c.setFillColor(color_hex)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColor("#FFFFFF")
    c.setFont("Times-Bold", 26)
    y = H - 60 * mm
    for line in _wrap(title, 18):
        c.drawCentredString(W / 2, y, line)
        y -= 30
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(W / 2, 22 * mm, author.upper())
    c.showPage()
    body = ("This page is placeholder text for the Wordnest demo. It shows how the online reader, "
            "chapter navigation, free sample pages and the watermarked PDF download work. "
            "Upload the real manuscript PDF from the Admin panel to replace this demo book.")
    for ch in range(1, chapters + 1):
        for p in range(pages_per_chapter):
            c.setFillColor("#1C2321")
            if p == 0:
                c.setFont("Helvetica-Bold", 9)
                c.setFillColor(color_hex)
                c.drawString(18 * mm, H - 30 * mm, f"CHAPTER {ch}")
                c.setFillColor("#1C2321")
                c.setFont("Times-Bold", 20)
                c.drawString(18 * mm, H - 42 * mm, f"Chapter {ch} title")
                y = H - 58 * mm
            else:
                y = H - 25 * mm
            c.setFont("Times-Roman", 11.5)
            for _ in range(3 if p == 0 else 4):
                for line in _wrap(body, 62):
                    c.drawString(18 * mm, y, line)
                    y -= 16
                y -= 10
            c.setFont("Helvetica", 8)
            c.setFillColor("#5F6A66")
            c.drawCentredString(W / 2, 12 * mm, f"{title}  ·  page {c.getPageNumber()}")
            c.showPage()
    c.save()
    return buf.getvalue()


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return lines
