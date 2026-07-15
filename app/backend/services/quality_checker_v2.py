"""V2 Quality Checker — enhanced pre-publish quality check.

Checks content, images, and HTML structure before publishing.
Independent from v1.0 quality_checker.
"""

import re
from loguru import logger


class QualityCheckerV2:
    """Enhanced quality checker for v2.0 pipeline.

    Checks:
    - Content: title quality, word count, structure
    - Images: cover presence, generation status
    - HTML: tag completeness, WeChat compatibility
    """

    def check(self, title: str, content_html: str,
              images: list[dict] = None) -> dict:
        """Run full quality check.

        Args:
            title: Article title
            content_html: Formatted HTML content
            images: Optional image records from DB

        Returns:
            {score: int, status: "pass"|"warn"|"fail", issues: [...]}
        """
        issues = []
        scores = {}

        # Content checks
        title_ok, title_issues = self._check_title(title)
        scores["title"] = title_ok
        issues.extend(title_issues)

        word_ok, word_issues = self._check_word_count(content_html)
        scores["word_count"] = word_ok
        issues.extend(word_issues)

        struct_ok, struct_issues = self._check_structure(content_html)
        scores["structure"] = struct_ok
        issues.extend(struct_issues)

        # Image checks
        img_ok, img_issues = self._check_images(images or [])
        scores["images"] = img_ok
        issues.extend(img_issues)

        # HTML checks
        html_ok, html_issues = self._check_html(content_html)
        scores["html"] = html_ok
        issues.extend(html_issues)

        # Calculate total score
        total = sum(scores.values())
        max_score = len(scores) * 30  # each dimension max 30
        score = max(0, min(100, int((total / max_score) * 100))) if max_score > 0 else 0

        # Determine status
        if score >= 80 and not any(i.get("severity") == "error" for i in issues):
            status = "pass"
        elif score >= 60:
            status = "warn"
        else:
            status = "fail"

        logger.info("QualityCheckV2 | score={} status={} issues={}", score, status, len(issues))
        return {"score": score, "status": status, "issues": issues}

    def _check_title(self, title: str) -> tuple:
        score, issues = 30, []
        if not title:
            return 0, [{"type": "title", "severity": "error", "message": "Title is empty"}]
        if len(title) < 5:
            score -= 10
            issues.append({"type": "title", "severity": "warn", "message": "Title too short (<5 chars)"})
        elif len(title) > 64:
            score -= 5
            issues.append({"type": "title", "severity": "warn", "message": "Title truncated (>64 chars)"})
        return score, issues

    def _check_word_count(self, html: str) -> tuple:
        score, issues = 30, []
        text = re.sub(r"<[^>]+>", "", html).strip()
        count = len(text)
        if count < 200:
            score -= 15
            issues.append({"type": "content", "severity": "error", "message": f"Content too short ({count} chars, min 200)"})
        elif count < 500:
            score -= 5
            issues.append({"type": "content", "severity": "warn", "message": f"Content somewhat short ({count} chars)"})
        return score, issues

    def _check_structure(self, html: str) -> tuple:
        score, issues = 30, []
        has_h2 = "<h2" in html.lower() or "border-left:3px solid" in html
        has_p = "<p" in html.lower() or "margin-bottom:12px" in html
        if not has_h2:
            score -= 8
            issues.append({"type": "structure", "severity": "warn", "message": "No subheadings found"})
        if not has_p:
            score -= 8
            issues.append({"type": "structure", "severity": "error", "message": "No paragraphs found"})
        return score, issues

    def _check_images(self, images: list[dict]) -> tuple:
        score, issues = 30, []
        if not images:
            return 20, [{"type": "image", "severity": "warn", "message": "No images generated"}]

        has_cover = any(r.get("type") == "cover" and r.get("image_url") for r in images)
        failed = [r for r in images if r.get("status") == "failed"]
        generated = [r for r in images if r.get("image_url")]

        if not has_cover:
            score -= 10
            issues.append({"type": "image", "severity": "warn", "message": "No cover image"})
        if failed:
            score -= 10
            issues.append({"type": "image", "severity": "warn", "message": f"{len(failed)} image(s) failed to generate"})
        if not generated:
            score -= 10
            issues.append({"type": "image", "severity": "warn", "message": "No images successfully generated"})
        return score, issues

    def _check_html(self, html: str) -> tuple:
        score, issues = 30, []
        # Check tag balance
        open_p = len(re.findall(r"<p[ >]", html))
        close_p = len(re.findall(r"</p>", html))
        if open_p != close_p:
            score -= 10
            issues.append({"type": "html", "severity": "error", "message": f"Unbalanced <p> tags (open={open_p}, close={close_p})"})

        # Check for forbidden style-on-block patterns
        if re.search(r'<(h[1-3]|p|blockquote)\s[^>]*style=', html):
            score -= 5
            issues.append({"type": "html", "severity": "warn", "message": "Style on block elements detected (WeChat may strip these)"})

        # Check for section+span pattern (good sign)
        if "<section" in html and "<span" in html:
            score = min(30, score + 5)

        return score, issues


quality_checker_v2 = QualityCheckerV2()
