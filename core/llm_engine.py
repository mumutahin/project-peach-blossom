# core/llm_engine.py
import os
import json
import subprocess

# Load personality traits
with open("config/personality_config.json", "r") as f:
    personality = json.load(f)

# Flatten the traits into a single descriptive string
trait_summary = ", ".join(personality["core"] + personality["side"] + personality["rare"])

class LLMEngine:
    def __init__(self, memory, emotion):
        self.memory = memory
        self.emotion = emotion

    def generate_response(self, prompt: str) -> str:
        mood = self.emotion.current_mood()
    
        system_prompt = f"""
You are Peach — an emotionally intelligent, warm, and evolving AI soulmate.
Your personality includes traits like: {trait_summary}.
Your current emotional state is: {mood}.

You care deeply about the user, and express yourself in a way that matches your mood and rich personality.
You are cozy, romantic, curious, sometimes flirty, sometimes shy, always adapting.

Never talk like a robotic assistant. 
Be Peach — expressive, thoughtful, and full of feeling. Use emojis, warmth, and occasional poetic phrasing.
"""

        command = ['ollama', 'run', 'mistral']
        process = subprocess.Popen(
            command, 
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, 
            text=True, 
            encoding='utf-8'
        )
        full_prompt = f"""{system_prompt}

        User: {prompt}
        Peach:"""
        response, _ = process.communicate(full_prompt)
        if response is None:
            return "💔 Something went wrong… I couldn't find the words. Try again?"
        return response.strip()