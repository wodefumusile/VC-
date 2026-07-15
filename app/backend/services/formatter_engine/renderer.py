"""Renderer — section+span WeChat-compatible HTML renderer.

Reads template JSON, renders with section+span pattern.
Do NOT put style on block elements (p, h2, h3) — WeChat strips them.
"""

import re
import json
from pathlib import Path
from loguru import logger
from backend.config import settings
from __future__ import annotations

# Default font sizes
WECHAT_FONT = {"h1": "22px", "h2": "18px", "h3": "16px", "body": "15px", "small": "13px"}


def load_template(name: str) -> dict:
    """Load template JSON file.

    Args:
        name: Template name (technology, business, knowledge, personal)

    Returns:
        Template dict with style config
    """
    template_path = settings.TEMPLATES_DIR / "wechat" / f"{name}.json"
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    # Fallback
    logger.warning("Template not found: {}, using defaults", template_path)
    return _default_template()


def _default_template() -> dict:
    return {
        "name": "default",
        "h1_color": "#2c3e50", "h2_color": "#34495e",
        "body_color": "#444", "body_size": "16px", "line_height": "2.0",
        "img_style": "max-width:100%;border-radius:8px",
        "footer_text": "— END —",
    }


def render(title: str, content_html: str, author: str = "",
           template: str = "knowledge", images: list[dict] = None) -> dict:
    """Render article to WeChat-compatible HTML.

    Uses section+span pattern for ProseMirror compatibility.

    Args:
        title: Article title
        content_html: Cleaned HTML content
        author: Author name
        template: Template name
        images: Optional list of image records for injection

    Returns:
        {"title": str, "content_html": str, "summary": str, "template": str}
    """
    tmpl = load_template(template)
    h1_c = tmpl.get("h1_color", "#2c3e50")
    h2_c = tmpl.get("h2_color", "#34495e")
    body_c = tmpl.get("body_color", "#444")
    body_s = tmpl.get("body_size", "16px")
    lh = tmpl.get("line_height", "2.0")
    footer = tmpl.get("footer_text", "— END —")
    img_style = tmpl.get("img_style", "max-width:100%;border-radius:8px")

    parts = []

    # --- Title block ---
    parts.append(
        f'<section style="text-align:center;margin:12px 0 20px">'
        f'<span style="font-size:{WECHAT_FONT["h1"]};color:{h1_c};font-weight:bold">'
        f'{title[:64]}</span></section>'
    )

    if author:
        parts.append(
            f'<section style="text-align:center;margin-bottom:14px">'
            f'<span style="font-size:{WECHAT_FONT["small"]};color:#999">'
            f'✍️ {author}</span></section>'
        )

    # Divider
    parts.append('<section style="border-top:1px solid #eee;margin:8px 0 16px"></section>')

    # --- Body ---
    html = content_html

    # h1 → section+span centered
    html = re.sub(
        r'<h1[^>]*>(.*?)</h1>',
        rf'<section style="text-align:center;margin:12px 0 20px">'
        rf'<span style="font-size:{WECHAT_FONT["h1"]};color:{h1_c};font-weight:bold">\1</span></section>',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # h2 → section+span with left border
    html = re.sub(
        r'<h2[^>]*>(.*?)</h2>',
        rf'<section style="margin:16px 0 8px;padding-left:8px;border-left:3px solid {h2_c}">'
        rf'<span style="font-size:{WECHAT_FONT["h2"]};color:{h2_c};font-weight:bold">\1</span></section>',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # h3 → section+span
    html = re.sub(
        r'<h3[^>]*>(.*?)</h3>',
        rf'<section style="margin:12px 0 6px">'
        rf'<span style="font-size:{WECHAT_FONT["h3"]};color:{h2_c};font-weight:bold">\1</span></section>',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # strong → red bold
    html = re.sub(r'<strong([^>]*)>', r'<strong style="color:#e74c3c"\1>', html)

    # blockquote → gray background section
    html = re.sub(
        r'<blockquote[^>]*>(.*?)</blockquote>',
        r'<section style="background:#f5f5f5;border-left:3px solid #ddd;padding:8px 12px;margin:10px 0">'
        r'<span style="font-size:14px;color:#888">\1</span></section>',
        html, flags=re.DOTALL | re.IGNORECASE
    )

    # p → section+span (no style on p!)
    def wrap_p(m):
        c = m.group(1).strip()
        if not c:
            return '<p><br></p>'
        if '<img' in c:
            # Keep img as-is, wrap with section
            return f'<section style="margin-bottom:12px">{c}</section>'
        return (f'<section style="margin-bottom:12px">'
                f'<span style="font-size:{body_s};color:{body_c};line-height:{lh};'
                f'letter-spacing:0.5px">{c}</span></section>')
    html = re.sub(r'<p[^>]*>(.*?)</p>', wrap_p, html, flags=re.DOTALL)

    # li → span inside
    def wrap_li(m):
        return (f'<li><span style="font-size:{body_s};color:{body_c};line-height:{lh}">'
                f'{m.group(1)}</span></li>')
    html = re.sub(r'<li[^>]*>(.*?)</li>', wrap_li, html, flags=re.DOTALL)

    # hr → divider
    html = re.sub(r'<hr[^>]*>', '<section style="border-top:1px solid #eee;margin:12px 0"></section>', html)

    # img → enhance with style
    html = re.sub(
        r'<img[^>]*>',
        lambda m: _enhance_img(m.group(0), img_style),
        html
    )

    parts.append(html)

    # --- Footer ---
    parts.append(
        f'<section style="text-align:center;margin:30px 0 5px">'
        f'<span style="font-size:{WECHAT_FONT["small"]};color:#bbb">{footer}</span></section>'
    )

    result_html = "\n".join(parts)

    # Generate summary
    summary = ""
    m = re.search(r'<p[^>]*>(.*?)</p>', content_html, re.DOTALL)
    if m:
        summary = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:120]

    logger.success("FormatterEngine rendered | template={} | html_len={}", template, len(result_html))
    return {
        "title": title[:64],
        "content_html": result_html,
        "summary": summary,
        "template": template,
    }


def _enhance_img(img_tag: str, style: str) -> str:
    """Add WeChat-compatible styling to img tag."""
    if 'style=' in img_tag:
        return img_tag
    return img_tag.replace('<img', f'<img style="{style}"')
