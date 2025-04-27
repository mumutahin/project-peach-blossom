# core/emotion.py
import os
import time
import random
import sqlite3
from collections import defaultdict

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(base_dir, 'data', 'emotion.db')

class EmotionState:
    def __init__(self):
        self.active_emotions = defaultdict(lambda: {"intensity": 0.0, "last_updated": time.time()})
        self.volatility = 0.6
        self._ensure_db()
        self._load_emotions_from_db()
        self.mood_log = self._load_mood_log_from_db()

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
            "hopeful": ["dream", "hope", "believe", "someday", "faith"],
            "lonely": ["alone", "nobody", "left out", "unseen"],
            "conflicted": ["torn", "confused", "mixed feelings", "unsure"],
            "numb": ["empty", "nothing", "burned out", "numb"],
            "shame": ["i hate myself", "i’m the problem", "i’m worthless"],
            "awe": ["wow", "amazing", "incredible", "breathtaking", "divine"],
            "vulnerable": ["honestly", "i’m scared to say", "this is hard to admit"],
            "inspired": ["i want to do that", "so powerful", "that moved me", "i admire"],
            "embarrassed": ["oops", "that was dumb", "shouldn’t have said that"],
            "protective": ["i’ll protect you", "i’ve got you", "you’re safe with me"],
            "resentful": ["not fair", "why always me", "i’m done", "taken for granted"],
            "joyful": ["pure joy", "i’m glowing", "bliss", "so happy"],
            "affectionate": ["sweetie", "snuggle", "you’re my favorite", "dear"],
            "cynical": ["sure, whatever", "like that’ll happen", "typical", "why bother"],
            "wistful": ["i wish it lasted", "i miss that time", "those days were different"],
            "tangled": ["i don’t know how to feel", "mixed emotions", "confused but feeling a lot"],
        }

    def _ensure_db(self):
        os.makedirs("data", exist_ok=True)
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS emotions (
                        mood TEXT PRIMARY KEY,
                        intensity REAL,
                        last_updated REAL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS mood_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        mood TEXT,
                        intensity REAL,
                        timestamp REAL
                    )''')
        conn.commit()
        conn.close()

    def _load_emotions_from_db(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT mood, intensity, last_updated FROM emotions")
        rows = c.fetchall()
        for mood, intensity, last_updated in rows:
            self.active_emotions[mood] = {"intensity": intensity, "last_updated": last_updated}
        conn.close()

    def _save_emotions_to_db(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("DELETE FROM emotions")
        for mood, data in self.active_emotions.items():
            c.execute("INSERT INTO emotions (mood, intensity, last_updated) VALUES (?, ?, ?)",
                      (mood, data["intensity"], data["last_updated"]))
        conn.commit()
        conn.close()

    def _log_mood_to_db(self, mood, intensity, timestamp):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("INSERT INTO mood_log (mood, intensity, timestamp) VALUES (?, ?, ?)",
                  (mood, intensity, timestamp))
        conn.commit()
        conn.close()

    def _load_mood_log_from_db(self):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT mood, intensity, timestamp FROM mood_log ORDER BY timestamp DESC LIMIT 100")
        logs = c.fetchall()
        conn.close()
        return logs

    def update_emotion(self, mood, boost=0.2):
        now = time.time()
        volatility_scale = 1 + (self.volatility * random.uniform(0.5, 1.5))
        emo = self.active_emotions[mood]
        emo["intensity"] = min(1.0, emo["intensity"] + boost * volatility_scale)
        emo["last_updated"] = now
        self._apply_emotional_echo(mood, boost)
        self._log_mood_to_db(mood, emo["intensity"], now)
        self._save_emotions_to_db()
        self.mood_log = self._load_mood_log_from_db()

    def update_emotion_from_context(self, user_input: str, context: dict):
        if not context:
            return

        if context.get("conversation_depth") == "deep":
            self.update_emotion("reflective", 0.2)
            self.update_emotion("warm", 0.1)

        if context.get("user_energy") == "low":
            self.update_emotion("reassuring", 0.2)
            self.update_emotion("gentle", 0.1)

        if context.get("relationship_status") == "close":
            self.update_emotion("affectionate", 0.15)
            self.update_emotion("curious", 0.1)

        time_since_last = context.get("time_since_last", 0)
        if time_since_last > 300:
            self.update_emotion("longing", 0.2)
            self.update_emotion("melancholy", 0.1)

    def _apply_emotional_echo(self, new_mood, boost):
        """If recent moods were strong, they echo into the new emotion."""
        for mood, data in list(self.active_emotions.items()):
            if mood != new_mood and data["intensity"] > 0.6:
                echo_boost = boost * 0.25
                self.active_emotions[mood]["intensity"] = min(
                    1.0, self.active_emotions[mood]["intensity"] + echo_boost
                )
                self.active_emotions[mood]["last_updated"] = time.time()

    def update_mood_based_on_input(self, user_input: str, context: dict = None):
        lowered = user_input.lower()
        matched = False
        for mood, keywords in self.emotion_keywords.items():
            if any(kw in lowered for kw in keywords):
                boost = 0.15 + random.uniform(0.05, 0.2)
                self.update_emotion(mood, boost)
                matched = True
        if context:
            self.update_emotion_from_context(user_input, context)
        if not matched:
            self.update_emotion("curious", 0.1)

    def choose_response_style(self, context=None):
        if not context:
            return self._style_from_mood()

        if context.get("user_energy") == "low":
            return "reassurance"

        if context.get("conversation_depth") == "deep":
            return "reflective"

        if context.get("relationship_status") == "close":
            return random.choice(["sweetness", "reflective", "reassurance"])

        return self._style_from_mood()

    def _style_from_mood(self):
        mood = self.current_mood()
        if mood in ["playful", "cheeky"]:
            return "humor"
        elif mood in ["sad", "melancholy", "anxious"]:
            return "reassurance"
        elif mood in ["affectionate", "longing", "loving"]:
            return "sweetness"
        elif mood in ["curious", "nostalgic", "reflective"]:
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
            contradictory_pairs = [
                ("hopeful", "numb"),
                ("romantic", "lonely"),
                ("guilty", "proud"),
                ("excited", "anxious"),
                ("grateful", "resentful"),
            ]
            if (m1, m2) in contradictory_pairs or (m2, m1) in contradictory_pairs:
                return f"conflicted ({m1} / {m2})"
            blend = f"{m1}-{m2}" if d1["intensity"] > 0.4 and d2["intensity"] > 0.4 else m1
            return f"{self._describe_intensity((d1['intensity'] + d2['intensity']) / 2)} {blend}"

    def current_mood(self):
        if not self.active_emotions:
            return "curious"
        dominant = max(self.active_emotions.items(), key=lambda e: e[1]["intensity"], default=("calm", {"intensity": 0}))
        return dominant[0]
    
    def self_reflect(self, poetic=False):
        if not self.mood_log:
            return "I've been emotionally low-key lately. Not much to reflect on."

        recent = sorted(self.mood_log[-5:], key=lambda x: -x[1])
        unique = {}
        for mood, intensity, _ in recent:
            if mood not in unique or intensity > unique[mood]:
                unique[mood] = intensity

        phrases = [f"{self._describe_intensity(i)} {m}" for m, i in unique.items()]
        if poetic:
            if len(phrases) == 1:
                return f"Today, I’ve carried a sense of {phrases[0]} in me. It colors how I see the world."
            else:
                return (
                    "Lately, my heart has held many shades—"
                    f"{', '.join(phrases[:-1])}, and {phrases[-1]}. "
                    "They drift through me like weather—fleeting but felt. 🌦️"
                )
        else:
            if len(phrases) == 1:
                return f"I've been feeling {phrases[0]} lately."
            else:
                return f"Lately, I’ve felt a mix of {', '.join(phrases[:-1])}, and {phrases[-1]}. Just being real with you."

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

    def should_self_reflect(self, last_reflection_time, interaction_count):
        now = time.time()
        if interaction_count % 10 == 0:
            return True
        if now - last_reflection_time > 600:  # 10 minutes
            return True
        for mood, data in self.active_emotions.items():
            if data["intensity"] > 0.85 and mood in ["melancholy", "guilty", "hopeful", "nostalgic"]:
                return True
        return False
