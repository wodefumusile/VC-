"""WeChat formatter v2 - PRESERVES AI-generated HTML structure.

Instead of stripping HTML and rebuilding, we:
1. Keep the AI's h2, p, blockquote, strong structure
2. Add WeChat-compatible inline styles
3. Clean only metadata labels like (正文), (解释)
"""

import re
from loguru import logger

# WeChat-compatible inline styles
P_STYLE = "margin-bottom:20px;line-height:1.8;font-size:16px;color:#333"
H2_STYLE = "margin-top:28px;margin-bottom:15px;font-size:20px;font-weight:bold;color:#2c3e0"
STRONG_STYLE = "color:#c0392b;font-weight:bold"
BQ_STYLE = "margin:15px 0;padding:10px 15px;border-left:3px solid #3498db;background:#f0f6fc;color:#555;font-size:15px"
LI_STYLE = "margin-bottom:8px;line-height:1.7;font-size:16px;color:#333"

# Metadata labels to strip from content
METADATA_LABELS = [
    "（正文）", "（解释）", "（说明）", "（标题）",
    "【正文】", "【解释】", "【说明】",
    "正文：", "解释：",
]


def clean_metadata(text: str) -> str:
    """Remove metadata labels from article text."""
    for label in METADATA_LABELS:
        text = text.replace(label, "")
    return text.strip()


def format_article(title: str, content_html: str, author: str = "", template: str = "knowledge") -> dict:
    """Transform AI-generated HTML into WeChat-compatible format.

    Preserves the AI's structure (h2, p, blockquote, strong) and adds
    inline styles that WeChat's editor accepts.
    """
    logger.info("format v2 | template={} | title_len={} | html_len={}",
                template, len(title), len(content_html))

    html = content_html

    # 1. Clean metadata labels
    html = clean_metadata(html)

    # 2. Convert h2 -> styled p (WeChat strips h2, but keeps styled p)
    html = re.sub(
        r'<h2[^>]*>(.*?)</h2>',
        rf'<p style="{H2_STYLE}"><span style="{H2_STYLE}">\1</span></p>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    html = re.sub(
        r'<h3[^>]*>(.*?)</h3>',
        rf'<p style="{H2_STYLE}"><span style="{H2_STYLE}">\1</span></p>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 3. Convert blockquote -> styled blockquote
    html = re.sub(
        r'<blockquote[^>]*>(.*?)</blockquote>',
        rf'<blockquote style="{BQ_STYLE}">\1</blockquote>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # 4. Add style to p tags (only those without existing style)
    def add_p_style(match):
        tag_content = match.group(0)
        if 'style=' in tag_content.lower():
            return tag_content
        return match.group(0).replace('<p>', f'<p style="{P_STYLE}">').replace('<p ', f'<p style="{P_STYLE}" ')

    html = re.sub(r'<p[^>]*>.*?</p>', add_p_style, html, flags=re.DOTALL)

    # 5. Add strong style
    html = html.replace('<strong>', f'<strong style="{STRONG_STYLE}">')
    html = re.sub(r'<strong ([^>]*)>', rf'<strong style="{STRONG_STYLE}" \1>', html)

    # 6. Add li style
    html = re.sub(r'<li>', f'<li style="{LI_STYLE}">', html)

    # 7. Build final WeChat article HTML
    parts = []

    # Title block
    parts.append(
        f'<p style="text-align:center;margin-bottom:8px;line-height:1.4">'
        f'<span style="font-size:22px;font-weight:bold;color:#2c3e0">{title[:64]}</span>'
        f'</p>'
    )
    if author:
        parts.append(
            f'<p style="text-align:center;margin-bottom:25px">'
            f'<span style="font-size:13px;color:#999">{author}</span>'
            f'</p>'
        )

    # Body
    parts.append(html)

    # Footer
    parts.append(
        f'<p style="text-align:center;margin:30px 0 5px">'
        f'<span style="font-size:13px;color:#bbb">—— END ——</span>'
        f'</p>'
    )

    result_html = "\n".join(parts)

    # Validate
    p_count = result_html.count("</p>")
    strong_count = result_html.count("<strong")
    bq_count = result_html.count("<blockquote")

    logger.success("format v2 done | html={} | p={} strong={} bq={}",
                   len(result_html), p_count, strong_count, bq_count)

    # Generate summary from first paragraph
    summary = ""
    m = re.search(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
    if m:
        raw_summary = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        summary = raw_summary[:120]

    return {
        "title": title[:64],
        "content_html": result_html,
        "summary": summary,
        "template": template,
    }