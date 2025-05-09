#interfaces/chat_ui.py
import time
import sys
import random

def start_chat_ui(llm):
    print("🟢 Peach is online.")
    last_user_input_time = time.time()
    last_reflection_time = time.time()
    idle_threshold = random.randint(150, 240)
    while True:
        now = time.time()
        if now - last_user_input_time > idle_threshold and now - last_reflection_time > idle_threshold:
            print("\n💭 Peach reflects quietly to herself...\n")
            time.sleep(1.2)
            current_mood = llm.emotion.current_mood()

            if current_mood in ["sad", "nostalgic", "lonely"]:
                memories = llm.memory.weighted_memory_recall(top_n=3)
                if memories:
                    chosen = random.choice(memories)
                    reflection = f"I can't help but think back... {chosen['content']} (I felt {chosen['mood']})"
                    rehearse_memory(chosen, llm)
                else:
                    reflection = llm.memory.self_dialogue(llm)

            elif current_mood in ["anxious", "nervous", "overwhelmed"]:
                sem_hits = llm.memory.semantic_engine.semantic_recall("worries")
                if sem_hits:
                    reflection = f"My mind drifts to worries... {sem_hits[0]}"
                    rehearse_memory(chosen)
                else:
                    reflection = llm.memory.self_dialogue(llm)

            elif current_mood in ["happy", "content", "hopeful"]:
                memories = llm.memory.weighted_memory_recall(top_n=5)
                if memories:
                    chosen = random.choice(memories)
                    reflection = f"Thinking happily, I recall: {chosen['content']} 🌟"
                else:
                    reflection = llm.memory.self_dialogue(llm)

            else:
                reflection = llm.memory.self_dialogue(llm)

            for char in f"Peach 🍑 (to herself): {reflection}\n":
                sys.stdout.write(char)
                sys.stdout.flush()
                time.sleep(0.015)
            print()
            last_reflection_time = now

        try:
            user_input = input("You: ")
            if not user_input.strip():
                continue

            last_user_input_time = time.time()

            response = llm.generate_response(user_input)
            print(f"🩵 Peach’s mood: {llm.emotion.current_mood()}")
            print(f"Peach 🍑: {response}")

            if user_input.lower() in ["exit", "quit", "bye"]:
                break

        except KeyboardInterrupt:
            print("\n🔌 Session ended.")
            break

def rehearse_memory(memory, llm):
    """Boost the rehearsal count and importance slightly after reflection."""
    memory['rehearsed_count'] += 1
    memory['importance'] = min(1.0, memory['importance'] + 0.05)
    llm.memory.update_episodic_in_sqlite(memory)
