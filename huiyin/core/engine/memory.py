"""
回音 - 记忆引擎
管理对话存储、语义索引、用户画像。
Phase 1 实现：基于 SQLite 的全量对话存储与 FTS5。
"""

import json
import sqlite3
from typing import List

from loguru import logger

from config.settings import settings
from core.models import Message, Role


class MemoryEngine:
    """
    Phase 1 简易记忆：SQLite 全量持久化存储。
    包含 FTS5 全文搜索表的自动维护。
    """

    def __init__(self):
        self.db_path = settings.DB_PATH
        self._init_db()

    def _get_conn(self):
        # 使用 check_same_thread=False 并在每个连接内设置适当的 pragma，以防多线程报错
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 原始对话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    channel TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # FTS5 全文搜索虚拟表（预留）
            cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts 
                USING fts5(content, content='messages', content_rowid='id')
            ''')
            
            # 创建触发器，在插入原始数据时自动同步到 FTS5
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
                    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
                END;
            ''')
            conn.commit()
            logger.info(f"💾 记忆引擎已连接至 SQLite: {self.db_path.name}")

    def add(self, message: Message, channel: str = "cli") -> None:
        """记录一条消息到数据库"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO messages (role, content, channel) VALUES (?, ?, ?)",
                (message.role.value, message.content, channel)
            )
            conn.commit()

    def get_context(self, max_recent: int = 50) -> List[Message]:
        """
        获取上下文。
        返回最近 max_recent 条消息作为当前工作区上下文。
        """
        with self._get_conn() as conn:
            cursor = conn.cursor()
            # 先降序查最后 max_recent 条，再在 Python 里反转为时间正序
            cursor.execute(
                "SELECT role, content, timestamp FROM messages ORDER BY id DESC LIMIT ?",
                (max_recent,)
            )
            rows = cursor.fetchall()
            
            messages = []
            from datetime import datetime, timezone
            for r in reversed(rows):
                # SQLite 默认保存的 timestamp 是 string (YYYY-MM-DD HH:MM:SS) 且为 UTC 时区
                dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc).astimezone()
                messages.append(Message(role=Role(r["role"]), content=r["content"], timestamp=dt))
            return messages

    def get_all(self) -> List[Message]:
        """返回全部历史"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role, content, timestamp FROM messages ORDER BY id ASC")
            rows = cursor.fetchall()
            
            messages = []
            from datetime import datetime, timezone
            for r in rows:
                dt = datetime.strptime(r["timestamp"], "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc).astimezone()
                messages.append(Message(role=Role(r["role"]), content=r["content"], timestamp=dt))
            return messages

    def search_history(self, keyword: str, limit: int = 5) -> List[dict]:
        """利用 FTS5 进行全文搜索（供未来的 Skill 或 上下文组装器 使用）"""
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT m.id, m.role, m.content, m.timestamp 
                FROM messages_fts f
                JOIN messages m ON f.rowid = m.id
                WHERE messages_fts MATCH ? 
                ORDER BY rank LIMIT ?
            ''', (keyword, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_user_profile_summary(self) -> str:
        """
        返回用户画像摘要字符串（供注入 system prompt）。
        Phase 2 实现。
        """
        return ""

