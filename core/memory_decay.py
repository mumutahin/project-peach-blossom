# core/memory_decay.py
import sqlite3
import time
import logging
from core.memory_storage import DB_PATH
from core.memory_storage import MemoryStorage
from core.memory_emotion import EmotionReflectionEngine
from core.memory_tags import TaggingEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

DECAY_RATES = {
    "happy": 0.01,
    "excited": 0.015,
    "calm": 0.02,
    "sad": 0.03,
    "angry": 0.04,
    "anxious": 0.05,
    # Add more if needed
}

class MemoryDecayEngine:
    def __init__(self, tag: TaggingEngine):
        self.tag = tag
        self.storage = MemoryStorage(DB_PATH)
        self.episodic_memory = self.storage.get_episodic_memories()
        self.emotion_engine = EmotionReflectionEngine(self.storage, self.episodic_memory)
        self.emotion_engine.link_memory(self.storage, self.episodic_memory)

    def link_memory(self, episodic_memory, update_func):
        self.episodic_memory = episodic_memory
        self.update_episodic_in_sqlite = update_func

    def decay_episodic_memory(self, decay_half_life=86400, min_importance=0.1):
        """
        Decays episodic memory over time using exponential decay.
        Half-life defines how long it takes for a memory's importance to drop by half.
        """
        now = time.time()
        decay_factor = lambda elapsed: 0.5 ** (elapsed / decay_half_life)
        updated = []

        for mem in self.episodic_memory:
            elapsed = now - mem["timestamp"]
            base_decay = decay_factor(elapsed)

            if mem["mood"] in ["happy", "hopeful", "excited"]:
                base_decay *= 0.85
            elif mem["mood"] in ["sad", "angry", "anxious"]:
                base_decay *= 1.15
            else:
                base_decay *= 1.0

            old = mem["importance"]
            mem["importance"] *= base_decay

            logging.info(f"[Decay] '{mem['content'][:30]}...' from {old:.2f} to {mem['importance']:.2f}")

            new_cat = self.tag.categorize_memory(mem)
            if new_cat != mem["category"]:
                mem["category"] = new_cat

            if mem["importance"] >= min_importance:
                updated.append(mem)
                self.update_episodic_in_sqlite(mem)

        self.episodic_memory = updated

    def decay_mood(self, decay_half_life=86400, min_mood_intensity=0.1):
        """
        Decays mood intensity of memories over time using exponential decay.
        Half-life defines how long it takes for a memory's mood to drop by half.
        """
        now = time.time()
        decay_factor = lambda elapsed: 0.5 ** (elapsed / decay_half_life)
        updated = []
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT timestamp, mood FROM episodic_memory WHERE mood IS NOT NULL')
        memories = c.fetchall()

        for ts, mood in memories:
            elapsed = now - ts
            base_decay = decay_factor(elapsed)

            if mood in ["happy", "excited", "hopeful"]:
                base_decay *= 0.85
            elif mood in ["sad", "angry", "anxious"]:
                base_decay *= 1.15
            else:
                base_decay *= 1.0

            new_intensity = max(min_mood_intensity, 1.0 * base_decay)
            c.execute('UPDATE episodic_memory SET mood = ? WHERE timestamp = ?', (new_intensity, ts))
            updated.append((ts, new_intensity))
            
        conn.commit()
        conn.close()

    def reinforce_important_memories(self, boost_amount=0.2):
        """
        Periodically rehearse important memories to strengthen their importance score.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT timestamp, importance FROM episodic_memory WHERE importance > 0.3')
        memories = c.fetchall()

        for mem_id, importance in memories:
            new_importance = min(1.0, importance + boost_amount)
            c.execute('UPDATE episodic_memory SET importance = ? WHERE timestamp = ?', (new_importance, mem_id))

        conn.commit()
        conn.close()

    def decay_memory_importance(self):
        """
        Gradually reduce importance of memories based on mood.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT timestamp, importance, mood FROM episodic_memory')
        memories = c.fetchall()

        for ts, importance, mood in memories:
            decay = DECAY_RATES.get(mood, 0.03)  # Default decay
            new_importance = max(0, importance - decay)
            c.execute('UPDATE episodic_memory SET importance = ? WHERE timestamp = ?', (new_importance, ts))

        conn.commit()
        conn.close()
