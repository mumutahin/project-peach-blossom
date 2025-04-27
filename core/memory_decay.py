# core/memory_decay.py
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class MemoryDecayEngine:
    def link_memory(self, episodic_memory, update_func):
        self.episodic_memory = episodic_memory
        self._update_episodic_in_sqlite = update_func

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

            new_cat = self._categorize_memory(mem)
            if new_cat != mem["category"]:
                mem["category"] = new_cat

            if mem["importance"] >= min_importance:
                updated.append(mem)
                self._update_episodic_in_sqlite(mem)

        self.episodic_memory = updated

    def mood_decay(self):
        if self.emotion_engine:
            self.emotion_engine.decay_mood()
