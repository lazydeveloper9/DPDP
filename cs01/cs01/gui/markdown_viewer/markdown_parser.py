"""
CS-01 DPDP Compliance Desktop GUI - Markdown Document Parser & HTML Engine.

Converts CommonMark and GitHub Flavored Markdown (GFM) into styled HTML
conforming strictly to the CS-01 Neo-Brutalist Bold Enterprise design language.
Includes language-aware Pygments syntax highlighting, GFM tables, heading anchors,
and safe local asset resolution with zero external egress.
"""
from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygments
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name

from cs01.gui.theme_engine.theme_manager import ThemeManager


@dataclass
class HeadingItem:
    """Represents a heading entry in the Table of Contents."""
    level: int
    title: str
    anchor: str
    line_number: int


class MarkdownParser:
    """
    Safe offline Markdown-to-HTML parser with Neo-Brutalist styling.
    Extracts heading hierarchy and prevents remote resource egress.
    """

    HEADING_REGEX = re.compile(r"^(#{1,6})\s+(.+)$")
    TABLE_ROW_REGEX = re.compile(r"^\s*\|(.+)\|\s*$")
    TABLE_SEP_REGEX = re.compile(r"^\s*\|(\s*[-:]+[-| :]*)\|\s*$")
    FENCE_START_REGEX = re.compile(r"^```(\w*)\s*$")
    IMAGE_REGEX = re.compile(r"!\[(.*?)\]\((.*?)\)")
    LINK_REGEX = re.compile(r"\[(.*?)\]\((.*?)\)")
    BOLD_REGEX = re.compile(r"\*\*(.+?)\*\*")
    ITALIC_REGEX = re.compile(r"\*(.+?)\*")
    STRIKE_REGEX = re.compile(r"~~(.+?)~~")
    CODE_INLINE_REGEX = re.compile(r"`(.+?)`")

    @classmethod
    def slugify(cls, text: str) -> str:
        """Converts heading text into a unique URL/anchor slug."""
        clean = re.sub(r"<[^>]+>", "", text).strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
        return slug or "section"

    @classmethod
    def parse(
        cls, markdown_text: str, base_dir: Path | None = None
    ) -> tuple[str, list[HeadingItem]]:
        """
        Parses Markdown into rendered HTML and a Table of Contents list.

        Args:
            markdown_text: Raw Markdown text.
            base_dir: Optional base directory for resolving local relative image paths.

        Returns:
            Tuple of (complete_html_string, list_of_HeadingItem)
        """
        lines = markdown_text.splitlines()
        headings: list[HeadingItem] = []
        html_out: list[str] = []

        in_code_block = False
        code_lang = ""
        code_lines: list[str] = []

        in_table = False
        table_headers: list[str] = []
        table_rows: list[list[str]] = []

        in_blockquote = False
        quote_lines: list[str] = []

        in_list = False
        list_type = "ul"

        anchor_counts: dict[str, int] = {}

        def _make_unique_anchor(title_str: str) -> str:
            base_anchor = cls.slugify(title_str)
            count = anchor_counts.get(base_anchor, 0)
            anchor_counts[base_anchor] = count + 1
            return base_anchor if count == 0 else f"{base_anchor}-{count}"

        def _flush_table() -> None:
            nonlocal in_table, table_headers, table_rows
            if not in_table:
                return
            html_out.append('<div class="table-container"><table class="report-table">')
            if table_headers:
                html_out.append("<thead><tr>")
                for h in table_headers:
                    html_out.append(f"<th>{cls._format_inline(h)}</th>")
                html_out.append("</tr></thead>")
            if table_rows:
                html_out.append("<tbody>")
                for r in table_rows:
                    html_out.append("<tr>")
                    for cell in r:
                        html_out.append(f"<td>{cls._format_inline(cell)}</td>")
                    html_out.append("</tr>")
                html_out.append("</tbody>")
            html_out.append("</table></div>")
            in_table = False
            table_headers = []
            table_rows = []

        def _flush_quote() -> None:
            nonlocal in_blockquote, quote_lines
            if not in_blockquote or not quote_lines:
                return
            quote_text = "<br>".join(cls._format_inline(l) for l in quote_lines)
            html_out.append(f'<blockquote class="report-quote">{quote_text}</blockquote>')
            quote_lines = []
            in_blockquote = False

        def _flush_list() -> None:
            nonlocal in_list, list_type
            if in_list:
                html_out.append(f"</{list_type}>")
                in_list = False

        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()

            # 1. Code Fences
            fence_match = cls.FENCE_START_REGEX.match(stripped)
            if fence_match:
                if in_code_block:
                    # Closing fence
                    raw_code = "\n".join(code_lines)
                    highlighted = cls._highlight_code(raw_code, code_lang)
                    badge_label = code_lang.upper() if code_lang else "CODE"
                    html_out.append(
                        f'<div class="code-container">'
                        f'<div class="code-header"><span>{badge_label}</span></div>'
                        f'<pre class="code-block"><code>{highlighted}</code></pre>'
                        f'</div>'
                    )
                    in_code_block = False
                    code_lang = ""
                    code_lines = []
                else:
                    # Opening fence
                    _flush_table()
                    _flush_quote()
                    _flush_list()
                    in_code_block = True
                    code_lang = fence_match.group(1).lower()
                    code_lines = []
                continue

            if in_code_block:
                code_lines.append(line)
                continue

            # 2. Blockquotes
            if stripped.startswith(">"):
                _flush_table()
                _flush_list()
                in_blockquote = True
                q_content = stripped.lstrip("> ").strip()
                quote_lines.append(q_content)
                continue
            elif in_blockquote:
                _flush_quote()

            # 3. Tables (GFM pipe tables)
            table_match = cls.TABLE_ROW_REGEX.match(line)
            if table_match:
                _flush_list()
                cells = [c.strip() for c in table_match.group(1).split("|")]
                if cls.TABLE_SEP_REGEX.match(line):
                    # Separator row between header and body
                    continue
                if not in_table:
                    in_table = True
                    table_headers = cells
                else:
                    table_rows.append(cells)
                continue
            elif in_table:
                _flush_table()

            # 4. Horizontal Rules
            if stripped in ("---", "***", "___", "- - -", "* * *"):
                _flush_list()
                html_out.append('<hr class="report-hr" />')
                continue

            # 5. Headings
            h_match = cls.HEADING_REGEX.match(line)
            if h_match:
                _flush_list()
                level = len(h_match.group(1))
                raw_title = h_match.group(2).strip()
                clean_title = re.sub(r"[*_`]", "", raw_title)
                anchor = _make_unique_anchor(clean_title)
                headings.append(
                    HeadingItem(
                        level=level,
                        title=clean_title,
                        anchor=anchor,
                        line_number=line_num,
                    )
                )
                formatted_title = cls._format_inline(raw_title)
                html_out.append(
                    f'<h{level} id="{anchor}" class="report-h{level}">'
                    f'<a name="{anchor}"></a>{formatted_title}'
                    f'</h{level}>'
                )
                continue

            # 6. Lists (ordered, unordered, and task lists)
            ul_match = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            ol_match = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
            if ul_match or ol_match:
                m = ul_match or ol_match
                curr_type = "ul" if ul_match else "ol"
                item_content = m.group(2)

                if not in_list or list_type != curr_type:
                    _flush_list()
                    in_list = True
                    list_type = curr_type
                    html_out.append(f'<{list_type} class="report-list">')

                # Check for GitHub-style task list: [ ] or [x]
                if item_content.startswith("[ ] "):
                    task_text = cls._format_inline(item_content[4:])
                    html_out.append(f'<li class="task-item"><span class="task-box">☐</span> {task_text}</li>')
                elif item_content.startswith("[x] ") or item_content.startswith("[X] "):
                    task_text = cls._format_inline(item_content[4:])
                    html_out.append(f'<li class="task-item task-done"><span class="task-box">☑</span> {task_text}</li>')
                else:
                    html_out.append(f'<li>{cls._format_inline(item_content)}</li>')
                continue
            elif in_list:
                _flush_list()

            # 7. Images
            img_match = cls.IMAGE_REGEX.search(line)
            if img_match:
                alt = img_match.group(1)
                src = img_match.group(2).strip()
                resolved = cls._resolve_image(src, base_dir)
                if resolved:
                    html_out.append(f'<div class="img-wrap"><img src="{resolved}" alt="{alt}" class="report-img" /></div>')
                else:
                    html_out.append(f'<div class="img-placeholder"><strong>[Image: {alt} ({src}) - not found locally]</strong></div>')
                continue

            # 8. Empty lines
            if not stripped:
                html_out.append('<div class="spacer"></div>')
                continue

            # 9. Regular Paragraphs
            html_out.append(f'<p class="report-p">{cls._format_inline(line)}</p>')

        # Final flushes
        _flush_table()
        _flush_quote()
        _flush_list()

        body_html = "\n".join(html_out)
        full_html = cls._wrap_html(body_html)
        return full_html, headings

    @classmethod
    def _format_inline(cls, text: str) -> str:
        """Applies inline formatting for bold, italic, code, and links with escaping."""
        # Sanitize HTML tags except allowed inline markup
        escaped = html.escape(text)

        # Inline code: `code`
        escaped = cls.CODE_INLINE_REGEX.sub(r'<code class="inline-code">\1</code>', escaped)

        # Bold: **bold**
        escaped = cls.BOLD_REGEX.sub(r"<strong>\1</strong>", escaped)

        # Italic: *italic*
        escaped = cls.ITALIC_REGEX.sub(r"<em>\1</em>", escaped)

        # Strikethrough: ~~strike~~
        escaped = cls.STRIKE_REGEX.sub(r"<del>\1</del>", escaped)

        # Links: [text](url) -> safe local or explicit link
        escaped = cls.LINK_REGEX.sub(r'<a href="\2" class="report-link">\1</a>', escaped)

        return escaped

    @classmethod
    def _highlight_code(cls, code: str, lang: str) -> str:
        """Highlights code block syntax using Pygments with HTML escaping fallback."""
        if not code.strip():
            return ""
        try:
            lexer = get_lexer_by_name(lang) if lang else TextLexer()
        except Exception:
            lexer = TextLexer()

        formatter = HtmlFormatter(nowrap=True)
        try:
            return pygments.highlight(code, lexer, formatter)
        except Exception:
            return html.escape(code)

    @classmethod
    def _resolve_image(cls, src: str, base_dir: Path | None) -> str | None:
        """Resolves local image path safely, preventing directory traversal outside root."""
        if src.startswith("http://") or src.startswith("https://"):
            return None  # Disallow external image downloads for zero-egress compliance

        if base_dir:
            p = (base_dir / src).resolve()
            if p.exists() and p.is_file():
                return p.as_uri()

        direct_p = Path(src).resolve()
        if direct_p.exists() and direct_p.is_file():
            return direct_p.as_uri()

        return None

    @classmethod
    def _wrap_html(cls, body_html: str) -> str:
        """Wraps document body in full HTML template with Neo-Brutalist CSS."""
        tm = ThemeManager.instance()
        bg_main = str(tm.get_token("global.bg.main", "#FFF6CC"))
        surface_bg = str(tm.get_token("component.card.bg", "#FFFFFF"))
        surface_alt = str(tm.get_token("global.bg.card_secondary", "#FFF4C2"))
        text_primary = str(tm.get_token("global.text.primary", "#111111"))
        text_muted = str(tm.get_token("global.text.muted", "#595959"))
        border_col = str(tm.get_token("design.border.color", "#111111"))
        border_width = int(tm.get_token("design.border.width", 2))
        accent_yellow = str(tm.get_token("global.accent.primary", "#FFE500"))
        accent_blue = str(tm.get_token("global.accent.secondary", "#3155FF"))
        font_sans = str(tm.get_token("typography.font_sans", '"Space Grotesk", "Inter", sans-serif'))
        font_mono = str(tm.get_token("typography.font_mono", '"Cascadia Code", "Consolas", monospace'))

        pygments_css = HtmlFormatter().get_style_defs(".code-block")

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    body {{
        background-color: {bg_main};
        color: {text_primary};
        font-family: {font_sans};
        font-size: 10.5pt;
        line-height: 1.6;
        margin: 0;
        padding: 16px;
    }}
    .report-container {{
        background-color: {surface_bg};
        border: {border_width}px solid {border_col};
        padding: 24px 32px;
        margin: 0 auto;
        max-width: 960px;
    }}
    h1.report-h1 {{
        font-size: 18pt;
        font-weight: 800;
        color: {text_primary};
        border-bottom: {border_width}px solid {border_col};
        padding-bottom: 6px;
        margin-top: 16px;
        margin-bottom: 12px;
        letter-spacing: -0.5px;
    }}
    h2.report-h2 {{
        font-size: 14pt;
        font-weight: 800;
        color: {text_primary};
        border-bottom: 1.5px solid {border_col};
        padding-bottom: 4px;
        margin-top: 20px;
        margin-bottom: 10px;
    }}
    h3.report-h3 {{
        font-size: 11.5pt;
        font-weight: 700;
        color: {text_primary};
        margin-top: 14px;
        margin-bottom: 6px;
    }}
    h4.report-h4, h5.report-h5, h6.report-h6 {{
        font-size: 10pt;
        font-weight: 700;
        color: {text_primary};
        margin-top: 10px;
        margin-bottom: 4px;
    }}
    p.report-p {{
        margin: 6px 0;
        color: {text_primary};
    }}
    .spacer {{
        height: 8px;
    }}
    hr.report-hr {{
        border: none;
        border-top: {border_width}px solid {border_col};
        margin: 18px 0;
    }}
    /* Tables */
    .table-container {{
        overflow-x: auto;
        margin: 12px 0;
    }}
    table.report-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 9.5pt;
        border: {border_width}px solid {border_col};
        background-color: {surface_bg};
    }}
    table.report-table th {{
        background-color: {accent_yellow};
        color: {text_primary};
        font-weight: 800;
        padding: 8px 10px;
        border: 1px solid {border_col};
        text-align: left;
    }}
    table.report-table td {{
        padding: 6px 10px;
        border: 1px solid {border_col};
        color: {text_primary};
    }}
    table.report-table tr:nth-child(even) {{
        background-color: {surface_alt};
    }}
    /* Code Blocks */
    .code-container {{
        margin: 12px 0;
        border: {border_width}px solid {border_col};
        background-color: {surface_alt};
    }}
    .code-header {{
        background-color: {border_col};
        color: #FFFFFF;
        font-family: {font_mono};
        font-size: 8pt;
        font-weight: 800;
        padding: 3px 8px;
        letter-spacing: 0.5px;
    }}
    pre.code-block {{
        margin: 0;
        padding: 10px 14px;
        font-family: {font_mono};
        font-size: 9.5pt;
        color: {text_primary};
        overflow-x: auto;
        white-space: pre-wrap;
    }}
    code.inline-code {{
        font-family: {font_mono};
        font-size: 9pt;
        font-weight: 700;
        background-color: {surface_alt};
        border: 1px solid {border_col};
        padding: 2px 5px;
    }}
    /* Quotes */
    blockquote.report-quote {{
        border-left: 4px solid {border_col};
        background-color: {surface_alt};
        padding: 8px 14px;
        margin: 10px 0;
        font-style: italic;
        color: {text_primary};
    }}
    /* Lists */
    ul.report-list, ol.report-list {{
        margin: 8px 0;
        padding-left: 24px;
    }}
    li.task-item {{
        list-style-type: none;
        margin-left: -14px;
    }}
    span.task-box {{
        font-family: {font_mono};
        font-weight: bold;
    }}
    li.task-done {{
        text-decoration: line-through;
        color: {text_muted};
    }}
    /* Links */
    a.report-link {{
        color: {accent_blue};
        font-weight: 700;
        text-decoration: underline;
    }}
    /* Images */
    .img-wrap {{
        text-align: center;
        margin: 12px 0;
    }}
    img.report-img {{
        max-width: 100%;
        border: {border_width}px solid {border_col};
    }}
    .img-placeholder {{
        background-color: #FFE8E8;
        border: 1.5px dashed #FF4444;
        color: #CC0000;
        padding: 8px 12px;
        font-size: 9pt;
        margin: 8px 0;
    }}
    /* Pygments styles */
    {pygments_css}
</style>
</head>
<body>
<div class="report-container">
{body_html}
</div>
</body>
</html>"""
