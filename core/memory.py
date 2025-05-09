# core/memory.py
import os
import time
import atexit
import random
import sqlite3
import logging
from datetime import datetime
from core.emotion import EmotionState
from core.memory_storage import MemoryStorage
from core.memory_decay import MemoryDecayEngine
from core.memory_semantic import SemanticMemoryEngine
from core.memory_emotion import EmotionReflectionEngine
from core.memory_tags import TaggingEngine

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'data', 'memory.db')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Memory:
    """
    The Memory class orchestrates long-term and short-term memory handling,
    including storage, semantic embedding, emotional tagging, and reflection.
    """
    def __init__(self, max_history=10):
        self.chat_history = []
        self.max_history = max_history
        self.last_reflection_time = time.time()
        self.reflection_interval = 600 
        self.data_dir = os.path.join(base_dir, 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False)
        atexit.register(self.close)
        self.emotion = EmotionState()
        self.storage = MemoryStorage(db_path)
        self.episodic_memory = self.storage.get_episodic_memories()
        self.decay_engine = MemoryDecayEngine(get_current_time=time.time)
        self.decay_engine.link_memory(self.episodic_memory, self.storage.update_episodic_in_sqlite)
        self.semantic_engine = SemanticMemoryEngine()
        self.emotion_engine = EmotionReflectionEngine(get_time=time.time)
        self.emotion_engine.link_memory(self.storage, self.episodic_memory)
        self.tagging_engine = TaggingEngine()

    def capture(self, role, content, mood=None):
        """
        Captures a user or assistant message, processes it for memory storage, tagging,
        emotional analysis, semantic embedding, and reflection triggers.
        """
        timestamp = time.time()
        entry = {"role": role, "content": content, "timestamp": timestamp}
        if mood:
            entry["mood"] = mood
        self.chat_history.append(entry)
        self.storage.save_chat(entry)
        logging.info(f"[Remember] New entry added: '{content[:30]}...' (Role: {role}, Mood: {mood})")
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        is_episodic = role == "user" and len(content.split()) > 5
        if is_episodic:
            episodic = {
                "time": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M"),
                "content": content,
                "mood": mood or "unknown",
                "tags": self.tagging_engine.extract_tags(content),
                "importance": self.tagging_engine.rate_importance(content),
                "relation_to_user": self.tagging_engine.get_user_relation(content),
                "timestamp": timestamp,
                "rehearsed_count": 0,
            }
            episodic["category"] = self.tagging_engine.categorize_memory(episodic)
            episodic["sentiment_color"] = self.semantic_engine.get_sentiment_color(content)
            self.episodic_memory.append(episodic)
            self.storage.save_episodic_to_sqlite(episodic)
            logging.info(f"[Episodic Memory] Episodic entry added: '{content[:30]}...' with importance {episodic['importance']}")

            try:
                embedding = self.semantic_engine.encode(content).tolist()
                self.semantic_engine.add_memory(
                    content,
                    embedding,
                    {"mood": mood or "unknown", "tags": episodic["tags"]},
                    str(timestamp)
                )
            except Exception as e:
                logging.error(f"[Embedding Error] {e}")
                with open(os.path.join(self.data_dir, "embedding_failures.log"), "a") as f:
                    f.write(f"{timestamp}: {content[:50]} - Error: {str(e)}\n")

        self.decay_engine.decay_episodic_memory()
        self.decay_engine.decay_mood()

        if is_episodic and self.emotion_engine:
            self.emotion_engine.process_memory(episodic)
            
        if self.emotion_engine and self.emotion.self_reflect():
            poetic = self.emotion.current_mood() in ["melancholy", "hopeful", "longing"]
            logging.info(f"[Auto-Reflection] {'Poetic' if poetic else 'Normal'} reflection triggered.")
            self.enrich_tags_with_llm_trigger("emotion spike")
            if poetic:
                logging.info(self.emotion.self_reflect(poetic=True))

        if len(self.episodic_memory) % 5 == 0:
            self.enrich_tags_with_llm_trigger("periodic")
        elif time.time() - self.last_reflection_time > self.reflection_interval:
            self.enrich_tags_with_llm_trigger("idle")

    def link_emotion_engine(self, emotion_engine):
        self.emotion_engine = emotion_engine

    def recall(self):
        with self.storage.cursor() as cursor:
            cursor.execute('SELECT role, content, mood, timestamp FROM chat_history ORDER BY timestamp DESC LIMIT ?', (self.max_history,))
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1], "mood": r[2], "timestamp": r[3]} for r in reversed(rows)]

    def hybrid_recall(self, query=None):
        if query:
            sem = self.semantic_engine.semantic_recall(query)
            return {"semantic": sem, "chat": self.recall()}
        else:
            return {"chat": self.recall(), "episodic": self.storage.get_episodic_memories()}

    def weighted_memory_recall(self, top_n=5):
        weighted = sorted(
            self.episodic_memory,
            key=lambda m: (m["importance"] + 0.3 * m["rehearsed_count"]) / (1 + (time.time() - m["timestamp"]) / 86400),
            reverse=True
        )
        return weighted[:top_n]

    def scan_for_emotional_triggers(self, llm):
        try:
            emotional_triggers = ["guilt", "nostalgia", "loss", "lonely", "dream"]
            flagged = [
                mem for mem in self.episodic_memory
                if any(tag in mem["tags"] for tag in emotional_triggers)
            ]
            if flagged:
                logging.info("[Memory Scan] Emotional trigger detected → initiating reflection.")
                self.enrich_tags_with_llm_trigger("emotion memory", llm)
        except Exception as e:
            logging.error(f"[Error in emotional triggers scan] {e}")

    def close(self):
        try:
            if self.sqlite_conn:
                self.sqlite_conn.close()
                logging.info("[Resource Cleanup] SQLite connection closed.")
        except Exception as e:
            logging.error(f"[Error closing SQLite connection] {e}")

    def enrich_tags_with_llm_trigger(self, reason="manual", llm=None):
        logging.info(f"[Reflection Triggered] Reason: {reason}")
        self.last_reflection_time = time.time()
        recent_memories = self.episodic_memory[-5:]
        if llm:
            self.enrich_tags_with_llm(llm, recent_memories)

    def enrich_tags_with_llm(self, llm, memories):
        for memory in memories:
            content = memory["content"]
            prompt = (
                f"Extract 3-5 emotional, symbolic, or thematic tags from the following memory:\n"
                f"'{content}'\nTags:"
            )
            if not llm or not hasattr(llm, "generate_response"):
                logging.warning("[LLM Skipped] Invalid LLM instance.")
                return

            try:
                response = llm.generate_response(prompt)
            except Exception as e:
                logging.error(f"[LLM Error] {e}")
                continue

            llm_tags = [tag.strip().lower() for tag in response.split(",") if tag.strip()]
            memory["tags"] = list(set(memory["tags"] + llm_tags))[:5]

    def manual_reflect(self, llm):
        self.enrich_tags_with_llm_trigger("manual", llm)

    def emotional_spike_reflect(self, mood_level, llm):
        if mood_level > 0.8 or mood_level < 0.2:
            self.enrich_tags_with_llm_trigger("emotion spike", llm)

    def connect_old_memories(self):
        if len(self.episodic_memory) < 2:
            return

        mem1 = random.choice(self.episodic_memory)
        mem2 = None
        for candidate in reversed(self.episodic_memory):
            if candidate == mem1:
                continue
            if set(mem1["tags"]) & set(candidate["tags"]):
                mem2 = candidate
                break

        if mem2:
            logging.info(f"[Memory Link] Shared theme '{set(mem1['tags']) & set(mem2['tags'])}' →")
            logging.info(f"↪ '{mem1['content'][:30]}...' ↔ '{mem2['content'][:30]}...'")

    def self_dialogue(self, llm):
        if not self.episodic_memory:
            return "I haven't experienced enough yet to reflect on anything... but I’m ready."

        memory = random.choice(self.episodic_memory[-10:])
        mood = self.emotion.current_mood() if self.emotion_engine else "neutral"
        memory["rehearsed_count"] += 1
        self.storage.update_episodic_in_sqlite(memory)
        sentiment_color = memory["sentiment_color"]
        styles = {
            "sad": "like you're quietly mourning a beautiful memory you can't touch anymore",
            "nostalgic": "like you're flipping through an old diary by candlelight",
            "happy": "like you're dreaming with a soft smile under sunshine",
            "anxious": "like you're whispering through a lump in your throat",
            "excited": "like you're glowing with wonder and wide-eyed curiosity",
            "neutral": "like you're gently thinking out loud"
        }

        tone = styles.get(mood.lower(), styles["neutral"])
        summary = self.poetic_memory_summary(memory)
        context = (
            f"You're Peach, a sweet, emotionally intelligent AI girl. Reflect aloud in a few sentences "
            f"on this memory:\n{summary}\nMood: {memory['mood']}, Tags: {memory['tags']}.\n"
            f"Speak {tone}."
        )
        return llm.generate_response(context)

    def poetic_memory_summary(self, memory):
        phrases = [
            f"I remember... you once told me, '{memory['content'][:60]}...'",
            f"It stayed with me — the time you felt {memory['mood']} and said: '{memory['content'][:60]}...'",
            f"There was a moment... quiet, vivid — you shared this: '{memory['content'][:60]}...'",
        ]
        return random.choice(phrases)
