# memory.py
class Memory:
    def __init__(self, max_history=10):
        self.chat_history = []
        self.episodic_memory = []  # New: memory of moments with emotion context
        self.max_history = max_history

    def remember(self, role, content, mood=None):
        entry = {"role": role, "content": content}
        self.chat_history.append(entry)
        if len(self.chat_history) > self.max_history:
            self.chat_history.pop(0)

        # Save significant events as episodic memories if mood is notable
        if role == "user" and mood and mood != "calm":
            self.episodic_memory.append({
                "event": content,
                "emotion": mood
            })

    def recall(self):
        return self.chat_history[-self.max_history:]

    def get_episodic_memory(self, limit=5):
        return self.episodic_memory[-limit:]
    
    def get_emotional_history(self, limit=5):
        # For now, fake it by returning the last few mood updates as tuples
        # In a future upgrade, this could track true mood history in a list
        return [(self.mood, self.last_updated)] * limit  # Placeholder

