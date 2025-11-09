from utils import lm, loading
from utils.clean_output import clean_model_output as clean_output
from utils.colourized_logs import ColorFormatter
import colorama as colourama
import logging
import json
import ast  # safe literal parser

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

def meta_agent():
    pass

def main():
    plans = planner()

    for step in plans.get("steps", []):
        u_lm(step)
        r_lm()
"""        u_lm_output = u_lm() # we will provide the step in the plan
        r_lm_output = r_lm()
        meta_agent_output = meta_agent() # Will be given the plan, the current step, and will see if we need to adjust anything."""


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        if Exception != KeyboardInterrupt:
            logger.error("An error occurred: %s", e)
        else:
            logger.warning("Process interrupted by user")