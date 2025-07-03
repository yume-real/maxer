import logging
import sys


def setup_basic_logging(level: int = logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    ) 