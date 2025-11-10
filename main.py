from utils import lm, loading
from utils.clean_output import clean_model_output as clean_output
from utils.colourized_logs import ColorFormatter
import colorama as colourama
import logging
import json
import ast  # safe literal parser
from utils.safe_parse import safe_parse_json


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

formatter = ColorFormatter("%(asctime)s | %(levelname)s | %(message)s")
ch.setFormatter(formatter)

logger.addHandler(ch)


colourama.init()


messages = [{"role": "user", "content": "A farmer has a wolf, a goat, and a cabbage. He needs to get them all across a river using a small boat that can only carry him and one other item at a time. The wolf will eat the goat if they are left alone, and the goat will eat the cabbage if they are left alone. How can the farmer transport everything across the river??"}]
thought_messages = []


planner_path = "prompts/planner/planner.md" # Path to the planner system prompt
u_lm_path = "prompts/u_lm/u_lm.md" # Path to the user LM system prompt
r_lm_path = "prompts/r_lm/r_lm.md" # Path to the response LM system prompt
meta_agent_path = "prompts/meta_agent/meta_agent.md" # Path to the meta-agent system prompt


def planner():
    logger.info("Loading planner system prompt")
    with open(planner_path, "r") as f:
        planner_system_prompt = f.read()

    planner_messages = [
        {"role": "system", "content": planner_system_prompt},
        *messages
    ]

    logger.info("Requesting plan from model")
    planner_response = lm.chat(planner_messages)

    # Model returned dict directly
    if isinstance(planner_response, dict):
        logger.debug("Received native dict response from model")
        return planner_response

    raw_text = planner_response
    logger.debug("Raw model output: %s", raw_text)

    # Clean code fences
    if "```" in raw_text:
        logger.debug("Cleaning code fences from model output")
        raw_text = clean_output(raw_text)

    logger.debug("Cleaned output: %s", raw_text)

    # If clean_output returned a dict
    if isinstance(raw_text, dict):
        logger.debug("Cleaned output already parsed as dict")
        return raw_text

    logger.info("Parsing structured planner output")

    # Strict JSON parse
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        logger.debug("Strict JSON parsing failed, using literal eval")

    # Python dict-style parse
    try:
        return ast.literal_eval(raw_text)
    except Exception as e:
        logger.error("Failed to parse planner output: %s", e)
        raise

def u_lm(step):
    logger.info("Loading user LM system prompt")
    with open(u_lm_path, "r") as f:
        u_lm_system_prompt = f.read()
    
    
    u_lm_messages = [
                        {"role": "system", "content": u_lm_system_prompt},
                        {"role": "user", "content": f"CURENT STEP: {step}\nCURRENT THOUGHTS: {thought_messages}"}
                    ]
    logger.info("Requesting user LM prompt")

    u_lm_response = lm.chat(u_lm_messages)
    logger.debug("User LM response: " + u_lm_response)
    thought_messages.append({"role": "user", "content": u_lm_response})
    return u_lm_response

def r_lm():
    logger.info("Loading response LM system prompt")
    with open(r_lm_path, "r") as f:
        r_lm_system_prompt = f.read()
    r_lm_messages = [
                        {"role": "system", "content": r_lm_system_prompt},
                        *thought_messages
                    ]
    
    logger.info("Requesting response LM response")
    r_lm_response = lm.chat(r_lm_messages)
    logger.debug("Response LM output: " + r_lm_response)

    thought_messages.append({"role": "assistant", "content": r_lm_response})
    return r_lm_response

def meta_agent(plan, step, thought_messages):
    logger.info("Loading meta-agent system prompt")
    with open(meta_agent_path, "r") as f:
        meta_system_prompt = f.read()

    meta_input = {
        "plan": plan,
        "current_step": step,
        "history": thought_messages[-10:],  # keep it short
        "latest_user": thought_messages[-2] if len(thought_messages) >= 2 else None,
        "latest_assistant": thought_messages[-1] if len(thought_messages) >= 1 else None,
    }

    meta_messages = [
        {"role": "system", "content": meta_system_prompt},
        {"role": "user", "content": json.dumps(meta_input)}
    ]

    logger.info("Requesting meta-agent judgement")
    raw = lm.chat(meta_messages)
    logger.debug("Raw meta-agent output: %s", raw)

    try:
        parsed = safe_parse_json(raw)
    except Exception as e:
        logger.error("Meta-agent parse failed: %s", e)
        # default to retry but also nudge U-LM to re-anchor
        return {
            "status": "retry_required",
            "corrected_step": None,
            "message_for_u_lm": "Re-anchor to the current step; avoid adding new entities or details."
        }

    # Guarantee keys exist
    return {
        "status": parsed.get("status", "retry_required"),
        "corrected_step": parsed.get("corrected_step"),
        "message_for_u_lm": parsed.get("message_for_u_lm"),
    }



def turn(step):
    u_lm_output = u_lm(step)
    r_lm_output = r_lm()
    return [
        {"u_lm_output": u_lm_output},
        {"r_lm_output": r_lm_output}
    ]

def main():
    plan = planner()
    steps = plan.get("steps", [])

    for step in steps:
        logger.info(f"Starting step: {step}")

        step_complete = False

        while not step_complete:

            # Run U-LM → R-LM turn
            u_output = u_lm(step)
            r_output = r_lm()

            # Meta-agent decides what to do
            meta = meta_agent(plan, step, thought_messages)

            status = meta.get("status")

            if status == "step_completed":
                logger.info("Step completed successfully.")
                step_complete = True

            elif status == "retry_required":
                logger.warning("Retrying step due to unclear or incorrect output.")
                continue  # re-run the same step without changes

            elif status == "correction_required":
                corrected = meta.get("corrected_step")
                message_for_u = meta.get("message_for_u_lm")

                if corrected:
                    logger.info("Applying corrected step from meta-agent")
                    step = corrected

                if message_for_u:
                    logger.info("Meta-agent provided correction for U-LM")
                    thought_messages.append({"role": "meta", "content": message_for_u})

                continue

            elif status == "off_plan":
                logger.warning("R-LM went off plan. Re-anchoring.")
                thought_messages.append({
                    "role": "meta",
                    "content": "Please stay focused on the current step only."
                })
                continue

            else:
                logger.error(f"Unknown meta-agent status: {status}. Retrying.")
                continue



if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if Exception != KeyboardInterrupt:
            logger.error("An error occurred: %s", e)
        else:
            logger.warning("Process interrupted by user")