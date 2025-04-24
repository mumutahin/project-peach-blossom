# app.py
from core.llm_engine import LLMEngine
from core.memory import Memory
from core.emotion import EmotionState
from interfaces.chat_ui import start_chat_ui

# Initialize core systems
memory = Memory()
emotion = EmotionState()
llm = LLMEngine(memory=memory, emotion=emotion)

# Launch interface
start_chat_ui(llm)
