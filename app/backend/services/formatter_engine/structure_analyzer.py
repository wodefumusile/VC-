"""Structure Analyzer — smart article content enhancement.

Auto-detects:
- Subheadings: 第一/首先/其次/最后/一、/二、etc.
- Quotes: 据统计/数据显示/案例 etc.
- Data: 30%/500万/10亿元 etc. → auto-bold
"""

import re
from loguru import logger

# Subheading trigger patterns
SUBHEADING_TRIGGERS = [
    r'^第[一二三四五六七八九十\d]+[、，,. ]',
    r'^(首先|其次|最后|另外|此外|总之|总结|综上|然而|但是|不过|因此|所以)',
    r'^[一二三四五六七八九十]+[、．.]',
    r'^\d+[、．.]',
]

# Quote trigger patterns
QUOTE_TRIGGERS = [
    r'^(案例|数据|观点|引用|例如|比如|举个例子|据统计|调查显示|研究表明|根据.*数据显示)',
]

# Data patterns for auto-bold
DATA_PATTERN = r'([\d,.]+[万亿千百%％倍元美金人民币€¥\w]{1,3})'


def analyze_and_enhance(html: str) -> str:
    """Analyze article structure and apply smart enhancements.

    - Wraps detected subheadings in <h2>
    - Wraps detected quotes in <blockquote>
    - Bolds detected data patterns

    Args:
        html: Cleaned HTML content

    Returns:
        Enhanced HTML with structural markup
    """
    # Find all <p> blocks
    def enhance_paragraph(match):
        full_tag = match.group(0)
        content = match.group(1).strip()

        # Skip if already has strong/em inside
        if '<strong' in full_tag.lower() or '<em' in full_tag.lower():
            return full_tag

        # Check subheading
        for pattern in SUBHEADING_TRIGGERS:
            if re.match(pattern, content) and len(content) <= 40:
                # Clean subheading markers
                title = re.sub(r'^第[一二三四五六七八九十\d]+[、，,. ]*', '', content)
                title = re.sub(r'^(首先|其次|最后|另外|此外|总之|总结|综上|然而|但是|不过|因此|所以)[，, ]*', '', title)
                title = re.sub(r'^[一二三四五六七八九十\d]+[、．.]*', '', title)
                logger.debug("Detected subheading: {}", title[:30])
                return f'<h2>{title}</h2>'

        # Check quote
        for pattern in QUOTE_TRIGGERS:
            if re.match(pattern, content):
                logger.debug("Detected quote: {}", content[:30])
                # Also bold data within quote
                quote_content = re.sub(DATA_PATTERN, r'<strong>\1</strong>', content)
                return f'<blockquote>{quote_content}</blockquote>'

        # Bold data patterns
        if re.search(DATA_PATTERN, content):
            enhanced = re.sub(DATA_PATTERN, r'<strong>\1</strong>', content)
            return f'<p>{enhanced}</p>'

        return full_tag

    html = re.sub(r'<p[^>]*>(.*?)</p>', enhance_paragraph, html, flags=re.DOTALL)
    return html
