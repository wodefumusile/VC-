import re
from dataclasses import dataclass, field

NL = chr(10)

@dataclass
class ContentBlock:
    type: str = "paragraph"
    text: str = ""

@dataclass  
class ArticleSection:
    heading: str = ""
    blocks: list = field(default_factory=list)

@dataclass
class ArticleStructure:
    title: str = ""
    intro: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    all_blocks: list = field(default_factory=list)

def analyze_structure(text):
    text = re.sub(r"<[^>]+>", "", text).strip()
    result = ArticleStructure()
    
    markers = [
        "\u7b2c\u4e00", "\u7b2c\u4e8c", "\u7b2c\u4e09",
        "\u9996\u5148", "\u5176\u6b21", "\u6700\u540e",
        "\u53e6\u5916", "\u6b64\u5916",
        "\u603b\u4e4b", "\u603b\u7ed3", "\u7efc\u4e0a",
    ]
    
    pattern = "(?:" + NL + "|^)(" + "|".join(markers) + ")"
    segments = re.split(pattern, text)
    
    if len(segments) <= 2:
        return _simple_split(text, result)
    
    current_parts = []
    current_marker = None
    in_intro = True
    
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        if seg in markers:
            if current_parts:
                content_text = "".join(current_parts).strip()
                if content_text:
                    section = ArticleSection(heading=current_marker, blocks=_to_blocks(content_text))
                    in_intro = False
                    result.sections.append(section)
                current_parts = []
            current_marker = seg
        else:
            current_parts.append(seg)
    
    if current_parts:
        content_text = "".join(current_parts).strip()
        if content_text:
            section = ArticleSection(heading=current_marker, blocks=_to_blocks(content_text))
            result.sections.append(section)
    
    if not result.sections:
        result = _simple_split(text, result)
    
    return result

def _simple_split(text, result):
    paras = [p.strip() for p in text.split(NL + NL) if p.strip()]
    if len(paras) <= 1:
        paras = [p.strip() for p in text.split(NL) if p.strip()]
    
    if len(paras) <= 1:
        blocks = _to_blocks(text)
        if blocks:
            result.sections = [ArticleSection(blocks=blocks)]
        return result
    
    if paras:
        result.intro = _to_blocks(paras[0])
    for p in paras[1:]:
        section = ArticleSection(blocks=_to_blocks(p))
        result.sections.append(section)
    
    return result

def _to_blocks(text, max_chars=100):
    if not text.strip():
        return []
    if len(text) <= max_chars:
        return [ContentBlock(text=text)]
    
    sentences = re.split(r"(?<=[\u3002\uff01\uff1f\uff1b])", text)
    blocks = []
    current = ""
    
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if len(current) + len(s) <= max_chars:
            current += s
        else:
            if current.strip():
                blocks.append(ContentBlock(text=current.strip()))
            current = s
    
    if current.strip():
        blocks.append(ContentBlock(text=current.strip()))
    
    return blocks

def split_paragraphs(text, max_chars=100):
    blocks = _to_blocks(text, max_chars)
    return [b.text for b in blocks]
