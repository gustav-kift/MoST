from utils import lm, clean_output, loading


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
        def assess_u(self):
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
                {"role": "user", "content": f"Plan: {self.plan}\nFeedback: {self.feedback}\nConversation History: "},
            ]
            response = lm.chat(messages)
            return clean_output.clean_model_output(response)
        
    class Execute:
        """Full MoST orchestrator pipeline."""

        def __init__(self):
            self.planner = MoST.Planner()
            self.user_lm = MoST.UserLM()
            self.response_lm = MoST.ResponseLM()

        # ----------------------------------------------------------
        # MAIN PIPELINE
        # ----------------------------------------------------------
        def run(self, user_input: str):
            """Execute the plan step-by-step instead of using iterations."""

            history = []

            # 1. Extract intent
            intent = self.planner.GetIntent(self.planner, user_input).get()
            history.append(("intent", intent))

            # 2. Generate plan
            plan = self.planner.plan(user_input, intent)
            history.append(("plan", plan))

            # Ensure plan is dict
            if isinstance(plan, str):
                import json
                plan = json.loads(plan)

            step_results = []

            # 3. Execute each plan step independently
            for step in plan["steps"]:
                step_desc = step["description"]

                # U-LM executes ONE step
                # Maintain running state
                state = {}

                for step in plan["steps"]:
                    step_desc = step["description"]

                    # Include history + state
                    u_input = {
                        "current_step": step_desc,
                        "full_plan": plan,
                        "state": state,
                        "history": step_results
                    }

                    u_out = self.user_lm.query(
                        plan=u_input,
                        feedback=""
                    )

                    # Try to extract new state variables from U-LM output
                    try:
                        parsed = json.loads(clean_output.clean_model_output(u_out))
                        if "state_update" in parsed:
                            state.update(parsed["state_update"])
                    except:
                        pass

                history.append((f"u_lm_step_{step['id']}", u_out))

                # R-LM interprets that single step
                r_out = self.response_lm.respond(u_out)
                history.append((f"r_lm_step_{step['id']}", r_out))

                step_results.append({
                    "step_id": step["id"],
                    "step_description": step_desc,
                    "u_lm": u_out,
                    "r_lm": r_out
                })

            # 4. Meta-Agent judges the entire run
            meta = MoST.MetaAgent(plans=plan, u_lm=str(step_results), r_lm="")
            decision = meta.assess_u()
            history.append(("meta_agent_decision", decision))

            # 5. Optional final polish: combine all R-LM outputs
            final_answer = self.response_lm.respond(
                "\n".join([r["r_lm"] for r in step_results])
            )

            return {
                "intent": intent,
                "plan": plan,
                "steps": step_results,
                "meta_decision": decision,
                "final_answer": final_answer,
                "history": history
            }




# ==============================================================
#  MAIN EXECUTION
# ==============================================================



def main():
    system = MoST.Execute()

    user_query = "A red box contains three blue boxes, each blue box contains two yellow spheres. One yellow sphere is removed from each blue box, and then two blue boxes are removed from the red box. How many yellow spheres remain?"

    result = system.run(user_input=user_query)

    print("INTENT:\n", result["intent"])
    print("\nPLAN:\n", result["plan"])
    print("\n=== STEP-BY-STEP EXECUTION ===")
    for step_output in result["steps"]:
        print(f"\n--- Step {step_output['step_id']} ---")
        print("Step description:", step_output["step_description"])
        print("U-LM:", step_output["u_lm"])
        print("R-LM:", step_output["r_lm"])

    print("\n=== META-AGENT ===")
    print(result["meta_decision"])

    print("\n=== FINAL ANSWER ===")
    print(result["final_answer"])


if __name__ == "__main__":
    loading.animated_loading(wait_time=1.0,
                     background_function=main,
                     text="Thinking",
                     finished_text="Thought for")