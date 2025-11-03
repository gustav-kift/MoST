from utils import lm

class MetaAgent:
    def __init__(self, provider: str | None = None):
        self.provider = provider
    system_prompt = ""
    def send_message(self, message: str, conversation_history: list[dict]) -> str:
        """
        Sends a message to the language model and returns the response.
        Appends the message to the conversation history.
        """
        conversation_history.append({"role": "user", "content": message})
        response = lm.chat(conversation_history, provider=self.provider)
        conversation_history.append({"role": "assistant", "content": response})
        return response