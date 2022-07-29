import logging
from rich.logging import RichHandler

from .data import pystr, pyoption

LOG_KEYWORDS = [pystr.analysis_warning_prefix, pystr.parse_waning_prefix]

FORMAT = pystr.logger_format
logging.basicConfig(
    level=pyoption.log_level,
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, tracebacks_show_locals=True,
                          show_path=False, show_time=False, keywords=LOG_KEYWORDS)])

log = logging.getLogger(pystr.software)
