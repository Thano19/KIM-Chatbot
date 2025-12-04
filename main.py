import ollama

MODEL_NAME = "tinyllama"

def main():
    chatverlauf = [
        {
            "role": "system",
            "content": (
                "Du bist ein hilfreicher, sachlicher Assistent. "
                "Du antwortest kurz, präzise und erfindest nichts."
            ),
        }
    ]

    while True:
        user_input = input("Du: ")

        if user_input.strip().lower() in {"exit", "quit"}:
            print("Bot: Okay, bis dann 👋")
            break

        chatverlauf.append({"role": "user", "content": user_input})

        try:
            response = ollama.chat(
                model=MODEL_NAME,
                messages=chatverlauf,
            )
        except Exception as e:
            print("⚠️ Fehler beim Aufruf von Ollama:", e)
            continue

        bot_msg = response["message"]["content"]
        chatverlauf.append(response["message"])

        print("Bot:", bot_msg)
        print()  # Leerzeile für bessere Lesbarkeit

if __name__ == "__main__":
    main()
