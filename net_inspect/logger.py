import logging
from rich.logging import RichHandler

from .data import pystr

FORMAT = pystr.logger_format
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True)],
)
log = logging.getLogger(pystr.software)
