"""
Knowledge Engine — 知识库抽象层

统一接口，Pipeline 只依赖此接口。
未来可扩展为 Embedding/RAG 实现。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from __future__ import annotations


@dataclass
class KnowledgeResult:
    """单条检索结果"""
    title: str
    content: str
    source: str           # 来源文件路径
    score: float = 1.0    # 匹配得分 (0-1)
    meta: dict = field(default_factory=dict)


@dataclass
class KnowledgeScanResult:
    """知识库扫描结果"""
    total_files: int
    total_chars: int
    categories: dict      # {category: file_count}
    sample_titles: list   # 前 N 个标题


class BaseKnowledgeEngine(ABC):
    """知识库引擎统一接口

    所有实现必须实现 search() 和 scan()。
    Pipeline 只通过此抽象层访问知识库。
    """

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> list[KnowledgeResult]:
        """关键词检索

        Args:
            query: 搜索关键词/句子
            top_k: 返回条数

        Returns:
            匹配的 KnowledgeResult 列表，按 score 降序
        """
        ...

    @abstractmethod
    def scan(self) -> KnowledgeScanResult:
        """扫描知识库概览

        Returns:
            KnowledgeScanResult 包含文件数、总字数、分类统计
        """
        ...
