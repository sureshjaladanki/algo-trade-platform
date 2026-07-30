from pathlib import Path
from typing import Union

import yaml


def load_config(path: Union[str, Path]) -> dict:
    """
    Load a YAML configuration file and return its parsed contents as a dict.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        The YAML document parsed into native Python types via yaml.safe_load.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
