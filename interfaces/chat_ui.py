#interfaces/chat_ui.py
def start_chat_ui(llm):
    print("🟢 Peach is online.")
    while True:
        user_input = input("You: ")
        response = llm.generate_response(user_input)
        print(f"🩵 Peach’s mood: {llm.emotion.current_mood()}")
        print(f"Peach 🍑: {response}")
        if user_input.lower() in ["exit", "quit", "bye"]:
            break