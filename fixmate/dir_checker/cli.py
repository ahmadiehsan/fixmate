import argparse
from pathlib import Path

from fixmate.dir_checker.dir_checker import DirChecker
from fixmate.helpers.logger import setup_logger


def main() -> None:
    setup_logger()

    parser = argparse.ArgumentParser(description="Directory structure checker")
    parser.add_argument("--config", type=Path, help="Path to pyproject.toml file")
    parser.add_argument("dirs", nargs="*", help="Directories to check (optional)")
    args = parser.parse_args()

    DirChecker(config_path=args.config).run(dirs_to_check=args.dirs)


if __name__ == "__main__":
    main()
