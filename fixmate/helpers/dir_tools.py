def is_hidden_dir(dir_name: str) -> bool:
    return dir_name.startswith(".")


def is_blacklisted_dir(dir_name: str) -> bool:
    black_list = ["__pycache__", "venv", "env", "build"]
    return dir_name in black_list
