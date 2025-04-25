# core/emotion.py
import time
import random
from collections import defaultdict

class EmotionState:
    def __init__(self):
        self.active_emotions = defaultdict(lambda: {"intensity": 0.0, "last_updated": time.time()})
        self.volatility = 0.6
        self.mood_log = []

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
            "flirty": ["hey you", "cutie", "handsome", "wink", "tease", "😏"],
            "hopeful": ["dream", "hope", "believe", "someday", "faith"]
        }

    def update_emotion(self, mood, boost=0.2):
        now = time.time()
        volatility_scale = 1 + (self.volatility * random.uniform(0.5, 1.5))
        emo = self.active_emotions[mood]
        emo["intensity"] = min(1.0, emo["intensity"] + boost * volatility_scale)
        emo["last_updated"] = now
        self.mood_log.append((mood, emo["intensity"], now))

    def update_mood_based_on_input(self, user_input: str):
        lowered = user_input.lower()
        matched = False
        for mood, keywords in self.emotion_keywords.items():
            if any(kw in lowered for kw in keywords):
                boost = 0.15 + random.uniform(0.05, 0.2)
                self.update_emotion(mood, boost)
                matched = True
        if not matched:
            self.update_emotion("curious", 0.1)

    def update_emotion_from_context(self, input_text, context):
        if context.get("relationship_status") == "close":
            self.update_emotion("romantic", 0.2)
        if context.get("user_energy") == "low":
            self.update_emotion("comforting", 0.2)
        if context.get("conversation_depth") == "deep":
            self.update_emotion("melancholy", 0.15)

    def choose_response_style(self):
        if not self.active_emotions:
            return "neutral"
        dominant = max(self.active_emotions.items(), key=lambda e: e[1]["intensity"], default=("calm", {"intensity": 0}))
        mood = dominant[0]
        if mood == "playful":
            return "humor"
        elif mood == "concerned":
            return "reassurance"
        elif mood == "romantic":
            return "sweetness"
        elif mood == "melancholy":
            return "reflective"
        return "neutral"

    def poetic_mood_blend(self):
        blends = {
            ("melancholy", "romantic"): "longing",
            ("anxious", "hopeful"): "nervous optimism",
            ("playful", "flirty"): "cheeky charm",
            ("peaceful", "grateful"): "contentment",
            ("concerned", "guilty"): "remorseful",
            ("excited", "motivated"): "fired up",
        }
        self._decay_emotions()
        top = sorted(self.active_emotions.items(), key=lambda x: -x[1]["intensity"])[:2]
        if len(top) < 2:
            return self.blended_mood()
        e1, e2 = top[0][0], top[1][0]
        poetic = blends.get((e1, e2)) or blends.get((e2, e1))
        if poetic:
            return poetic
        return f"{e1}-{e2}"

    def weight_memory_emotions(self, memory_log):
        for memory in memory_log:
            if memory.get("emotional_impact", 0) > 0.7:
                mood = memory.get("dominant_mood")
                if mood:
                    self.update_emotion(mood, boost=0.25)

    def _decay_emotions(self):
        decay_interval = 60
        decay_rate = 0.05
        now = time.time()
        to_remove = []
        for mood, data in self.active_emotions.items():
            elapsed = now - data["last_updated"]
            if elapsed > decay_interval:
                decayed = data["intensity"] - decay_rate * (elapsed // decay_interval)
                if decayed <= 0.1:
                    to_remove.append(mood)
                else:
                    self.active_emotions[mood]["intensity"] = round(decayed, 2)
                    self.active_emotions[mood]["last_updated"] = now
        for mood in to_remove:
            del self.active_emotions[mood]

    def _describe_intensity(self, val):
        if val >= 0.85: return "overwhelming"
        elif val >= 0.6: return "strong"
        elif val >= 0.4: return "noticeable"
        elif val >= 0.2: return "faint"
        return "barely there"

    def blended_mood(self):
        self._decay_emotions()
        if not self.active_emotions:
            return "calm and steady"
        top_emotions = sorted(self.active_emotions.items(), key=lambda x: -x[1]["intensity"])[:2]
        if len(top_emotions) == 1:
            mood, data = top_emotions[0]
            return f"{self._describe_intensity(data['intensity'])} {mood}"
        else:
            (m1, d1), (m2, d2) = top_emotions
            blend = f"{m1}-{m2}" if d1["intensity"] > 0.4 and d2["intensity"] > 0.4 else m1
            return f"{self._describe_intensity((d1['intensity'] + d2['intensity']) / 2)} {blend}"

    def current_mood(self):
        if not self.active_emotions:
            return "curious"
        dominant = max(self.active_emotions.items(), key=lambda e: e[1]["intensity"], default=("calm", {"intensity": 0}))
        return dominant[0]
    
    def self_reflect(self):
        if not self.mood_log:
            return "I've been emotionally low-key lately. Not much to reflect on."

        recent = sorted(self.mood_log[-5:], key=lambda x: -x[1])
        unique = {}
        for mood, intensity, _ in recent:
            if mood not in unique or intensity > unique[mood]:
                unique[mood] = intensity

        phrases = [f"{self._describe_intensity(i)} {m}" for m, i in unique.items()]
        if len(phrases) == 1:
            return f"I've been feeling {phrases[0]} lately."
        else:
            return f"Lately, I’ve been a mix of {', '.join(phrases[:-1])}, and {phrases[-1]}. That’s just who I am. 💫"

    def get_emotional_history(self, limit=5):
        return self.mood_log[-limit:]

    def process_memory(self, memory):
        tags = memory.get("tags", [])
        tag_to_mood = {
            "guilt": "guilty",
            "nostalgia": "melancholy",
            "dream": "hopeful",
            "hurt": "comforting",
            "love": "romantic",
            "funny": "playful",
            "excited": "excited",
            "stress": "anxious"
        }
        for tag in tags:
            if tag in tag_to_mood:
                self.update_emotion(tag_to_mood[tag], boost=0.1 + random.uniform(0.05, 0.15))

    def external_trigger(self, trigger_type, value):
        if trigger_type == "voice_tone":
            if value == "soothing":
                self.update_emotion("peaceful", 0.2)
            elif value == "sharp":
                self.update_emotion("concerned", 0.2)
        elif trigger_type == "avatar_expression":
            if value == "blush":
                self.update_emotion("shy", 0.15)
            elif value == "laugh":
                self.update_emotion("playful", 0.2)
