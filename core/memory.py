# core/memory.py
import time
import spacy
import random
from datetime import datetime

nlp = spacy.load("en_core_web_sm")

class Memory:
    def __init__(self, max_history=10):
        self.chat_history = []
        self.episodic_memory = []
        self.max_history = max_history
        self.last_reflection_time = time.time()
        self.reflection_interval = 300

    def remember(self, role, content, mood=None):
        timestamp = time.time()
        entry = {"role": role, "content": content, "timestamp": timestamp}
        if mood:
            entry["mood"] = mood
        self.chat_history.append(entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        if role == "user" and len(content.split()) > 5:
            episodic = {
                "time": datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M"),
                "content": content,
                "mood": mood or "unknown",
                "tags": self._extract_tags(content)
            }
            self.episodic_memory.append(episodic)

            # Natural triggers for reflection
            if len(self.episodic_memory) % 5 == 0:
                self.enrich_tags_with_llm_trigger("periodic")
            elif time.time() - self.last_reflection_time > self.reflection_interval:
                self.enrich_tags_with_llm_trigger("idle")

    def recall(self):
        return self.chat_history[-self.max_history:]

    def get_episodic_memories(self):
        return self.episodic_memory[-20:]

    def _extract_tags(self, content):
        doc = nlp(content.lower())
        tags = [ent.label_.lower() for ent in doc.ents]  # e.g., "person", "event"
        tokens = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop]
        common_keywords = ["love", "miss", "dream", "hope", "hurt", "excited"]
        if any(kw in content.lower() for kw in common_keywords):
            tags.extend([kw for kw in common_keywords if kw in content.lower()])
        return list(set(tags))[:5]

    def enrich_tags_with_llm(self, llm):
        for memory in self.episodic_memory:
            content = memory["content"]
            prompt = f"Extract 3 to 5 emotional or thematic tags from this memory: '{content}'\nTags:"
            response = llm.generate_response(prompt)
            llm_tags = [tag.strip().lower() for tag in response.split(',') if tag.strip()]
            memory["tags"] = list(set(memory["tags"] + llm_tags))[:5]

    def enrich_tags_with_llm_trigger(self, reason="manual", llm=None):
        print(f"[Reflection Triggered] Reason: {reason}")
        self.last_reflection_time = time.time()
        recent_memories = self.episodic_memory[-5:]
        if llm:
            self.enrich_tags_with_llm(llm, recent_memories)

    def manual_reflect(self, llm):
        self.enrich_tags_with_llm_trigger("manual", llm)

    def emotional_spike_reflect(self, mood_level, llm):
        if mood_level > 0.8 or mood_level < 0.2:
            self.enrich_tags_with_llm_trigger("emotion spike", llm)

    def connect_old_memories(self):
        if len(self.episodic_memory) >= 2:
            mem1, mem2 = random.sample(self.episodic_memory, 2)
            print(f"[Memory Link] '{mem1['content'][:30]}...' ↔ '{mem2['content'][:30]}...'")
