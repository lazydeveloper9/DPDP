"""
CS-01 DPDP Compliance Desktop GUI - Audit Report Viewer View.

Provides the complete in-app Markdown report reading experience:
- Top Toolbar: Back navigation, title & stats, Rendered/Source toggle, Zoom, Copy, Search, PDF Export
- Collapsible Left Table of Contents tree with section jump anchors
- Central QSplitter hosting formatted Neo-Brutalist HTML rendered view and raw source view
- In-document search with match navigation
- Synchronized theme engine integration
"""
from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor, QTextDocument
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.markdown_viewer.markdown_parser import HeadingItem, MarkdownParser
from cs01.gui.markdown_viewer.search_widget import MarkdownSearchBar
from cs01.gui.markdown_viewer.source_view import MarkdownSourceView
from cs01.gui.markdown_viewer.toc_widget import TableOfContentsWidget
from cs01.gui.theme_engine.theme_manager import ThemeManager


class AuditReportViewer(QWidget):
    """
    Dedicated in-app Markdown Report Viewer.
    Mounted at index 7 in MainWindow's QStackedWidget.
    """

    back_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tm = ThemeManager.instance()
        self._current_path: Path | None = None
        self._raw_markdown: str = ""
        self._headings: list[HeadingItem] = []
        self._zoom_level: int = 0

        self._setup_ui()
        self._setup_shortcuts()

        # Connect to dynamic theme updates
        self.tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # 1. Top Navigation Toolbar
        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        # 2. Search Bar (hidden by default)
        self.search_bar = MarkdownSearchBar(self)
        self.search_bar.setVisible(False)
        self.search_bar.search_requested.connect(self._on_search_requested)
        self.search_bar.search_closed.connect(self._on_search_closed)
        layout.addWidget(self.search_bar)

        # 3. Main Central Splitter (Left TOC + Right Document View)
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)

        # Left TOC
        self.toc_widget = TableOfContentsWidget(self)
        self.toc_widget.heading_selected.connect(self._on_heading_selected)
        self.toc_widget.setMinimumWidth(180)
        self.splitter.addWidget(self.toc_widget)

        # Right Stacked Content (0 = Rendered, 1 = Source)
        self.content_stack = QStackedWidget(self)

        # 3A. Rendered View (QTextBrowser with full rich-text & anchor support)
        self.browser = QTextBrowser(self)
        self.browser.setOpenExternalLinks(False)
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self._on_anchor_clicked)
        self.browser.setStyleSheet(
            "QTextBrowser { background-color: #FFFFFF; border: 2px solid #111111; "
            "border-radius: 0px; padding: 12px; } "
            "QTextBrowser:focus { border: 2px solid #111111; }"
        )
        self.content_stack.addWidget(self.browser)

        # 3B. Source View (Raw markdown with line numbers)
        self.source_view = MarkdownSourceView(self)
        self.content_stack.addWidget(self.source_view)

        self.splitter.addWidget(self.content_stack)
        self.splitter.setSizes([260, 900])
        layout.addWidget(self.splitter, stretch=1)

    def _build_toolbar(self) -> QWidget:
        bar = QFrame(self)
        bar.setStyleSheet(
            "QFrame { background-color: #EAE6DA; border: 2px solid #111111; "
            "padding: 6px 10px; border-radius: 0px; }"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(8)

        # Back to Reports Button
        self.back_btn = QPushButton("← Back to Reports")
        self.back_btn.setProperty("class", "primary")
        self.back_btn.setStyleSheet(
            "QPushButton { background-color: #FFE500; color: #111111; font-weight: 800; "
            "border: 2px solid #111111; padding: 6px 14px; font-size: 9pt; } "
            "QPushButton:hover { background-color: #FFD400; }"
        )
        self.back_btn.clicked.connect(self.back_requested.emit)
        layout.addWidget(self.back_btn)

        # Document Title / Filename Label
        self.title_label = QLabel("NO REPORT LOADED")
        self.title_label.setStyleSheet(
            "font-size: 10pt; font-weight: 800; color: #111111; margin-left: 8px;"
        )
        layout.addWidget(self.title_label)

        # Stats Badge
        self.stats_badge = QLabel("")
        self.stats_badge.setStyleSheet(
            "font-size: 8pt; font-weight: 800; background-color: #FFF4C2; color: #111111; "
            "border: 1px solid #111111; padding: 2px 6px;"
        )
        layout.addWidget(self.stats_badge)

        layout.addStretch()

        # View Mode Toggle: Rendered vs Source
        self.rendered_btn = QPushButton("Rendered View")
        self.rendered_btn.setCheckable(True)
        self.rendered_btn.setChecked(True)
        self.rendered_btn.setStyleSheet(
            "QPushButton { background-color: #FFE500; color: #111111; font-weight: 800; "
            "border: 1.5px solid #111111; padding: 4px 10px; font-size: 8.5pt; } "
            "QPushButton:!checked { background-color: #FFFFFF; font-weight: 600; }"
        )
        self.rendered_btn.clicked.connect(lambda: self.set_view_mode(0))
        layout.addWidget(self.rendered_btn)

        self.source_btn = QPushButton("Source View")
        self.source_btn.setCheckable(True)
        self.source_btn.setStyleSheet(
            "QPushButton { background-color: #FFE500; color: #111111; font-weight: 800; "
            "border: 1.5px solid #111111; padding: 4px 10px; font-size: 8.5pt; } "
            "QPushButton:!checked { background-color: #FFFFFF; font-weight: 600; }"
        )
        self.source_btn.clicked.connect(lambda: self.set_view_mode(1))
        layout.addWidget(self.source_btn)

        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.rendered_btn, 0)
        self.mode_group.addButton(self.source_btn, 1)

        # Search Trigger Button
        self.search_btn = QPushButton("🔍 Find (Ctrl+F)")
        self.search_btn.setStyleSheet(
            "font-size: 8.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 1.5px solid #111111; padding: 4px 10px;"
        )
        self.search_btn.clicked.connect(self.toggle_search)
        layout.addWidget(self.search_btn)

        # Zoom Controls
        self.zoom_out_btn = QPushButton("-")
        self.zoom_out_btn.setFixedSize(26, 26)
        self.zoom_out_btn.setToolTip("Zoom Out (Ctrl+-)")
        self.zoom_out_btn.setStyleSheet("font-weight: 900; background: #FFFFFF; border: 1.5px solid #111111;")
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        layout.addWidget(self.zoom_out_btn)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("font-size: 8.5pt; font-weight: 700; color: #595959;")
        layout.addWidget(self.zoom_label)

        self.zoom_in_btn = QPushButton("+")
        self.zoom_in_btn.setFixedSize(26, 26)
        self.zoom_in_btn.setToolTip("Zoom In (Ctrl++)")
        self.zoom_in_btn.setStyleSheet("font-weight: 900; background: #FFFFFF; border: 1.5px solid #111111;")
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        layout.addWidget(self.zoom_in_btn)

        # Copy Document
        self.copy_btn = QPushButton("Copy Content")
        self.copy_btn.setStyleSheet(
            "font-size: 8.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 1.5px solid #111111; padding: 4px 10px;"
        )
        self.copy_btn.clicked.connect(self.copy_content)
        layout.addWidget(self.copy_btn)

        # Export PDF
        self.export_pdf_btn = QPushButton("Export PDF")
        self.export_pdf_btn.setStyleSheet(
            "font-size: 8.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 1.5px solid #111111; padding: 4px 10px;"
        )
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        layout.addWidget(self.export_pdf_btn)

        return bar

    def _setup_shortcuts(self) -> None:
        """Configures keyboard shortcuts."""
        # Ctrl+F to open search
        QShortcut(QKeySequence("Ctrl+F"), self, activated=self.open_search)
        # Escape to close search
        QShortcut(QKeySequence("Esc"), self, activated=self.search_bar.close_search)
        # Zoom shortcuts
        QShortcut(QKeySequence("Ctrl+="), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl++"), self, activated=self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, activated=self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, activated=self.reset_zoom)

    # -------------------------------------------------------------------------
    # Public Document Loading API
    # -------------------------------------------------------------------------

    def load_file(self, path: Path | str) -> bool:
        """
        Safely loads and renders a Markdown report file from disk.
        Handles BOM, UTF-8, and invalid paths with explicit feedback.
        """
        p = Path(path).resolve()
        if not p.exists() or not p.is_file():
            self._render_empty_state(f"Report file not found: {p}")
            return False

        if p.suffix.lower() not in (".md", ".markdown", ".mdown", ".txt"):
            self._render_empty_state(f"Unsupported report format: {p.suffix} (expected .md)")
            return False

        try:
            # Handle UTF-8 with BOM or standard UTF-8
            raw_bytes = p.read_bytes()
            if raw_bytes.startswith(b"\xef\xbb\xbf"):
                raw_text = raw_bytes[3:].decode("utf-8", errors="replace")
            else:
                raw_text = raw_bytes.decode("utf-8", errors="replace")

            self._current_path = p
            self.load_text(raw_text, filename=p.name, base_dir=p.parent)
            return True
        except Exception as e:
            self._render_empty_state(f"Failed to load Markdown file: {e}")
            return False

    def load_text(
        self, markdown_text: str, filename: str = "report.md", base_dir: Path | None = None
    ) -> None:
        """Renders raw Markdown text and populates all views."""
        self._raw_markdown = markdown_text
        line_count = len(markdown_text.splitlines())

        # Update Toolbar
        self.title_label.setText(filename.upper())
        self.stats_badge.setText(f"{line_count:,} LINES")

        # Parse Markdown into HTML and Headings
        html_content, headings = MarkdownParser.parse(markdown_text, base_dir=base_dir)
        self._headings = headings

        # 1. Populate TOC Tree
        self.toc_widget.populate(headings)

        # 2. Populate Rendered HTML View
        self.browser.setHtml(html_content)

        # 3. Populate Source View
        self.source_view.setPlainText(markdown_text)

        # Reset Zoom
        self.reset_zoom()

    def set_view_mode(self, mode: int) -> None:
        """Switches between 0 (Rendered View) and 1 (Source View)."""
        self.content_stack.setCurrentIndex(mode)
        if mode == 0:
            self.rendered_btn.setChecked(True)
        else:
            self.source_btn.setChecked(True)

    # -------------------------------------------------------------------------
    # Search & Navigation Slots
    # -------------------------------------------------------------------------

    def open_search(self) -> None:
        self.search_bar.setVisible(True)
        self.search_bar.focus_input()

    def toggle_search(self) -> None:
        self.search_bar.setVisible(not self.search_bar.isVisible())
        if self.search_bar.isVisible():
            self.search_bar.focus_input()

    def _on_search_closed(self) -> None:
        self.browser.setExtraSelections([])

    def _on_search_requested(self, query: str, forward: bool, case_sensitive: bool) -> None:
        """Performs search in the active view (Rendered or Source)."""
        active_view = self.browser if self.content_stack.currentIndex() == 0 else self.source_view

        flags = QTextDocument.FindFlag(0)
        if not forward:
            flags |= QTextDocument.FindFlag.FindBackward
        if case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively

        found = active_view.find(query, flags)
        if not found:
            # Wrap around search
            cursor = active_view.textCursor()
            if forward:
                cursor.movePosition(QTextCursor.MoveOperation.Start)
            else:
                cursor.movePosition(QTextCursor.MoveOperation.End)
            active_view.setTextCursor(cursor)
            found = active_view.find(query, flags)

        # Count total matches for user feedback
        text = active_view.toPlainText()
        total_matches = text.count(query if case_sensitive else query.lower())
        self.search_bar.set_match_status(1 if found else 0, total_matches)

    def _on_heading_selected(self, anchor: str) -> None:
        """Scrolls rendered view to selected heading anchor."""
        if self.content_stack.currentIndex() != 0:
            self.set_view_mode(0)
        self.browser.scrollToAnchor(anchor)

    def _on_anchor_clicked(self, url) -> None:
        """Handles internal anchor links without external navigation."""
        frag = url.fragment()
        if frag:
            self.browser.scrollToAnchor(frag)
            self.toc_widget.select_heading(frag)

    # -------------------------------------------------------------------------
    # Zoom Controls
    # -------------------------------------------------------------------------

    def zoom_in(self) -> None:
        if self._zoom_level < 8:
            self._zoom_level += 1
            self.browser.zoomIn(1)
            self.source_view.zoomIn(1)
            self._update_zoom_label()

    def zoom_out(self) -> None:
        if self._zoom_level > -4:
            self._zoom_level -= 1
            self.browser.zoomOut(1)
            self.source_view.zoomOut(1)
            self._update_zoom_label()

    def reset_zoom(self) -> None:
        if self._zoom_level != 0:
            diff = -self._zoom_level
            if diff > 0:
                self.browser.zoomIn(diff)
                self.source_view.zoomIn(diff)
            else:
                self.browser.zoomOut(-diff)
                self.source_view.zoomOut(-diff)
            self._zoom_level = 0
            self._update_zoom_label()

    def _update_zoom_label(self) -> None:
        percent = int(100 * (1.15 ** self._zoom_level))
        self.zoom_label.setText(f"{percent}%")

    # -------------------------------------------------------------------------
    # Actions: Copy & PDF Export
    # -------------------------------------------------------------------------

    def copy_content(self) -> None:
        """Copies document content to system clipboard."""
        clipboard = QApplication.clipboard()
        if self.content_stack.currentIndex() == 0:
            clipboard.setText(self.browser.toPlainText())
        else:
            clipboard.setText(self.source_view.toPlainText())
        QMessageBox.information(self, "Copied", "Document content copied to clipboard!")

    def export_pdf(self) -> None:
        """Exports the rendered Markdown report to PDF."""
        default_name = (
            f"{self._current_path.stem}.pdf" if self._current_path else "cs01-report.pdf"
        )
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Report to PDF", default_name, "PDF Files (*.pdf)"
        )
        if path:
            try:
                from PySide6.QtGui import QPageLayout, QPageSize, QPagedPaintDevice, QPdfWriter
                writer = QPdfWriter(path)
                writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                writer.setResolution(300)
                self.browser.document().print_(writer)
                QMessageBox.information(self, "Export Successful", f"Report saved to:\n{path}")
            except Exception as e:
                QMessageBox.critical(self, "Export Failed", f"Could not export PDF:\n{e}")

    # -------------------------------------------------------------------------
    # Empty State & Theme Handlers
    # -------------------------------------------------------------------------

    def _render_empty_state(self, message: str) -> None:
        self.title_label.setText("NO REPORT FOUND")
        self.stats_badge.setText("")
        self.toc_widget.populate([])
        empty_html = f"""
        <html>
        <body style="background-color: #FFF6CC; padding: 40px; font-family: sans-serif; text-align: center;">
            <div style="background-color: #FFFFFF; border: 2px solid #111111; padding: 40px; max-width: 600px; margin: 0 auto;">
                <h2 style="font-size: 16pt; font-weight: 800; color: #111111;">NO REPORT SELECTED</h2>
                <p style="font-size: 10pt; color: #595959; font-weight: 600;">{message}</p>
                <p style="font-size: 9pt; color: #111111;">Run a compliance audit or click 'Load Reports' in the top HUD to view deliverables.</p>
            </div>
        </body>
        </html>
        """
        self.browser.setHtml(empty_html)
        self.source_view.setPlainText(message)

    def _on_theme_changed(self) -> None:
        """Re-renders active document when theme changes dynamically."""
        if self._raw_markdown:
            base_dir = self._current_path.parent if self._current_path else None
            html_content, _ = MarkdownParser.parse(self._raw_markdown, base_dir=base_dir)
            self.browser.setHtml(html_content)
