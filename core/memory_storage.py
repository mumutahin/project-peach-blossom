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
        self.create_tables()
        self.migrate_tables()

    def create_tables(self):
        with self.cursor() as cursor:
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

    # def migrate_tables(self):
    #     with self.cursor() as cursor:
    #         cursor.execute("PRAGMA user_version")
    #         version = cursor.fetchone()[0]

    #         if version < 1:
    #             cursor.execute("ALTER TABLE episodic_memory ADD COLUMN rehearsed_count INTEGER DEFAULT 0")
    #             cursor.execute("PRAGMA user_version = 1")
    #             logging.info("[Migration] Added 'rehearsed_count' column.")
    #             self.sqlite_conn.commit()

    @contextmanager
    def cursor(self):
        cursor = self.sqlite_conn.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def save_chat_to_sqlite(self, entry):
        with self.cursor() as cursor:
            try:
                cursor.execute('INSERT INTO chat_history (role, content, mood, timestamp) VALUES (?, ?, ?, ?)',
                            (entry.get("role"), entry.get("content"), entry.get("mood"), entry.get("timestamp")))
                self.sqlite_conn.commit()
                logging.info(f"[DB Save] Chat entry saved: '{entry['content'][:30]}...'")
            except Exception as e:
                logging.error(f"[Database Error] {e}")

    def save_episodic_to_sqlite(self, mem):
        with self.cursor() as cursor:
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
        with self.cursor() as cursor:
            cursor.execute('''
                UPDATE episodic_memory
                SET importance = ?, category = ?, rehearsed_count = ?
                WHERE timestamp = ?
            ''', (mem["importance"], mem["category"], mem["rehearsed_count"], mem["timestamp"]))
        self.sqlite_conn.commit()

    def load_memories(self, limit=50):
        with self.cursor() as cursor:
            cursor.execute('SELECT role, content, mood, timestamp FROM chat_history ORDER BY timestamp DESC LIMIT ?', (limit,))
            rows = cursor.fetchall()

        return [
            {
                "role": row[0], "content": row[1], "mood": row[2], "timestamp": row[3]
            }
            for row in rows
        ]

    def delete_memory(self, keyword=None, tag=None, mood=None, timestamp=None, category=None):
        if not keyword and not tag and not mood and not timestamp and not category:
            return
        with self.cursor() as cursor:
            filters = []
            params = []
            if keyword:
                filters.append("content LIKE ?")
                params.append(f"%{keyword}%")
            if tag:
                filters.append("tags LIKE ?")
                params.append(f"%{tag}%")
            if mood:
                filters.append("mood = ?")
                params.append(mood)
            if timestamp:
                filters.append("timestamp = ?")
                params.append(timestamp)
            if category:
                filters.append("category = ?")
                params.append(category)
            
            if filters:
                query = "DELETE FROM episodic_memory WHERE " + " AND ".join(filters)
                cursor.execute(query, tuple(params))
                logging.info(f"[Memory Deletion] Entries deleted based on filter: {filters}")
        
        self.sqlite_conn.commit()

    def cleanup_old_memories(self, older_than_timestamp):
        with self.cursor() as cursor:
            cursor.execute("DELETE FROM episodic_memory WHERE timestamp < ?", (older_than_timestamp,))
            logging.info("[Memory Cleanup] Old memories deleted.")
        self.sqlite_conn.commit()

    def get_episodic_memories(self, limit=20, tag=None, category=None):
        query = 'SELECT time, content, mood, tags, importance, relation, category, timestamp FROM episodic_memory'
        filters = []
        params = []

        if tag:
            filters.append("tags LIKE ?")
            params.append(f"%{tag}%")
        if category:
            filters.append("category = ?")
            params.append(category)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with self.cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()

        return [
            {
                "time": row[0], "content": row[1], "mood": row[2],
                "tags": row[3].split(","), "importance": row[4],
                "relation_to_user": row[5], "category": row[6], "timestamp": row[7]
            }
            for row in rows
        ]
