# core/memory_tags.py
import spacy
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
nlp = spacy.load("en_core_web_sm")

class TaggingEngine:
    def __init__(self, episodic_memory=None):
        self.episodic_memory = episodic_memory or []

    def extract_tags(self, content):
        doc = nlp(content.lower())
        tags = [ent.label_.lower() for ent in doc.ents]
        tokens = [token.lemma_ for token in doc if token.pos_ in ["NOUN", "ADJ"] and not token.is_stop]
        symbolic = self.symbolic_tagging(content)
        common_keywords = ["love", "miss", "dream", "hope", "hurt", "excited", "guilt", "nostalgia"]

        tags.extend([kw for kw in common_keywords if kw in content])
        tags.extend(symbolic)
        tags.extend(tokens)
        final_tags = list(set(tags))[:5]
        if len(tags) > 5:
            logging.info(f"[Tags Trimmed] {tags} → {final_tags}")
        return final_tags

    def symbolic_tagging(self, content):
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

    def rate_importance(self, content):
        emotional_words = ["love", "hate", "dream", "hope", "fear", "cry", "beautiful", "miss", "remember"]
        level = sum(1 for word in emotional_words if word in content.lower())
        return min(level / 5.0, 1.0)

    def categorize_memory(self, memory):
        """Classify the memory as 'core', 'casual', or 'fleeting' based on importance and mood."""
        score = memory["importance"]
        mood = memory["mood"].lower()
        tags = memory.get("tags", [])
        high_impact_moods = {"love", "grief", "longing", "hope", "hurt", "shame", "nostalgia"}
        content_lower = memory["content"].lower()
        if score > 0.7 or mood or any(tag in tags for tag in high_impact_moods):
            logging.debug(f"[Categorize] '{memory['content'][:30]}...': Core")
            return "core"
        elif score < 0.3:
            logging.debug(f"[Categorize] '{memory['content'][:30]}...': Fleeting")
            return "fleeting"
        elif any(p in content_lower for p in ["someday", "i wish", "maybe", "imagine if", "if only"]):
            logging.debug(f"[Categorize] '{memory['content'][:30]}...': Imagined")
            return "imagined"
        else:
            logging.debug(f"[Categorize] '{memory['content'][:30]}...': Casual")
            return "casual"

    def get_user_relation(self, content):
        content = content.lower()
        if "you" in content and "i" in content:
            return "personal"
        elif "we" in content:
            return "shared"
        elif "they" in content or "them" in content:
            return "external"
        return "neutral"

    def get_tag_frequency(self):
        tag_freq = {}
        for mem in self.episodic_memory:
            for tag in mem["tags"]:
                tag_freq[tag] = tag_freq.get(tag, 0) + 1
        return tag_freq
