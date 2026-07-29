import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

class SQLiteFTSManager:
    def __init__(self, db_path: str = "storage/database.sqlite"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        # ⚡ Optimisations SQLite 4 vCPU & Low-RAM (WAL Mode, Cache Cap, Zero-Copy MMAP)
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA cache_size = -16000;")  # Plafond de cache RAM fixé à 16 Mo
        conn.execute("PRAGMA mmap_size = 268435456;") # MMAP 256 Mo pour lectures ultra-rapides sans copie mémoire
        conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Investigations Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investigations (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    summary TEXT
                )
            """)
            
            # Investigation Logs Table (SSE Event Store)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS investigation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investigation_id TEXT NOT NULL,
                    step INTEGER NOT NULL,
                    agent TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata JSON,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (investigation_id) REFERENCES investigations (id)
                )
            """)
            
            # Documents Table for FTS5 Indexing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT,
                    sha256 TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Dead Letter Queue (DLQ) Table for Failed Targets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS failed_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    investigation_id TEXT NOT NULL,
                    target_url TEXT NOT NULL,
                    error_reason TEXT NOT NULL,
                    attempts INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'FAILED',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # SQLite FTS5 Virtual Table for Instant Full-Text Search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                    id UNINDEXED,
                    title,
                    source,
                    content,
                    tokenize = 'porter unicode61'
                )
            """)
            conn.commit()

    def create_investigation(self, inv_id: str, title: str, target: str) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO investigations (id, title, target, status, summary) VALUES (?, ?, ?, ?, ?)",
                (inv_id, title, target, "RUNNING", "Investigation initialisée")
            )
            conn.commit()
            return {"id": inv_id, "title": title, "target": target, "status": "RUNNING"}

    def get_investigations(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investigations ORDER BY updated_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investigations WHERE id = ?", (inv_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_log(self, inv_id: str, step: int, agent: str, action_type: str, content: str, metadata: dict = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO investigation_logs (investigation_id, step, agent, action_type, content, metadata) VALUES (?, ?, ?, ?, ?, ?)",
                (inv_id, step, agent, action_type, content, json.dumps(metadata or {}))
            )
            cursor.execute("UPDATE investigations SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (inv_id,))
            conn.commit()

    def get_logs(self, inv_id: str) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM investigation_logs WHERE investigation_id = ? ORDER BY id ASC", (inv_id,))
            logs = []
            for row in cursor.fetchall():
                item = dict(row)
                if item.get("metadata"):
                    try:
                        item["metadata"] = json.loads(item["metadata"])
                    except Exception:
                        pass
                logs.append(item)
            return logs

    def add_failed_target(self, inv_id: str, target_url: str, error_reason: str, attempts: int = 3):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO failed_targets (investigation_id, target_url, error_reason, attempts) VALUES (?, ?, ?, ?)",
                (inv_id, target_url, error_reason, attempts)
            )
            conn.commit()

    def get_failed_targets(self, inv_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if inv_id:
                cursor.execute("SELECT * FROM failed_targets WHERE investigation_id = ?", (inv_id,))
            else:
                cursor.execute("SELECT * FROM failed_targets ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    def index_document(self, doc_id: str, inv_id: str, title: str, source: str, content: str, url: str = None, sha256: str = None):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO documents (id, investigation_id, title, source, content, url, sha256) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (doc_id, inv_id, title, source, content, url, sha256)
            )
            cursor.execute(
                "INSERT OR REPLACE INTO documents_fts (id, title, source, content) VALUES (?, ?, ?, ?)",
                (doc_id, title, source, content)
            )
            conn.commit()

    def search_documents(self, query: str, inv_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if inv_id:
                cursor.execute("""
                    SELECT d.id, d.investigation_id, d.title, d.source, d.content, d.url, rank
                    FROM documents_fts fts
                    JOIN documents d ON fts.id = d.id
                    WHERE documents_fts MATCH ? AND d.investigation_id = ?
                    ORDER BY rank LIMIT 50
                """, (query, inv_id))
            else:
                cursor.execute("""
                    SELECT d.id, d.investigation_id, d.title, d.source, d.content, d.url, rank
                    FROM documents_fts fts
                    JOIN documents d ON fts.id = d.id
                    WHERE documents_fts MATCH ?
                    ORDER BY rank LIMIT 50
                """, (query,))
            return [dict(row) for row in cursor.fetchall()]
