"""
Obsidian Markdown Reader — 读取 Obsidian vault 的 Markdown 文件池

支持:
- 递归扫描 vault 目录
- 解析 YAML front matter（标题、标签）
- 提取纯文本内容（去 Markdown 标记）
"""

import os
import re
from pathlib import Path
from typing import Optional
from loguru import logger


class ObsidianReader:
    """Obsidian Vault Markdown 读取器"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        if not self.vault_path.exists():
            raise FileNotFoundError(f"Vault path not found: {vault_path}")

    def list_files(self) -> list[Path]:
        """递归列出所有 .md 文件（排除隐藏目录和模板）"""
        files = []
        for root, dirs, filenames in os.walk(self.vault_path):
            # 跳过隐藏目录和 .obsidian 目录
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != ".obsidian" and d != "_templates"]
            for f in filenames:
                if f.endswith(".md"):
                    files.append(Path(root) / f)
        return files

    def parse_front_matter(self, content: str) -> dict:
        """解析 YAML front matter

        Returns:
            {title: str, tags: [str], category: str}
        """
        meta = {"title": "", "tags": [], "category": ""}
        fm_match = re.match(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
        if not fm_match:
            return meta

        fm_text = fm_match.group(1)
        for line in fm_text.split("\n"):
            line = line.strip()
            if line.startswith("title:"):
                meta["title"] = line.replace("title:", "").strip().strip("\"'")
            elif line.startswith("tags:"):
                tag_str = line.replace("tags:", "").strip()
                if tag_str.startswith("[") and tag_str.endswith("]"):
                    meta["tags"] = [t.strip().strip("\"'") for t in tag_str[1:-1].split(",") if t.strip()]
                else:
                    meta["tags"] = [t.strip() for t in tag_str.split(",") if t.strip()]
            elif line.startswith("category:"):
                meta["category"] = line.replace("category:", "").strip().strip("\"'")
        return meta

    def strip_markdown(self, content: str) -> str:
        """去除 Markdown 标记，提取纯文本"""
        # 移除 front matter
        content = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)
        # 移除代码块
        content = re.sub(r"```.*?```", " ", content, flags=re.DOTALL)
        # 移除图片
        content = re.sub(r"!\[.*?\]\(.*?\)", " ", content)
        # 移除链接，保留文字
        content = re.sub(r"\[([^\]]*)\]\(.*?\)", r"\1", content)
        # 移除标题标记
        content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)
        # 移除粗体/斜体
        content = re.sub(r"\*{1,3}(.*?)\*{1,3}", r"\1", content)
        # 移除列表标记
        content = re.sub(r"^[\s]*[-*+]\s+", "", content, flags=re.MULTILINE)
        # 移除行内代码
        content = re.sub(r"`([^`]*)`", r"\1", content)
        # 移除多余空白
        content = re.sub(r"\n{3,}", "\n\n", content)
        content = re.sub(r" {2,}", " ", content)
        return content.strip()

    def read_file(self, file_path: Path) -> Optional[dict]:
        """读取单个 Markdown 文件

        Returns:
            {title, content, tags, category, source} or None
        """
        try:
            raw = file_path.read_text(encoding="utf-8")
            meta = self.parse_front_matter(raw)
            text = self.strip_markdown(raw)

            title = meta.get("title") or file_path.stem
            category = meta.get("category") or file_path.parent.name

            return {
                "title": title,
                "content": text,
                "tags": meta.get("tags", []),
                "category": category,
                "source": str(file_path.relative_to(self.vault_path)),
                "char_count": len(text),
            }
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return None

    def read_all(self) -> list[dict]:
        """读取整个 vault 的所有 Markdown 文件"""
        files = self.list_files()
        logger.info(f"ObsidianReader: scanning {len(files)} .md files in {self.vault_path}")
        docs = []
        for fp in files:
            doc = self.read_file(fp)
            if doc and doc["content"]:
                docs.append(doc)
        logger.info(f"ObsidianReader: loaded {len(docs)} valid documents")
        return docs
