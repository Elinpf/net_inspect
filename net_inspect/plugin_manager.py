from __future__ import annotations
import os
from typing import TYPE_CHECKING, Dict, List, Tuple
from textfsm import clitable

from .domain import PluginManagerAbc, DeviceInfo, ParsePluginAbstract
from .data import pypath, pyoption
from .logger import log

if TYPE_CHECKING:
    from .domain import Cmd


def _textfsm_reslut_to_dict(header: list, reslut: list) -> List[Dict[str, str]]:
    """将 TextFSM 的结果与header结合转化为dict"""
    objs = []
    for row in reslut:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[header[index].lower()] = element
        objs.append(temp_dict)

    return objs


def _clitable_to_dict(cli_table: clitable.CliTable) -> List[Dict[str, str]]:
    """将 TextFSM cli_table 转化成 dict"""
    objs = []
    for row in cli_table:
        temp_dict = {}
        for index, element in enumerate(row):
            temp_dict[cli_table.header[index].lower()] = element
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


class ParsePluginWithTextFSM(ParsePluginAbstract):
    def _run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """对命令进行解析
        :param cmd: 命令对象
        :param platform: 命令所属平台, e.g. huawei_os"""
        cli_table = clitable.CliTable('index', pypath.templates_dir_path)
        attrs = {"Command": cmd.command, "Platform": platform}
        try:
            cli_table.ParseCmd(cmd.content, attrs)
            stuctured_data = _clitable_to_dict(cli_table)
        except:
            log.error(f'无法解析在 {platform} 平台的 {cmd.command} 命令')
            return {}

        return stuctured_data
