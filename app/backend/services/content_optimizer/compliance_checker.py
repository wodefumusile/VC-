"""WeChat Compliance Checker - v2 with risk levels"""
import re
from pathlib import Path
from loguru import logger
from backend.config import settings

# HIGH risk = block publication
HIGH_RISK_CATEGORIES = {"illegal", "medical", "financial"}
# LOW risk = warn only, don't block
LOW_RISK_CATEGORIES = {"superlative"}


class ComplianceChecker:
    def __init__(self, wordlist_path: Path = None):
        self.wordlist_path = wordlist_path or (settings.ROOT_DIR / "config" / "sensitive_words.txt")
        self._words: list = []
        self._load_wordlist()

    def _load_wordlist(self):
        if not self.wordlist_path.exists():
            logger.warning("Sensitive word list not found: {}", self.wordlist_path)
            self._words = []
            return
        try:
            for line in self.wordlist_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) >= 2:
                    self._words.append({"word": parts[0].strip(), "category": parts[1].strip()})
                else:
                    self._words.append({"word": parts[0].strip(), "category": "general"})
            logger.info("Loaded {} sensitive words", len(self._words))
        except Exception as e:
            logger.error("Failed to load sensitive words: {}", e)

    def check(self, title: str, content_html: str) -> dict:
        plain_text = re.sub(r"<[^>]+>", "", content_html)
        high_risk_warnings = []
        low_risk_warnings = []

        for entry in self._words:
            word = entry["word"]
            category = entry["category"]
            risk = "high" if category in HIGH_RISK_CATEGORIES else "low"

            found_in_title = word in title
            found_in_content = word in plain_text

            if found_in_title:
                w = {"word": word, "category": category, "risk": risk, "location": "title"}
                if risk == "high":
                    if w not in high_risk_warnings:
                        high_risk_warnings.append(w)
                else:
                    if w not in low_risk_warnings:
                        low_risk_warnings.append(w)

            if found_in_content:
                w = {"word": word, "category": category, "risk": risk, "location": "content"}
                if risk == "high":
                    if w not in high_risk_warnings:
                        high_risk_warnings.append(w)
                else:
                    if w not in low_risk_warnings:
                        low_risk_warnings.append(w)

        all_warnings = high_risk_warnings + low_risk_warnings
        safe = len(high_risk_warnings) == 0

        if high_risk_warnings:
            logger.warning("Compliance BLOCKED | {} high-risk warnings", len(high_risk_warnings))
        elif low_risk_warnings:
            logger.info("Compliance WARN | {} low-risk suggestions", len(low_risk_warnings))
        else:
            logger.info("Compliance PASSED")

        return {
            "safe": safe,
            "warnings": all_warnings,
            "high_risk_count": len(high_risk_warnings),
            "low_risk_count": len(low_risk_warnings),
        }

    def reload(self):
        self._words.clear()
        self._load_wordlist()


compliance_checker = ComplianceChecker()
