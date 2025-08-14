import logging
import subprocess
import sys
from pathlib import Path

from fixmate.helpers.logger import setup_logger

_logger = logging.getLogger(__name__)


def main() -> None:
    setup_logger()
    script_path = Path(__file__).parent / "compose_checker.sh"
    cmd = [str(script_path), *sys.argv[1:]]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
    except subprocess.CalledProcessError as e:
        _logger.exception(e.stderr)
        sys.exit(1)
    else:
        _logger.info(result.stdout)
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
