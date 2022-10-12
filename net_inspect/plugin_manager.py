from __future__ import annotations

import os
from typing import Dict, List, Tuple

from .data import pyoption
from .domain import DeviceInfo, PluginManagerAbc
from .exception import InputFileTypeError
from .logger import logger


class PluginManager(PluginManagerAbc):
    def input_dir(
        self, dir_path: str, expend: str | List = None
    ) -> List[Tuple[Dict[str, str], DeviceInfo]]:
        """对目录中的文件进行设备输入"""
        devices = []

        if expend is None:
            expend = pyoption.input_file_expend
        elif expend is str:
            expend = [expend]

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if os.path.splitext(file)[-1] in expend:  # 判断文件后缀
                    file_path = os.path.join(root, file)
                    try:
                        devices.append(self.input(file_path))
                    except InputFileTypeError:  # pragma: no cover
                        logger.info('文件不符合input_plugin标准，跳过: {}'.format(file_path))

        return devices
