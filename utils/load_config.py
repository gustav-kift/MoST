import os
import configparser


# Path to the repository root (parent of utils/)
REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

# Path to the configuration file
CONFIG_PATH = os.path.join(REPO_ROOT, "config", "config.ini")


def load_config() -> configparser.ConfigParser:
    """
    Load and return the configuration from config/config.ini.
    Raises FileNotFoundError if the file cannot be read.
    """
    cfg = configparser.ConfigParser()
    read_files = cfg.read(CONFIG_PATH)

    if not read_files:
        raise FileNotFoundError(f"Could not read config file at {CONFIG_PATH}")

    return cfg
