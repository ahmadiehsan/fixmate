import logging


def setup_logger() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(stream_handler)
