import json
import ast
import re

def clean_meta_output(raw: str) -> str:
    """
    Cleans meta-agent output so it becomes valid JSON.

    - Removes markdown fences (```json, ```).
    - Removes leading 'json' tokens.
    - Extracts only the substring between the first { and last }.
    """
    if not isinstance(raw, str):
        return raw

    # Remove markdown fences
    raw = raw.replace("```json", "")
    raw = raw.replace("```", "").strip()

    # Remove leading language tag "json"
    if raw.lower().startswith("json"):
        raw = raw[4:].strip()

    # Extract inside braces
    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1:
        raw = raw[start:end + 1].strip()

    return raw


def safe_parse_json(x):
    """
    Safely parse meta-agent JSON, even if wrapped in code fences,
    prefixed with 'json', or formatted incorrectly.
    """

    # Already good
    if isinstance(x, dict):
        return x

    # Convert bytes
    if isinstance(x, bytes):
        x = x.decode("utf-8", errors="ignore")

    # ALWAYS clean before parsing
    x = clean_meta_output(x)

    # Try strict JSON
    try:
        return json.loads(x)
    except Exception:
        pass

    # Try python literal dict
    try:
        return ast.literal_eval(x)
    except Exception:
        pass

    raise ValueError(f"Could not parse JSON from: {x[:200]}")
