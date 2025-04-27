# core/memory_emotion.py
import time
import logging
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class EmotionReflectionEngine:
    def __init__(self, memory_storage, episodic_memory):
        self.emotion_engine = None
        self.last_reflection_time = time.time()
        self.reflection_interval = 300
        self.memory_storage = memory_storage
        self.episodic_memory = episodic_memory

    def emotionally_similar_memories(self, current_mood):
        return [
            m for m in self.episodic_memory
            if m["mood"] == current_mood or current_mood in m["tags"]
        ]

    def group_memories_by(self, unit="day"):
        groups = defaultdict(list)
        for mem in self.episodic_memory:
            key = datetime.fromtimestamp(mem["timestamp"]).strftime("%Y-%m-%d" if unit == "day" else "%Y-%m")
            groups[key].append(mem)
        return dict(groups)

    def load_recent_chat_history(self):
        return self.memory_storage.load_memories()
