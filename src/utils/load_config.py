from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    """
    Load a YAML configuration file and return its parsed contents as a dict.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        The YAML document parsed into native Python types via yaml.safe_load.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
