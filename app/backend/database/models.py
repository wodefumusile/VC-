"""
Database Module - SQLite article task storage

Tables:
  - articles: Generated article tasks with status tracking
  - task_logs: Operation logs per task
  - article_images (v2.0): AI-generated image records
"""

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from enum import Enum
from loguru import logger
from backend.config import settings


class TaskStatus(str, Enum):
    GENERATED = "GENERATED"
    CHECKING = "CHECKING"
    APPROVED = "APPROVED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class ImageStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    GENERATED = "generated"
    FAILED = "failed"


class Database:
    """SQLite database manager (singleton)"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.ROOT_DIR / "storage" / "articles.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = None
        self._init_db()

    def _init_db(self):
        """Create tables if not exists"""
        self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL UNIQUE,
                topic TEXT NOT NULL,
                title TEXT,
                summary TEXT,
                content_html TEXT,
                seo_keywords TEXT,
                style TEXT DEFAULT 'marketing',
                status TEXT DEFAULT 'GENERATED',
                quality_score INTEGER DEFAULT 0,
                safe_check INTEGER DEFAULT 1,
                error_message TEXT,
                draft_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                published_at TEXT
            );

            CREATE TABLE IF NOT EXISTS task_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                step TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                duration_ms INTEGER,
                created_at TEXT NOT NULL,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );

            CREATE TABLE IF NOT EXISTS article_images (
                id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                image_url TEXT,
                prompt TEXT NOT NULL,
                position INTEGER DEFAULT 0,
                type TEXT DEFAULT 'illustration',
                source_type TEXT DEFAULT 'ai_generated',
                vision_analysis TEXT,
                status TEXT DEFAULT 'pending',
                provider TEXT DEFAULT '',
                task_id TEXT,
                error_message TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );

            CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
            CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at);
            CREATE INDEX IF NOT EXISTS idx_task_logs_article ON task_logs(article_id);
            CREATE INDEX IF NOT EXISTS idx_article_images_article ON article_images(article_id);
        """)
        # --- v2.1 migration: add new columns if missing ---
        try:
            self._conn.execute("ALTER TABLE article_images ADD COLUMN source_type TEXT DEFAULT 'ai_generated'")
        except:
            pass
        try:
            self._conn.execute("ALTER TABLE article_images ADD COLUMN vision_analysis TEXT")
        except:
            pass
        self._conn.commit()

        logger.info("Database initialized | path={} | v2.0 (3 tables)", self.db_path)

    @property
    def conn(self):
        return self._conn

    # --- Article CRUD (v1.0, unchanged) ---

    def create_article(self, topic: str, style: str = "marketing", **kwargs) -> dict:
        article_id = str(uuid.uuid4())[:8]
        task_id = f"TASK-{datetime.now().strftime('%Y%m%d')}-{article_id}"
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO articles (id, task_id, topic, title, summary, content_html,
                seo_keywords, style, status, quality_score, safe_check, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id, task_id, topic,
            kwargs.get("title", ""), kwargs.get("summary", ""),
            kwargs.get("content_html", ""), kwargs.get("seo_keywords", ""),
            style, TaskStatus.GENERATED.value,
            kwargs.get("quality_score", 0), kwargs.get("safe_check", 1),
            now, now,
        ))
        self._conn.commit()
        logger.info("Article created | task_id={} | topic={}", task_id, topic[:30])
        return self.get_article(article_id)

    def get_article(self, article_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM articles WHERE id=?", (article_id,)).fetchone()
        return dict(row) if row else None

    def get_article_by_task_id(self, task_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM articles WHERE task_id=?", (task_id,)).fetchone()
        return dict(row) if row else None

    def list_articles(self, status: str = None, limit: int = 50, offset: int = 0) -> list[dict]:
        if status:
            rows = self._conn.execute(
                "SELECT * FROM articles WHERE status=? ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (status, limit, offset)).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM articles ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (limit, offset)).fetchall()
        return [dict(r) for r in rows]

    def update_article(self, article_id: str, **kwargs) -> dict | None:
        if not kwargs:
            return self.get_article(article_id)
        kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [article_id]
        self._conn.execute(f"UPDATE articles SET {sets} WHERE id=?", values)
        self._conn.commit()
        return self.get_article(article_id)

    def count_by_status(self) -> dict:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM articles GROUP BY status").fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    # --- Task Logs (v1.0, unchanged) ---

    def add_log(self, article_id: str, step: str, status: str, message: str = "", duration_ms: int = 0):
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO task_logs (article_id, step, status, message, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (article_id, step, status, message, duration_ms, now))
        self._conn.commit()

    def get_logs(self, article_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM task_logs WHERE article_id=? ORDER BY created_at ASC",
            (article_id,)).fetchall()
        return [dict(r) for r in rows]

    # --- Article Images (v2.0 new) ---

    def create_image_record(self, article_id: str, prompt: str, position: int = 0,
                            image_type: str = "cover", provider: str = "") -> dict:
        """Create an image generation task record"""
        img_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute("""
            INSERT INTO article_images (id, article_id, prompt, position, type,
                status, provider, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (img_id, article_id, prompt, position, image_type,
              ImageStatus.PENDING.value, provider, now, now))
        self._conn.commit()
        return self.get_image_record(img_id)

    def get_image_record(self, img_id: str) -> dict | None:
        row = self._conn.execute("SELECT * FROM article_images WHERE id=?", (img_id,)).fetchone()
        return dict(row) if row else None

    def get_images_by_article(self, article_id: str) -> list[dict]:
        rows = self._conn.execute(
            "SELECT * FROM article_images WHERE article_id=? ORDER BY position ASC",
            (article_id,)).fetchall()
        return [dict(r) for r in rows]

    def update_image_record(self, img_id: str, **kwargs) -> dict | None:
        if not kwargs:
            return self.get_image_record(img_id)
        kwargs["updated_at"] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [img_id]
        self._conn.execute(f"UPDATE article_images SET {sets} WHERE id=?", values)
        self._conn.commit()
        return self.get_image_record(img_id)

    def count_images_by_status(self, article_id: str) -> dict:
        rows = self._conn.execute(
            "SELECT status, COUNT(*) as cnt FROM article_images WHERE article_id=? GROUP BY status",
            (article_id,)).fetchall()
        return {r["status"]: r["cnt"] for r in rows}


# Global singleton
_db: Database = None


def get_db() -> Database:
    global _db
    if _db is None:
        _db = Database()
    return _db

