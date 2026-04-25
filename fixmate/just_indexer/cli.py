import argparse
from pathlib import Path

from fixmate.helpers.logger import setup_logger
from fixmate.just_indexer.just_indexer import JustIndexer


def main() -> None:
    setup_logger()

    parser = argparse.ArgumentParser(description="Just modules indexer")
    parser.add_argument("--config", type=Path, help="Path to pyproject.toml file")
    parser.add_argument("dirs", nargs="*", help="Directories to check")
    args = parser.parse_args()

    JustIndexer(config_path=args.config).run(root_dirs=args.dirs)


if __name__ == "__main__":
    main()
