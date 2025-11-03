from utils import lm

class MoST:
    class planner:
        def __init__(self, provider="gemini"):
            self.provider = provider
            with open("prompts/u_lm.md", "r") as f:
                self.system_prompt = f.read()
            self.messages = [{"role": "system", "content": self.system_prompt}]


    class MetaAgent:
        def __init__(self, provider="gemini"):
            self.provider = provider
            with open("prompts/meta_agent.md", "r") as f:
                self.system_prompt = f.read()
            self.messages = [{"role": "system", "content": self.system_prompt}]

        def agent(self, user_input: str) -> str:
            self.messages.append({"role": "user", "content": user_input})
            response = lm.chat(self.messages, provider=self.provider)
            self.messages.append(
                {"role": "assistant", "content": response}
            )
            return response