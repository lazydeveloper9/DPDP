import sys
from pathlib import Path
try:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument("cs01-reports/cs01-report.pdf")
    print("Total pages in cs01-reports/cs01-report.pdf:", len(pdf))
    for i in range(min(4, len(pdf))):
        page = pdf[i]
        image = page.render(scale=1.5).to_pil()
        out_p = f"cs01-reports/current_pdf_page_{i}.png"
        image.save(out_p)
        print(f"Rendered {out_p}")
except Exception as e:
    print("pypdfium2 failed or not installed:", e)
    # Try PySide6.QtPdf
    try:
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtPdf import QPdfDocument
        doc = QPdfDocument()
        err = doc.load("cs01-reports/cs01-report.pdf")
        print("QPdfDocument load status:", err, "pages:", doc.pageCount())
        from PySide6.QtCore import QSize
        for i in range(min(4, doc.pageCount())):
            size = doc.pagePointSize(i)
            img = doc.render(i, QSize(int(size.width() * 2), int(size.height() * 2)))
            out_p = f"cs01-reports/current_pdf_page_{i}.png"
            img.save(out_p)
            print(f"Rendered with QtPdf {out_p}")
    except Exception as e2:
        print("QtPdf failed:", e2)
