# core/memory_emotion.py
import time
import sqlite3
import logging
from datetime import datetime
from collections import defaultdict
from core.memory_storage import DB_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class EmotionReflectionEngine:
    def __init__(self, memory_storage, episodic_memory):
        self.last_reflection_time = time.time()
        self.reflection_interval = 300
        self.memory_storage = memory_storage
        self.episodic_memory = episodic_memory

    def blended_emotion_search(self, primary_mood):
        related_moods = {
            "happy": ["hopeful", "content"],
            "sad": ["lonely", "nostalgic"],
            "anxious": ["nervous", "overwhelmed"],
            "calm": ["peaceful", "relieved"],
            "angry": ["frustrated", "resentful"],
        }
        search_tags = related_moods.get(primary_mood, []) + [primary_mood]
        
        matching = [
            m for m in self.episodic_memory
            if any(tag in m["tags"] or m["mood"] == tag for tag in search_tags)
        ]
        return matching

    def internal_self_talk(self, memories, current_mood):
        if not memories:
            return f"Hmm... nothing really comes to mind right now. Maybe I'm feeling a bit {current_mood} without a clear reason."
        
        thought = f"Thinking about {current_mood} makes me remember...\n"
        for mem in memories:
            thought += f"- {mem['content']} (felt {mem['mood']})\n"
        return thought

    def group_memories_by(self, unit="day"):
        groups = defaultdict(list)
        for mem in self.episodic_memory:
            key = datetime.fromtimestamp(mem["timestamp"]).strftime("%Y-%m-%d" if unit == "day" else "%Y-%m")
            groups[key].append(mem)
        return dict(groups)

    def load_recent_chat_history(self):
        return self.memory_storage.load_memories()

    def narrate_with_mood_tone(self, memories, mood):
        tones = {
            "happy": "It feels so heartwarming to think about these moments!",
            "sad": "Reflecting on these memories feels heavy, yet important...",
            "anxious": "My mind rushes through these memories, uncertain...",
            "calm": "These memories flow through me gently.",
        }
        intro = tones.get(mood, "I drift back to these memories...")
        
        story = intro + "\n\n"
        for mem in memories:
            story += f"• {mem['content']} ({mem['mood']})\n"
        
        return story

    def prioritize_important_memories(self, memories):
        return sorted(memories, key=lambda m: (m['importance'] + m.get('rehearsed_count', 0) * 0.1), reverse=True)

    @staticmethod
    def emotionally_proximal_memories(emotion, tolerance=0.2, limit=5):
        """
        Find memories with emotions *close* to the target emotion, using mood similarity.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT id, emotion, content FROM memories ORDER BY timestamp DESC')
        all_memories = c.fetchall()
        conn.close()

        matches = []
        target_vector = EmotionReflectionEngine.mood_to_vector(emotion)

        for mem_id, mem_emotion, mem_content in all_memories:
            if not mem_emotion:
                continue
            mem_vector = EmotionReflectionEngine.mood_to_vector(mem_emotion)
            similarity = EmotionReflectionEngine.cosine_similarity(target_vector, mem_vector)
            if similarity >= (1 - tolerance):
                matches.append((similarity, mem_content))

        matches.sort(reverse=True)
        return [content for sim, content in matches[:limit]]

    @staticmethod
    def mood_to_vector(mood):
        """
        Rough mapping of moods into 3D vector space (simplified).
        You can refine this later.
        """
        mood_map = {
            "happy": (1, 1, 0),
            "excited": (1, 0.8, 0.2),
            "sad": (-1, -1, 0),
            "angry": (-1, 0, 1),
            "calm": (0.5, 1, -0.5),
            "anxious": (-0.5, -0.8, 0.5),
            # Expand as needed
        }
        return mood_map.get(mood, (0, 0, 0))

    @staticmethod
    def cosine_similarity(v1, v2):
        dot = sum(a*b for a, b in zip(v1, v2))
        norm1 = sum(a*a for a in v1) ** 0.5
        norm2 = sum(b*b for b in v2) ** 0.5
        return dot / (norm1 * norm2 + 1e-6)

    def reflect(self, current_mood):
        """
        Full emotional self-reflection pipeline.
        Should be triggered periodically based on self.reflection_interval.
        """
        emotionally_proximal = self.emotionally_proximal_memories(current_mood)
        raw_memories = self.blended_emotion_search(current_mood)
        all_memories = raw_memories + emotionally_proximal
        important_memories = self.prioritize_important_memories(all_memories)
        self_talk = self.internal_self_talk(important_memories, current_mood)
        narrated_story = self.narrate_with_mood_tone(important_memories, current_mood)
        reflection_output = f"{self_talk}\n\n{narrated_story}"
        return reflection_output
