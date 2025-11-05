from utils import lm, clean_output, loading


class MoST:
    """Main MoST class providing modular planning and response functionality."""

    # ==========================================================
    #  PLANNER COMPONENT
    # ==========================================================
    class Planner:
        def __init__(self):
            with open("prompts/planner/planner.md", "r", encoding="utf-8") as f:
                self.planner_system_prompt = f.read()

            with open("prompts/planner/get_intent.md", "r", encoding="utf-8") as f:
                self.intent_system_prompt = f.read()

            self.planner_messages = [
                {"role": "system", "content": self.planner_system_prompt}
            ]

        class GetIntent:
            def __init__(self, parent, user_input: str):
                self.parent = parent
                self.user_input = user_input
                self.intent_system_prompt = parent.intent_system_prompt
                self.intent_messages = [
                    {"role": "system", "content": self.intent_system_prompt}
                ]

            def get(self) -> str:
                messages = self.intent_messages + [
                    {"role": "user", "content": self.user_input}
                ]
                return lm.chat(messages, print_thoughts=True)

        def plan(self, user_input: str, user_intent: str):
            messages = self.planner_messages + [
                {
                    "role": "user",
                    "content": f"User Input: {user_input}\nUser Intent: {user_intent}",
                }
            ]
            response = lm.chat(messages, print_thoughts=True)
            return clean_output.clean_model_output(response)

    # ==========================================================
    # USER-LM
    # ==========================================================
    class UserLM:
        def __init__(self):
            with open("prompts/u_lm/u_lm.md", "r", encoding="utf-8") as f:
                self.u_system_prompt = f.read()

            self.u_messages = [{"role": "system", "content": self.u_system_prompt}]

        def query(self, payload: dict, print_thoughts=False) -> str:
            messages = self.u_messages + [
                {"role": "user", "content": f"{payload}"}
            ]
            return lm.chat(messages, print_thoughts=print_thoughts)

    # ==========================================================
    # RESPONSE-LM
    # ==========================================================
    class ResponseLM:
        def __init__(self):
            with open("prompts/r_lm/r_lm.md", "r", encoding="utf-8") as f:
                self.r_system_prompt = f.read()

            self.r_messages = [{"role": "system", "content": self.r_system_prompt}]

        def respond(self, content: str, print_thoughts=False) -> str:
            messages = self.r_messages + [
                {"role": "user", "content": content}
            ]
            return lm.chat(messages, print_thoughts=print_thoughts)

    # ==========================================================
    # META-AGENT
    # ==========================================================
    class MetaAgent:
        def __init__(self, plan: dict, steps: list):
            self.plan = plan
            self.steps = steps

            with open("prompts/meta_agent/meta_agent.md", "r", encoding="utf-8") as f:
                self.meta_system_prompt = f.read()

            self.meta_messages = [{"role": "system", "content": self.meta_system_prompt}]

        def assess(self):
            messages = self.meta_messages + [
                {"role": "user", "content": str(self.steps)}
            ]
            return lm.chat(messages, print_thoughts=True)

    # ==========================================================
    # EXECUTION ORCHESTRATOR (MAIN PIPELINE)
    # ==========================================================
    class Execute:
        def __init__(self):
            self.planner = MoST.Planner()
            self.user_lm = MoST.UserLM()
            self.response_lm = MoST.ResponseLM()

        def run(self, user_input: str):
            history = []

            print("\n=== INTENT EXTRACTION ===")
            intent = self.planner.GetIntent(self.planner, user_input).get()
            history.append(("intent", intent))

            print("\n=== PLAN GENERATION ===")
            plan_raw = self.planner.plan(user_input, intent)
            history.append(("plan_raw", plan_raw))

            import json

            # ✅ Already a dict? Use it directly.
            if isinstance(plan_raw, dict):
                plan = plan_raw

            # ✅ If it's a JSON string, parse it.
            else:
                try:
                    plan = json.loads(plan_raw)
                except Exception:
                    # ✅ Try extracting the JSON inside ```json``` blocks
                    import re
                    match = re.search(r"```json\s*(\{.*?\})\s*```", plan_raw, re.DOTALL)
                    if match:
                        plan = json.loads(match.group(1))
                    else:
                        raise ValueError("Planner did not return valid JSON.")

            print("\n=== EXECUTING PLAN STEP-BY-STEP ===")

            state = {}
            step_results = []

            for step in plan["steps"]:
                step_id = step["id"]
                step_desc = step["description"]

                print(f"\n━━━━━━━━━━ STEP {step_id}: {step_desc} ━━━━━━━━━━")

                # ---------- U-LM ----------
                u_payload = {
                    "step_id": step_id,
                    "step_description": step_desc,
                    "state": state,
                    "full_plan": plan,
                    "history": step_results,
                }

                u_out = self.user_lm.query(u_payload, print_thoughts=True)
                clean_u = clean_output.clean_model_output(u_out)

                # try extracting state from JSON block
                try:
                    parsed = json.loads(clean_u)
                    if "state_update" in parsed:
                        print("📌 STATE UPDATE:", parsed["state_update"])
                        state.update(parsed["state_update"])
                except:
                    pass

                # ---------- R-LM ----------
                # ---------- R-LM ----------
                import json

                safe_input = clean_u
                if not isinstance(safe_input, str):
                    safe_input = json.dumps(safe_input, indent=2)

                r_out = self.response_lm.respond(safe_input, print_thoughts=True)


                step_results.append({
                    "step_id": step_id,
                    "description": step_desc,
                    "u_lm": clean_u,
                    "r_lm": r_out,
                    "state": dict(state),
                })

            print("\n=== META-AGENT EVALUATION ===")
            meta = MoST.MetaAgent(plan, step_results)
            meta_decision = meta.assess()

            print("\n=== FINAL ANSWER SYNTHESIS ===")
            all_r = "\n".join([s["r_lm"] for s in step_results])
            final_answer = self.response_lm.respond(all_r, print_thoughts=True)

            return {
                "intent": intent,
                "plan": plan,
                "steps": step_results,
                "meta_decision": meta_decision,
                "final_answer": final_answer,
                "history": history,
            }


# ==============================================================
# MAIN EXECUTION
# ==============================================================

def main():
    system = MoST.Execute()

    user_query = (
        "A red box contains three blue boxes, each blue box contains two yellow spheres. "
        "One yellow sphere is removed from each blue box, and then two blue boxes are removed "
        "from the red box. How many yellow spheres remain?"
    )

    result = system.run(user_query)

    print("\n=== FINAL MOST OUTPUT ===")
    print("\nINTENT:", result["intent"])
    print("\nPLAN:", result["plan"])
    print("\nFINAL ANSWER:", result["final_answer"])


if __name__ == "__main__":
    # Remove spinner so streaming works!
    main()
