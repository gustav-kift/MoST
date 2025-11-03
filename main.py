from utils import lm


# Optional system prompt (empty by default)
system = ""


# Initial message list
messages = [{"role": "system", "content": system}]


if __name__ == "__main__":
    while True:
        try:
            prompt = input("> ")

            if prompt.lower() in (":help", ":?"):
                print(
                    "Commands:\n"
                    "  :help or :?   Show this help message\n"
                    "  :exit or :quit  Exit the chat"
                )
                continue

            if prompt.lower() in (":exit", ":quit"):
                print("Exiting...")
                break

            messages.append({"role": "user", "content": prompt})
            response = lm.chat(messages, provider="groq")
            messages.append({"role": "assistant", "content": response})

            print(response)

        except KeyboardInterrupt:
            print("\nExiting...")
            break
