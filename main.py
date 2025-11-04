from utils import lm, clean_output


class MoST:
    """Main MoST class providing modular planning and response functionality."""

    # ==========================================================
    #  PLANNER COMPONENT
    # ==========================================================
    class Planner:
        """Planner responsible for intent extraction and plan generation."""

        def __init__(self):
            """Initialize planner with system prompts."""
            with open(
                "prompts/planner/planner.md", "r", encoding="utf-8"
            ) as f:
                self.planner_system_prompt = f.read()

            with open(
                "prompts/planner/get_intent.md", "r", encoding="utf-8"
            ) as f:
                self.intent_system_prompt = f.read()

            self.planner_messages = [
                {"role": "system", "content": self.planner_system_prompt}
            ]

        # ------------------------------------------------------
        #  INTENT EXTRACTION
        # ------------------------------------------------------
        class GetIntent:
            """Extracts the user's intent from a given input."""

            def __init__(self, parent, user_input: str):
                """Initialize intent extractor with parent and user input."""
                self.parent = parent
                self.user_input = user_input
                self.intent_system_prompt = parent.intent_system_prompt
                self.intent_messages = [
                    {"role": "system", "content": self.intent_system_prompt}
                ]

            def get(self) -> str:
                """Step 1: Extract the intent from user input."""
                messages = self.intent_messages + [
                    {"role": "user", "content": self.user_input},
                ]
                return lm.chat(messages)

        # ------------------------------------------------------
        #  PLAN GENERATION
        # ------------------------------------------------------
        def plan(self, user_input: str, user_intent: str) -> str:
            """Step 2: Generate a plan based on the extracted intent."""
            messages = self.planner_messages + [
                {
                    "role": "user",
                    "content": (
                        f"User Input: {user_input}\n"
                        f"User Intent: {user_intent}"
                    ),
                }
            ]
            response = lm.chat(messages)
            return clean_output.clean_model_output(response)

    # ==========================================================
    #  USER LANGUAGE MODEL
    # ==========================================================
    class UserLM:
        """User-level language model responsible for executing plans."""

        def __init__(self):
            """Initialize the UserLM system prompt."""
            with open("prompts/u_lm/u_lm.md", "r", encoding="utf-8") as f:
                self.u_system_prompt = f.read()

            self.u_messages = [
                {"role": "system", "content": self.u_system_prompt}
            ]

        def query(self, plan: dict, feedback: str) -> str:
            """Query the model with user input and plan."""
            messages = self.u_messages + [
                {"role": "user", "content": f"Plan: {plan}\nFeedback: {feedback}"},
            ]
            return lm.chat(messages)

    # ==========================================================
    #  RESPONSE LANGUAGE MODEL
    # ==========================================================
    class ResponseLM:
        """Response-level language model for final user-facing output."""

        def __init__(self):
            """Initialize the ResponseLM system prompt."""
            with open("prompts/r_lm/r_lm.md", "r", encoding="utf-8") as f:
                self.r_system_prompt = f.read()

            self.r_messages = [
                {"role": "system", "content": self.r_system_prompt}
            ]

        def respond(self, user_lm_input: str) -> str:
            """Generate a response based on the UserLM output."""
            messages = self.r_messages + [
                {"role": "user", "content": user_lm_input},
            ]
            return lm.chat(messages)
    class MetaAgent:
        def __init__(self, plans: dict, u_lm: str, r_lm: str):
            self.u_lm = u_lm
            self.r_lm = r_lm
            with open("prompts/meta_agent/meta_agent.md", "r", encoding="utf-8") as f:
                self.meta_system_prompt = f.read()
            self.meta_messages = [
                {"role": "system", "content": self.meta_system_prompt}
            ]
        def do(self):
            outputs = []
            outputs.append({"role": "u_lm", "content": self.u_lm})
            outputs.append({"role": "r_lm", "content": self.r_lm})
            messages = self.meta_messages + [
                {"role": "user", "content": str(outputs)},
            ]
            return lm.chat(messages)
    class Replan:
        def __init__(self, plan: str, feedback: str):
            self.plan = plan
            self.feedback = feedback
            with open("prompts/replan/replan.md", "r", encoding="utf-8") as f:
                self.replan_system_prompt = f.read()
            self.replan_messages = [
                {"role": "system", "content": self.replan_system_prompt}
            ]
        def plan(self):
            messages = self.replan_messages + [
                {"role": "user", "content": f"Plan: {self.plan}\nFeedback: {self.feedback}"},
            ]
            response = lm.chat(messages)
            return clean_output.clean_model_output(response)
        


# ==============================================================
#  MAIN EXECUTION
# ==============================================================



def main():    """Main execution function for the MoST pipeline."""
    # Example user input


if __name__ == "__main__":
    main()