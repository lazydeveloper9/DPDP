"""
CS-01 DPDP Compliance Desktop GUI - In-App Markdown Report Viewer Package.
"""
from __future__ import annotations

from cs01.gui.markdown_viewer.markdown_parser import HeadingItem, MarkdownParser
from cs01.gui.markdown_viewer.search_widget import MarkdownSearchBar
from cs01.gui.markdown_viewer.source_view import MarkdownSourceView
from cs01.gui.markdown_viewer.toc_widget import TableOfContentsWidget
from cs01.gui.markdown_viewer.viewer_view import AuditReportViewer

__all__ = [
    "HeadingItem",
    "MarkdownParser",
    "MarkdownSearchBar",
    "MarkdownSourceView",
    "TableOfContentsWidget",
    "AuditReportViewer",
]
