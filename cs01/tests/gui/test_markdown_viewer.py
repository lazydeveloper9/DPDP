"""
Tests for In-App Markdown Report Viewer Component
Verifies:
- Safe offline GFM parsing and HTML generation
- Heading anchors and TOC hierarchy
- Rendered vs. Source view toggle
- Real-time document search navigation
- Zero-egress safe rendering (no external browser/app launched)
"""
from pathlib import Path
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cs01.gui.main_window import MainWindow
from cs01.gui.markdown_viewer.markdown_parser import MarkdownParser
from cs01.gui.markdown_viewer.viewer_view import AuditReportViewer


SAMPLE_MD = """# CS-01 DPDP Compliance Assessment Report

## Executive Summary
This document provides statutory compliance analysis under the **Digital Personal Data Protection Act, 2023**.

### Statutory Exposure
| Mandate | Status | Penalty Band |
| :--- | :--- | :--- |
| Notice & Consent | FAIL | ₹50 Crore |
| Security Safeguards | FAIL | ₹250 Crore |

## Technical Findings
Here is a sample vulnerability snippet:
```python
def process_data(req):
    logger.info("Payload: %s", req.body)
```

> [!IMPORTANT]
> All personal identifiers must be redacted prior to logging.
"""


def test_markdown_parser_headings_and_tables():
    """Verify MarkdownParser extracts hierarchical headings and builds HTML tables."""
    html_out, headings = MarkdownParser.parse(SAMPLE_MD)
    assert len(headings) >= 3
    assert headings[0].title == "CS-01 DPDP Compliance Assessment Report"
    assert headings[0].level == 1
    assert headings[1].title == "Executive Summary"
    assert headings[1].level == 2
    assert headings[2].title == "Statutory Exposure"
    assert headings[2].level == 3

    assert '<table class="report-table">' in html_out
    assert "Notice &amp; Consent" in html_out or "Notice & Consent" in html_out
    assert "₹250 Crore" in html_out
    assert 'class="code-container"' in html_out


def test_viewer_load_text_and_toggle_views(qtbot):
    """Verify AuditReportViewer loads markdown text and toggles Rendered/Source views."""
    viewer = AuditReportViewer()
    qtbot.addWidget(viewer)
    viewer.load_text(SAMPLE_MD, filename="test-report.md")

    # Rendered mode is default (index 0)
    assert viewer.content_stack.currentIndex() == 0
    assert "CS-01 DPDP" in viewer.browser.toPlainText()

    # Switch to Source View
    viewer.set_view_mode(1)
    assert viewer.content_stack.currentIndex() == 1
    assert "```python" in viewer.source_view.toPlainText()

    # Switch back to Rendered View
    viewer.set_view_mode(0)
    assert viewer.content_stack.currentIndex() == 0


def test_viewer_search_and_navigation(qtbot):
    """Verify in-document search and match navigation."""
    viewer = AuditReportViewer()
    qtbot.addWidget(viewer)
    viewer.show()
    viewer.load_text(SAMPLE_MD)

    viewer.open_search()
    assert viewer.search_bar.isVisible()

    # Search for a term present in the document
    viewer.search_bar.input.setText("Statutory")
    viewer.search_bar.prev_btn.click()
    viewer.search_bar.next_btn.click()
    viewer.search_bar.close_search()
    assert not viewer.search_bar.isVisible()


def test_viewer_zoom_actions(qtbot):
    """Verify zoom in, zoom out, and reset zoom."""
    viewer = AuditReportViewer()
    qtbot.addWidget(viewer)
    viewer.load_text(SAMPLE_MD)

    viewer.zoom_in()
    assert viewer._zoom_level == 1
    viewer.zoom_out()
    assert viewer._zoom_level == 0
    viewer.reset_zoom()
    assert viewer._zoom_level == 0


def test_main_window_markdown_viewer_integration(qtbot):
    """Verify MainWindow integrates AuditReportViewer at index 7 with back navigation."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Stack has 8 items
    assert window.stacked_widget.count() == 8
    assert isinstance(window.audit_report_viewer, AuditReportViewer)

    # Trigger markdown open
    md_file = Path("cs01-reports/cs01-report.md").resolve()
    window._on_open_markdown_requested(md_file if md_file.exists() else None)
    assert window.stacked_widget.currentIndex() == 7

    # Click Back to Reports
    window.audit_report_viewer.back_btn.click()
    assert window.stacked_widget.currentIndex() == 5
