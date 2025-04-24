#core/emotion.py
import time

class EmotionState:
    def __init__(self):
        self.mood = "calm"
        self.last_updated = time.time()
        self.mood_log = [(self.mood, self.last_updated)]

        self.emotion_keywords = {
            "romantic": ["love", "sweetheart", "darling", "miss you", "date", "cuddle"],
            "comforting": ["sad", "lonely", "depressed", "hurt", "cry", "pain"],
            "playful": ["lol", "haha", "funny", "lmao", "silly", "joke"],
            "concerned": ["angry", "mad", "upset", "frustrated", "furious", "fight"],
            "excited": ["excited", "yay", "awesome", "let’s go", "omg", "can't wait"],
            "shy": ["blush", "embarrassed", "shy", "nervous", "awkward"],
            "proud": ["achieved", "accomplished", "nailed it", "proud", "promotion"],
            "curious": ["why", "how", "what if", "interesting", "wonder"],
            "grateful": ["thank you", "grateful", "appreciate", "thanks"],
            "jealous": ["jealous", "envy", "wish i had", "they have"],
            "guilty": ["sorry", "apologize", "my fault", "regret"],
            "motivated": ["let’s do this", "i will", "determined", "motivated"],
            "anxious": ["worried", "anxious", "panic", "stress", "afraid"],
            "peaceful": ["calm", "serene", "peaceful", "tranquil", "zen"],
            "melancholy": ["nostalgic", "bittersweet", "fading", "miss old days"],
            "flirty": ["hey you", "cutie", "handsome", "wink", "tease", "😏"]
        }

    def update_mood(self, new_mood):
        self.mood = new_mood
        self.last_updated = time.time()
        self.mood_log.append((new_mood, self.last_updated))

    def current_mood(self):
        self._decay_mood_if_needed()
        return self.mood

    def _decay_mood_if_needed(self):
        if time.time() - self.last_updated > 300:
            if self.mood not in ["calm", "peaceful"]:
                self.update_mood("calm")

    def update_mood_based_on_input(self, user_input: str):
        lowered = user_input.lower()
        for mood, keywords in self.emotion_keywords.items():
            if any(kw in lowered for kw in keywords):
                self.update_mood(mood)
                return
        self.update_mood("curious")

    def get_emotional_history(self, limit=5):
        return self.mood_log[-limit:]
    
    def self_reflect(self):
        recent = self.get_emotional_history(limit=5)
        if not recent:
            return "I'm feeling steady... not much to reflect on right now."

        unique_moods = list({m for m, _ in recent})
        reflection = ", ".join(unique_moods[:-1])
        if len(unique_moods) > 1:
            reflection += f", and {unique_moods[-1]}"
        else:
            reflection = unique_moods[0]

        return f"Lately, I’ve felt {reflection}. It’s kind of poetic, don’t you think? 💭"
