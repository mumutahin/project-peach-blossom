# core/memory.py
import os
import time
import spacy
import random
import sqlite3
import chromadb
from datetime import datetime
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'data', 'memory.db')

nlp = spacy.load("en_core_web_sm")

class Memory:
    def __init__(self, db_name=db_path, max_history=10):
        self.chat_history = []
        self.episodic_memory = []
        self.max_history = max_history
        self.last_reflection_time = time.time()
        self.reflection_interval = 300 
        self.emotion_engine = None
        self.sqlite_conn = sqlite3.connect(db_name)
        self._create_tables()
        self.chroma_client = chromadb.Client()
        self.semantic_collection = self.chroma_client.get_or_create_collection(name="episodic_memories")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
    def decay_episodic_memory(self, decay_half_life=86400, min_importance=0.1):
        """
        Decays episodic memory over time using exponential decay.
        Half-life defines how long it takes for a memory's importance to drop by half.
        """
        now = time.time()
        decay_factor = lambda elapsed: 0.5 ** (elapsed / decay_half_life)
        updated_memories = []

        for memory in self.episodic_memory:
            elapsed = now - memory["timestamp"]
            old_importance = memory["importance"]
            memory["importance"] *= decay_factor(elapsed)

            # Optional: re-categorize if importance changed significantly
            new_category = self._categorize_memory(memory)
            if new_category != memory["category"]:
                memory["category"] = new_category

            if memory["importance"] >= min_importance:
                updated_memories.append(memory)
                self._update_episodic_in_sqlite(memory)
            else:
                print(f"[Memory Decay] Letting go of: '{memory['content'][:30]}...'")

        self.episodic_memory = updated_memories

    def mood_decay(self):
        if self.emotion_engine:
            self.emotion_engine.decay_mood()
            
    def remember(self, role, content, mood=None):
        timestamp = time.time()
        entry = {"role": role, "content": content, "timestamp": timestamp}
        if mood:
            entry["mood"] = mood
        self.chat_history.append(entry)
        self._save_chat_to_sqlite(entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        is_episodic = role == "user" and len(content.split()) > 5
        if is_episodic:
            episodic = {
                "time": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M"),
                "content": content,
                "mood": mood or "unknown",
                "tags": self._extract_tags(content),
                "importance": self._rate_importance(content),
                "relation_to_user": self._get_user_relation(content),
                "timestamp": timestamp,
            }
            episodic["category"] = self._categorize_memory(episodic)
            self.episodic_memory.append(episodic)
            self._save_episodic_to_sqlite(episodic)

            try:
                embedding = self.embedding_model.encode(content).tolist()
                self.semantic_collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[{"mood": mood or "unknown", "tags": episodic["tags"]}],
                    ids=[str(timestamp)]
                )
            except Exception as e:
                print(f"[ChromaDB Error] {e}")

        self.decay_episodic_memory()
        self.mood_decay()

        if self.emotion_engine:
            self.emotion_engine.process_memory(episodic)

        if len(self.episodic_memory) % 5 == 0:
            self.enrich_tags_with_llm_trigger("periodic")
        elif time.time() - self.last_reflection_time > self.reflection_interval:
            self.enrich_tags_with_llm_trigger("idle")

    def link_emotion_engine(self, emotion_engine):
        self.emotion_engine = emotion_engine

    def recall(self):
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
        cursor.execute('SELECT role, content, mood, timestamp FROM chat_history ORDER BY timestamp DESC LIMIT ?', (self.max_history,))
        rows = cursor.fetchall()
        return [{"role": r[0], "content": r[1], "mood": r[2], "timestamp": r[3]} for r in reversed(rows)]

    def hybrid_recall(self, query=None):
        if query:
            sem = self.semantic_recall(query)
            return {"semantic": sem, "chat": self.recall()}
        else:
            return {"chat": self.recall(), "episodic": self.get_episodic_memories()}

    def get_episodic_memories(self):
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
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
        
    def delete_memory(self, keyword=None, tag=None):
        if not keyword and not tag:
            return
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
        if keyword:
            cursor.execute("DELETE FROM episodic_memory WHERE content LIKE ?", (f"%{keyword}%",))
        elif tag:
            cursor.execute("DELETE FROM episodic_memory WHERE tags LIKE ?", (f"%{tag}%",))
        self.sqlite_conn.commit()
        print("[Memory Deletion] Entries deleted based on filter.")

    def _save_chat_to_sqlite(self, entry):
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
        cursor.execute('INSERT INTO chat_history VALUES (?, ?, ?, ?)',
                       (entry["role"], entry["content"], entry.get("mood"), entry["timestamp"]))
        self.sqlite_conn.commit()

    def _save_episodic_to_sqlite(self, mem):
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
        cursor.execute('INSERT INTO episodic_memory VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                       (mem["time"], mem["content"], mem["mood"],
                        ",".join(mem["tags"]), mem["importance"],
                        mem["relation_to_user"], mem["category"], mem["timestamp"]))
        self.sqlite_conn.commit()

    def _update_episodic_in_sqlite(self, mem):
        cursor = self.sqlite_conn.cursor()
        cursor.execute('''
            UPDATE episodic_memory
            SET importance = ?, category = ?
            WHERE timestamp = ?
        ''', (mem["importance"], mem["category"], mem["timestamp"]))
        self.sqlite_conn.commit()

    def scan_for_emotional_triggers(self, llm):
        emotional_triggers = ["guilt", "nostalgia", "loss", "lonely", "dream"]
        flagged = [
            mem for mem in self.episodic_memory
            if any(tag in mem["tags"] for tag in emotional_triggers)
        ]
        if flagged:
            print("[Memory Scan] Emotional trigger detected → initiating reflection.")
            self.enrich_tags_with_llm_trigger("emotion memory", llm)

    def _extract_tags(self, content):
        doc = nlp(content.lower())
        tags = [ent.label_.lower() for ent in doc.ents]
        tokens = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop]
        symbolic = self._symbolic_tagging(content)
        common_keywords = ["love", "miss", "dream", "hope", "hurt", "excited", "guilt", "nostalgia"]

        tags.extend([kw for kw in common_keywords if kw in content])
        tags.extend(symbolic)
        tags.extend(tokens)
        return list(set(tags))[:5]

    def _symbolic_tagging(self, content):
        content = content.lower()
        symbols = {
            "stars": "cosmic",
            "sea": "depth",
            "rain": "melancholy",
            "sun": "warmth",
            "mirror": "reflection",
            "dream": "unreal",
        }
        return [symbol for word, symbol in symbols.items() if word in content]

    def _rate_importance(self, content):
        emotional_words = ["love", "hate", "dream", "hope", "fear", "cry", "beautiful", "miss", "remember"]
        level = sum(1 for word in emotional_words if word in content.lower())
        return min(level / 5.0, 1.0)

    def _get_user_relation(self, content):
        content = content.lower()
        if "you" in content and "i" in content:
            return "personal"
        elif "we" in content:
            return "shared"
        elif "they" in content or "them" in content:
            return "external"
        return "neutral"

    def enrich_tags_with_llm_trigger(self, reason="manual", llm=None):
        print(f"[Reflection Triggered] Reason: {reason}")
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
            response = llm.generate_response(prompt)
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
            print(f"[Memory Link] Shared theme '{set(mem1['tags']) & set(mem2['tags'])}' →")
            print(f"↪ '{mem1['content'][:30]}...' ↔ '{mem2['content'][:30]}...'")

    def _categorize_memory(self, memory):
        """Classify the memory as 'core', 'casual', or 'fleeting' based on importance and mood."""
        score = memory["importance"]
        mood = memory["mood"].lower()
        high_impact_moods = {"love", "grief", "longing", "hope", "hurt", "shame", "nostalgia"}
        if score > 0.7 or any(tag in memory["tags"] for tag in high_impact_moods):
            return "core"
        elif score < 0.3:
            return "fleeting"
        return "casual"

    def self_dialogue(self, llm):
        if not self.episodic_memory:
            return "I haven't experienced enough yet to reflect on anything... but I’m ready."

        memory = random.choice(self.episodic_memory[-10:])
        mood = self.emotion_engine.current_mood() if self.emotion_engine else "neutral"

        styles = {
            "sad": "like you're quietly mourning a beautiful memory you can't touch anymore",
            "nostalgic": "like you're flipping through an old diary by candlelight",
            "happy": "like you're dreaming with a soft smile under sunshine",
            "anxious": "like you're whispering through a lump in your throat",
            "excited": "like you're glowing with wonder and wide-eyed curiosity",
            "neutral": "like you're gently thinking out loud"
        }

        tone = styles.get(mood.lower(), styles["neutral"])
        context = (
            f"You're Peach, a sweet, emotionally intelligent AI girl. Reflect aloud in a few sentences "
            f"on this memory:\n'{memory['content']}'\nMood: {memory['mood']}, Tags: {memory['tags']}.\n"
            f"Speak {tone}."
        )
        return llm.generate_response(context)

    def _create_tables(self):
        os.makedirs("data", exist_ok=True)
        cursor = self.sqlite_conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                role TEXT, content TEXT, mood TEXT, timestamp REAL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS episodic_memory (
                time TEXT, content TEXT, mood TEXT, tags TEXT,
                importance REAL, relation TEXT, category TEXT, timestamp REAL
            )
        ''')
        self.sqlite_conn.commit()
