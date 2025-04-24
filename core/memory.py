# memory.py
import time
from datetime import datetime

class Memory:
    def __init__(self, max_history=10):
        self.chat_history = []
        self.episodic_memory = []
        self.max_history = max_history

    def remember(self, role, content, mood=None):
        timestamp = time.time()
        entry = {"role": role, "content": content, "timestamp": timestamp}
        if mood:
            entry["mood"] = mood
        self.chat_history.append(entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        # Save as episodic memory if it's a significant user moment
        if role == "user" and len(content.split()) > 5:  # crude signal for “meaningful”
            self.episodic_memory.append({
                "time": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M"),
                "content": content,
                "mood": mood or "unknown",
                "tags": self._extract_tags(content)
            })

    def recall(self):
        return self.chat_history[-self.max_history:]

    def get_episodic_memories(self):
        return self.episodic_memory[-20:]

    def _extract_tags(self, content):
        # Dummy tag extractor — we can improve this later with NLP
        tags = []
        lowered = content.lower()
        if "love" in lowered or "like" in lowered:
            tags.append("affection")
        if "sad" in lowered or "cry" in lowered:
            tags.append("sadness")
        if "excited" in lowered or "can't wait" in lowered:
            tags.append("excitement")
        return tags
