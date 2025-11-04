import re
import json

def clean_model_output(output: str):
    """
    Cleans LLM output by removing code fences and safely parsing the dictionary or list structure.
    Returns a Python object (list or dict) if parsing succeeds, otherwise the cleaned string.
    """
    if not isinstance(output, str):
        return output

    # Remove common Markdown code fences and language hints (e.g., ```json, ```python)
    cleaned = re.sub(r"^```[a-zA-Z]*\s*", "", output.strip())
    cleaned = re.sub(r"```$", "", cleaned.strip())

    # Attempt to parse JSON-like Python structures safely
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        try:
            # fallback for Python-style dict/list (single quotes)
            return eval(cleaned, {"__builtins__": {}})
        except Exception:
            return cleaned
