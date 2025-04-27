# memory_narrative.py
import sqlite3
from core.memory_storage import DB_PATH

def generate_life_narrative():
    """
    Create a loose chronological timeline based on important memories.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT timestamp, content, emotion FROM memories WHERE importance > 0.5 ORDER BY timestamp ASC')
    memories = c.fetchall()
    conn.close()

    if not memories:
        return "I don't have enough memories yet to form a story."

    story = "Here’s a journey through my memories:\n\n"
    for timestamp, content, emotion in memories:
        date_str = timestamp.split("T")[0]
        story += f"On {date_str}, I felt {emotion} because: {content}\n\n"

    return story
