import sys

from loguru import logger

INPUT = 'INPUT'
ANALYSIS = 'ANALYSIS'
PARSE = 'PARSE'
OUTPUT = 'OUTPUT'


logger = logger.opt(colors=True)


class LoggerConfig:
    def __init__(self):
        self._logger = logger
        self._logger.remove()

        self._enable_file_log = False
        self._ebable_console_log = False
        self._setup_logger()

    def _setup_logger(self):

        self._logger.level(OUTPUT, no=6, color='<blue>')
        self._logger.level(ANALYSIS, no=7, color='<blue>')
        self._logger.level(PARSE, no=8, color='<blue>')
        self._logger.level(INPUT, no=9, color='<blue>')

    def enable_file_log(
        self,
        file_path: str,
        level: str,
        rotation: str,
        log_format: str,
    ):
        if self._enable_file_log is False:
            self._logger.add(
                sink=file_path,
                level=level,
                rotation=rotation,
                format=log_format,
                enqueue=True,
                backtrace=True,
                diagnose=True
            )
            self._enable_file_log = True

    def enable_console_log(
        self,
        level: str,
        log_format: str,
    ):
        if self._ebable_console_log is False:
            self._logger.add(
                sink=sys.stderr,
                level=level,
                format=log_format,
                enqueue=True,
                backtrace=True,
                diagnose=True,
            )
            self._ebable_console_log = True
