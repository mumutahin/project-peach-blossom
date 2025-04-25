#interfaces/chat_ui.py
import time
import sys

def start_chat_ui(llm):
    print("🟢 Peach is online.")
    last_user_input_time = time.time()
    last_reflection_time = time.time()
    idle_threshold = 180

    while True:
        now = time.time()
        if now - last_user_input_time > idle_threshold and now - last_reflection_time > idle_threshold:
            print("\n💭 Peach reflects quietly to herself...\n")
            time.sleep(1.2)
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
