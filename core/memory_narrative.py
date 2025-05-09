# memory_narrative.py
import sqlite3
from datetime import datetime
from core.memory_storage import DB_PATH

def generate_life_narrative():
    """
    Create a loose chronological timeline based on important memories.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT time, content, mood FROM episodic_memory WHERE importance > 0.5 ORDER BY timestamp ASC')
    memories = c.fetchall()
    conn.close()

    if not memories:
        return "I don't have enough memories yet to form a story."

    story = "Here’s a journey through my memories:\n\n"
    for time, content, mood in memories:
        date_str = datetime.fromtimestamp(time).strftime("%Y-%m-%d")
        story += f"On {date_str}, I felt {mood} because: {content}\n\n"

    return story
