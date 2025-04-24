def start_chat_ui(llm):
    print("🟢 Peach is online.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("👋 Peach: Bye bye!")
            break
        response = llm.generate_response(user_input)
        print(f"🩵 Peach’s mood: {llm.emotion.current_mood()}")
        print(f"Peach 🍑: {response}")
