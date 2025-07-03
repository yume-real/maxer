import logging

_logger = logging.getLogger("maxer")

if not _logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(
        logging.Formatter("%(levelname)s | %(name)s: %(message)s")
    )
    _logger.addHandler(_handler)

_logger.setLevel(logging.WARNING)

logger = _logger

__version__ = "0.1.0"

from .core.client import MaxerClient as Client
from .webapp import validate_init_data
from .bot import Bot
from .core import models as models
from .core import enums as enums
from .core import exceptions as exceptions

__all__ = [
    "Client",
    "validate_init_data",
    "Bot",
    "models",
    "enums",
    "exceptions",
] 