from pathlib import Path

import tomli


def load_configs(config_path: Path, section: str) -> dict:
    if not config_path.exists():
        return {}

    with config_path.open("rb") as file_obj:
        config = tomli.load(file_obj)

    return config.get("tool", {}).get(section, {})
