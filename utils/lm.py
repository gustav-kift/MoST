from dotenv import load_dotenv, get_key
from openai import OpenAI

try:
    from utils import load_config  # package context
except ImportError:
    import load_config  # direct run context


# --- Load .env and config file once at import ---
load_dotenv()
config = load_config.load_config()


# --- Credential selector ---
def get_creds(provider: str | None = None):
    """
    Reads base_url, model, and API key for a given provider.
    Falls back to the default provider in [general].
    """
    provider = provider or config["general"].get("provider")
    if provider not in config:
        raise ValueError(f"Provider '{provider}' not found in config.ini")

    base_url = config[provider].get("base_url")
    model = config[provider].get("model")

    # Derive env var name, e.g. GROQ_API_KEY
    key_name = config[provider].get("api_key")
    api_key = get_key(".env", key_name)

    if not api_key:
        raise EnvironmentError(f"Missing {key_name} in .env file")

    return base_url, model, api_key


# --- Persistent default client ---
_base_url, _model, _api_key = get_creds()
_client = OpenAI(base_url=_base_url, api_key=_api_key)


# --- Chat helper ---
def chat(messages, model: str | None = None, provider: str | None = None):
    """
    Perform a chat completion against the configured provider.
    You can override provider or model per call.
    """
    client = _client
    model = model or _model

    if provider:
        base_url, model, api_key = get_creds(provider)
        client = OpenAI(base_url=base_url, api_key=api_key)

    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content
