import sys

from loguru import logger as loguru_logger

from .func import Singleton

logger = loguru_logger.opt(colors=True)


class LoggerConfig(Singleton):
    def __init__(self):
        self._logger = loguru_logger
        self._enable_file_log = False
        self._ebable_console_log = False

        self.remove()

    def remove(self):
        self._logger.remove()
        self._enable_file_log = False
        self._ebable_console_log = False

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
                diagnose=True,
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
