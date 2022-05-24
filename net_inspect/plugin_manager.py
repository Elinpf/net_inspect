from __future__ import annotations
import os
from typing import Dict, List, Tuple

from .domain import PluginManagerAbc, DeviceInfo
from .data import pyoption


def _textfsm_reslut_to_dict(header: list, reslut: list) -> List[Dict[str, str]]:
    """将 TextFSM 的结果与header结合转化为dict"""
    objs = []
    for row in reslut:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[header[index].lower()] = element
        objs.append(temp_dict)

    return objs


class PluginManager(PluginManagerAbc):

    def input_dir(self, dir_path: str, expend: str | List = None) -> List[Tuple[Dict[str, str], DeviceInfo]]:
        """对目录中的文件进行设备输入"""
        devices = []

        if expend is None:
            expend = pyoption.log_file_expend
        elif expend is str:
            expend = [expend]

        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if os.path.splitext(file)[-1] in expend:  # 判断文件后缀
                    file_path = os.path.join(root, file)
                    devices.append(self.input(file_path))

        return devices
