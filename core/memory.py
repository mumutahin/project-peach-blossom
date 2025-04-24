class Memory:
    def __init__(self):
        self.history = []

    def remember(self, message):
        self.history.append(message)

    def recall(self):
        return self.history[-5:]  # last 5 for now
