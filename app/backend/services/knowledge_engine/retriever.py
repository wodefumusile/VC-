"""
Knowledge Retriever — 关键词 + Jaccard 匹配检索器

实现 BaseKnowledgeEngine 接口。
保持简单：关键词分词 + Jaccard 相似度。

v2.1.1: 增加 JSON 文件缓存，增量扫描
"""

import os
import json
import re
from pathlib import Path
from loguru import logger

from .base import BaseKnowledgeEngine, KnowledgeResult, KnowledgeScanResult
from .obsidian_reader import ObsidianReader
from __future__ import annotations


class KeywordJaccardRetriever(BaseKnowledgeEngine):
    """基于关键词分词 + Jaccard 相似度的检索器

    v2.1.1: 使用 .knowledge_cache.json 实现增量扫描。
    首次全量扫描后，后续只读取修改过的文件。
    """

    CACHE_FILENAME = ".knowledge_cache.json"

    def __init__(self, vault_path: str):
        self.vault_path = vault_path
        self.reader = ObsidianReader(vault_path)
        self._documents: list[dict] = []
        self._loaded = False

    @property
    def _cache_path(self) -> Path:
        """缓存文件存储在 vault 根目录"""
        return Path(self.vault_path) / self.CACHE_FILENAME

    def _load_cache(self) -> dict[str, float]:
        """读取缓存文件，返回 {filepath: mtime} 映射"""
        if not self._cache_path.exists():
            return {}
        try:
            with open(self._cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.warning("Knowledge cache corrupted, will rebuild")
            return {}

    def _save_cache(self, file_mtimes: dict[str, float]):
        """保存文件 mtime 到缓存"""
        try:
            with open(self._cache_path, "w", encoding="utf-8") as f:
                json.dump(file_mtimes, f, ensure_ascii=False, indent=2)
            logger.info("Knowledge cache saved | {} entries", len(file_mtimes))
        except Exception as e:
            logger.warning("Failed to save knowledge cache: {}", e)

    def _ensure_loaded(self):
        """增量加载：首次全量扫描，后续只读变更文件"""
        if self._loaded:
            return

        cache = self._load_cache()
        all_files = self.reader.list_files()
        current_mtimes: dict[str, float] = {}

        new_or_changed = []
        unchanged = 0

        for fp in all_files:
            rel = str(fp.relative_to(self.vault_path))
            mtime = fp.stat().st_mtime
            current_mtimes[rel] = mtime

            if rel in cache and cache[rel] == mtime:
                unchanged += 1
            else:
                new_or_changed.append(fp)

        if not cache:
            logger.info("Knowledge cache: cold start, scanning all {} files", len(all_files))
        else:
            logger.info("Knowledge cache: {} cached, {} new/changed",
                        unchanged, len(new_or_changed))

        # Read changed files
        new_docs = []
        for fp in new_or_changed:
            doc = self.reader.read_file(fp)
            if doc and doc.get("content"):
                new_docs.append(doc)

        # Remove deleted files from documents list
        current_paths = set(current_mtimes.keys())
        if cache:
            # Keep docs whose source files still exist
            self._documents = [d for d in self._documents if d.get("source") in current_paths]
            # Add/replace changed docs
            for nd in new_docs:
                # Remove old version of same file
                self._documents = [d for d in self._documents if d.get("source") != nd["source"]]
                self._documents.append(nd)
        else:
            self._documents = new_docs

        # Save updated cache
        self._save_cache(current_mtimes)
        self._loaded = True
        logger.info("Knowledge cache: {} documents loaded", len(self._documents))

    def _tokenize(self, text: str) -> set[str]:
        """中文简单分词 + 英文小写分词"""
        tokens = set()
        cn_chars = re.findall(r"[\u4e00-\u9fff]+", text.lower())
        for seg in cn_chars:
            tokens.update(seg)
            for i in range(len(seg) - 1):
                tokens.add(seg[i:i + 2])
        en_words = re.findall(r"[a-z0-9]{2,}", text.lower())
        tokens.update(en_words)
        return tokens

    def _jaccard(self, set_a: set[str], set_b: set[str]) -> float:
        """Jaccard 相似度: |A ∩ B| / |A ∪ B|"""
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return len(intersection) / len(union) if union else 0.0

    def search(self, query: str, top_k: int = 5) -> list[KnowledgeResult]:
        """关键词检索 — 使用缓存加速"""
        self._ensure_loaded()

        if not self._documents:
            return []

        query_tokens = self._tokenize(query)
        results = []

        for doc in self._documents:
            title_tokens = self._tokenize(doc["title"])
            content_tokens = self._tokenize(doc["content"])

            title_score = self._jaccard(query_tokens, title_tokens)
            content_score = self._jaccard(query_tokens, content_tokens)

            score = title_score * 0.4 + content_score * 0.6
            if score > 0.01:
                results.append(KnowledgeResult(
                    title=doc["title"],
                    content=doc["content"][:2000],
                    source=doc["source"],
                    score=round(score, 4),
                    meta={
                        "tags": doc.get("tags", []),
                        "category": doc.get("category", ""),
                        "char_count": doc.get("char_count", 0),
                    },
                ))

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def scan(self) -> KnowledgeScanResult:
        """扫描知识库概览"""
        self._ensure_loaded()

        categories = {}
        titles = []
        total_chars = 0

        for doc in self._documents:
            cat = doc.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
            if doc.get("title"):
                titles.append(doc["title"])
            total_chars += doc.get("char_count", 0)

        return KnowledgeScanResult(
            total_files=len(self._documents),
            total_chars=total_chars,
            categories=categories,
            sample_titles=titles[:20],
        )

    def invalidate_cache(self):
        """强制下次加载时全量重新扫描"""
        if self._cache_path.exists():
            self._cache_path.unlink()
        self._loaded = False
        self._documents = []
        logger.info("Knowledge cache invalidated")
