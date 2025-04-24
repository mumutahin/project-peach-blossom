class EmotionState:
    def __init__(self):
        self.mood = "calm"

    def update_mood(self, new_mood):
        self.mood = new_mood

    def current_mood(self):
        return self.mood
