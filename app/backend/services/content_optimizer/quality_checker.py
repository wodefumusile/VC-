"""
Article Quality Checker

Scores articles 0-100 across: title, content, structure, readability,
duplication risk, and AI-trace detection.
"""

import re
from loguru import logger


class QualityChecker:
    """Rule-based article quality scorer (0-100)"""

    def check(self, title: str, content_html: str) -> dict:
        """Run full quality check

        Returns:
            {score: int, issues: [str], details: {category: score}}
        """
        issues = []
        details = {}

        title_score, ti = self._check_title(title)
        details["title"] = title_score
        issues.extend(ti)

        content_score, ci = self._check_content(content_html)
        details["content"] = content_score
        issues.extend(ci)

        para_score, pi = self._check_paragraphs(content_html)
        details["paragraphs"] = para_score
        issues.extend(pi)

        read_score, ri = self._check_readability(content_html)
        details["readability"] = read_score
        issues.extend(ri)

        dup_score, di = self._check_duplication(content_html)
        details["duplication"] = dup_score
        issues.extend(di)

        ai_score, ai = self._check_ai_traces(content_html)
        details["ai_traces"] = ai_score
        issues.extend(ai)

        total = title_score + content_score + para_score + read_score + dup_score + ai_score
        total = max(0, min(100, total))

        logger.info("Quality score={} | issues={}", total, len(issues))
        return {"score": total, "issues": issues, "details": details}

    def _check_title(self, title: str) -> tuple:
        score, issues = 20, []
        if not title:
            return 0, ["Title is empty"]
        if len(title) < 5:
            score -= 8; issues.append("Title too short (<5 chars)")
        elif len(title) > 50:
            score -= 5; issues.append("Title too long (>50 chars)")
        emot = title.count("?") + title.count("!") + title.count("！") + title.count("？")
        if emot > 2:
            score -= 3; issues.append("Too many emotional punctuation marks in title")
        return score, issues

    def _check_content(self, html: str) -> tuple:
        score, issues = 25, []
        text = re.sub(r"<[^>]+>", "", html).strip()
        if not text:
            return 0, ["Content is empty"]
        if len(text) < 200:
            score -= 15; issues.append("Content too short (<200 chars)")
        elif len(text) < 500:
            score -= 5; issues.append("Content somewhat short (<500 chars)")
        if "<h2" not in html.lower() and "<h3" not in html.lower():
            score -= 5; issues.append("No subheadings (H2/H3) found")
        if "<blockquote" not in html.lower():
            score -= 2; issues.append("No blockquote for emphasis")
        return score, issues

    def _check_paragraphs(self, html: str) -> tuple:
        score, issues = 20, []
        paras = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL)
        if len(paras) < 2:
            score -= 10; issues.append("Too few paragraphs (<2)")
        else:
            long_count = sum(1 for p in paras if len(re.sub(r"<[^>]+>", "", p)) > 300)
            if long_count:
                score -= 5; issues.append(f"{long_count} paragraph(s) exceed 300 chars")
        return score, issues

    def _check_readability(self, html: str) -> tuple:
        score, issues = 20, []
        text = re.sub(r"<[^>]+>", "", html)
        sentences = re.split(r"[。！？.!?\n]", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            avg = sum(len(s) for s in sentences) / len(sentences)
            if avg > 80:
                score -= 5; issues.append(f"Avg sentence length {avg:.0f} chars (too long)")
        return score, issues

    def _check_duplication(self, html: str) -> tuple:
        score, issues = 10, []
        text = re.sub(r"<[^>]+>", "", html)
        chunks = set()
        dup = 0
        for i in range(0, len(text) - 20, 10):
            ch = text[i:i + 20]
            if len(ch) >= 20:
                if ch in chunks:
                    dup += 1
                chunks.add(ch)
        if dup > 5:
            score -= 5; issues.append(f"{dup} repeated text segments detected")
        return score, issues

    def _check_ai_traces(self, html: str) -> tuple:
        score, issues = 5, []
        text = re.sub(r"<[^>]+>", "", html)
        patterns = [
            ("综上所述", "AI summary marker"),
            ("值得注意的是", "AI filler phrase"),
            ("总而言之", "AI summary marker"),
            ("首先其次最后", "AI structure trace"),
            ("in conclusion", "English AI marker"),
        ]
        for pat, desc in patterns:
            if pat in text:
                score -= 1; issues.append(f"AI trace: {desc}")
        return max(score, 0), issues


quality_checker = QualityChecker()
