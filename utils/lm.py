from dotenv import load_dotenv
import os
from openai import OpenAI

try:
    from utils import load_config
except ImportError:
    import load_config


# ================================
# LOAD .env + CONFIG
# ================================
load_dotenv()
config = load_config.load_config()


# ================================
# PROVIDER CREDENTIAL HANDLING
# ================================
def get_creds(provider: str | None = None):
    """
    Returns (base_url, model, api_key)
    - Ollama uses a dummy API key
    - Other providers require real API keys from .env
    """

    provider = provider or config["general"]["provider"]

    if provider not in config:
        raise ValueError(f"Unknown provider '{provider}' in config.ini")

    base_url = config[provider].get("base_url")
    model = config[provider].get("model")

    # ✅ Providers that DO NOT require API keys -> give dummy key
    if provider.lower() == "ollama":
        return base_url, model, "ollama"

    # ✅ Others need real API keys from .env
    key_name = f"{provider.upper()}_API_KEY"
    api_key = os.getenv(key_name)

    if not api_key:
        raise EnvironmentError(
            f"Missing {key_name} in your .env file.\n"
            f"Add: {key_name}=your_key_here"
        )

    return base_url, model, api_key


# ================================
# CREATE CLIENT
# ================================
def create_client(provider=None):
    base_url, model, api_key = get_creds(provider)
    client = OpenAI(base_url=base_url, api_key=api_key)
    return client, model


# ✅ Load default provider (like ollama)
_default_client, _default_model = create_client()


# ================================
# CHAT COMPLETION WRAPPER
# ================================
def chat(messages, model: str | None = None, provider: str | None = None, print_thoughts=False):
    """
    Unified chat wrapper supporting:
    - all providers in config.ini
    - dynamic model/provider override
    - optional debug output
    """

    if provider:
        client, default_model = create_client(provider)
    else:
        client, default_model = _default_client, _default_model

    model = model or default_model

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
    )

    content = response.choices[0].message.content

    if print_thoughts:
        print("\n🧠 MODEL OUTPUT ===============================")
        print(content)
        print("==============================================\n", flush=True)

    return content
