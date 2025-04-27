# core/memory_storage.py
import os
import sqlite3
import logging
from contextlib import contextmanager

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'data', 'memory.db')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MemoryStorage:
    def __init__(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
        self._migrate_tables()

    def _create_tables(self):
        with self._cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    role TEXT, content TEXT, mood TEXT, timestamp REAL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    time TEXT, content TEXT, mood TEXT, tags TEXT,
                    importance REAL, relation TEXT, category TEXT,
                    timestamp REAL, rehearsed_count INTEGER DEFAULT 0
                )
            ''')
        self.sqlite_conn.commit()

    def _migrate_tables(self):
        with self._cursor() as cursor:
            cursor.execute("PRAGMA user_version")
            version = cursor.fetchone()[0]

            if version < 1:
                cursor.execute("ALTER TABLE episodic_memory ADD COLUMN rehearsed_count INTEGER DEFAULT 0")
                cursor.execute("PRAGMA user_version = 1")
                logging.info("[Migration] Added 'rehearsed_count' column.")
                self.sqlite_conn.commit()

    @contextmanager
    def _cursor(self):
        cursor = self.sqlite_conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def _save_chat_to_sqlite(self, entry):
        with self._cursor() as cursor:
            try:
                cursor.execute('INSERT INTO chat_history (role, content, mood, timestamp) VALUES (?, ?, ?, ?)',
                            (entry["role"], entry["content"], entry.get("mood"), entry["timestamp"]))
                self.sqlite_conn.commit()
                logging.info(f"[DB Save] Chat entry saved: '{entry['content'][:30]}...'")
            except Exception as e:
                logging.error(f"[Database Error] {e}")
            
    def save_episodic_to_sqlite(self, mem):
        with self._cursor() as cursor:
            try:
                cursor.execute('INSERT INTO episodic_memory VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                            (mem["time"], mem["content"], mem["mood"],
                                ",".join(mem["tags"]), mem["importance"],
                                mem["relation_to_user"], mem["category"],
                                mem["timestamp"], mem.get("rehearsed_count", 0)))
                self.sqlite_conn.commit()
                logging.info(f"[DB Save] Episodic memory saved: '{mem['content'][:30]}...'")
            except Exception as e:
                logging.error(f"[Database Error] {e}")

    def update_episodic_in_sqlite(self, mem):
        with self._cursor() as cursor:
            cursor.execute('''
                UPDATE episodic_memory
                SET importance = ?, category = ?, rehearsed_count = ?
                WHERE timestamp = ?
            ''', (mem["importance"], mem["category"], mem["rehearsed_count"], mem["timestamp"]))
        self.sqlite_conn.commit()

    def delete_memory(self, keyword=None, tag=None):
        if not keyword and not tag:
            return
        with self._cursor() as cursor:
            if keyword:
                cursor.execute("DELETE FROM episodic_memory WHERE content LIKE ?", (f"%{keyword}%",))
            elif tag:
                cursor.execute("DELETE FROM episodic_memory WHERE tags LIKE ?", (f"%{tag}%",))
        self.sqlite_conn.commit()
        logging.info("[Memory Deletion] Entries deleted based on filter.")

    def get_episodic_memories(self):
        with self._cursor() as cursor:
            cursor.execute('SELECT time, content, mood, tags, importance, relation, category, timestamp FROM episodic_memory ORDER BY timestamp DESC LIMIT 20')
        rows = cursor.fetchall()
        return [
            {
                "time": row[0], "content": row[1], "mood": row[2],
                "tags": row[3].split(","), "importance": row[4],
                "relation_to_user": row[5], "category": row[6], "timestamp": row[7]
            }
            for row in rows
        ]
