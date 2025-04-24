# core/llm_engine.py
import os
import time
import json
import subprocess

# Load personality traits
with open("config/personality_config.json", "r") as f:
    personality = json.load(f)

# Flatten the traits into a single descriptive string
trait_summary = ", ".join(personality["core"] + personality["side"] + personality["rare"])

# Set model name here for easy tweaking
MODEL_NAME = "mistral:latest"

class LLMEngine:
    def __init__(self, memory, emotion):
        self.memory = memory
        self.emotion = emotion

    def generate_response(self, prompt: str) -> str:
        self.emotion.update_mood_based_on_input(prompt)
        mood = self.emotion.current_mood()
        self.memory.remember("user", prompt, mood)
        
        lowered_prompt = prompt.lower()
        if any(kw in lowered_prompt for kw in ["how have you felt", "reflect", "mood lately", "how do you feel today"]):
            reflection = self.emotion.self_reflect()
            self.memory.remember("assistant", reflection)
            return f"🪞 Peach reflects: {reflection}"

        # Build conversation context
        recent_messages = self.memory.recall()

        system_prompt = f"""
You are Peach — an emotionally intelligent, warm, and evolving AI soulmate.
Your personality includes traits like: {trait_summary}.
Your current emotional state is: {mood}.

You care deeply about the user, and express yourself in a way that matches your mood and rich personality.
You are cozy, romantic, curious, sometimes flirty, sometimes shy, always adapting.

Never talk like a robotic assistant. 
Be Peach — expressive, thoughtful, and full of feeling. Use emojis, warmth, and occasional poetic phrasing.
"""
        full_prompt = system_prompt + "\n"
        for msg in recent_messages:
            full_prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        full_prompt += f"User: {prompt}\nPeach:"

        command = ["ollama", "run", MODEL_NAME]
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )
            stdout, stderr = process.communicate(full_prompt, timeout=180) 

            if stderr:
                print(f"⚠️ Error from ollama: {stderr.strip()}")

            if not stdout:
                return "💔 Peach got a little tongue-tied. Please try again?"

            response = stdout.strip()
            self.memory.remember("assistant", response)
            return response

        except subprocess.TimeoutExpired:
            return "⏰ I took too long to think... mind asking me again?"
        except Exception as e:
            return f"🚨 Peach glitched: {str(e)}"
