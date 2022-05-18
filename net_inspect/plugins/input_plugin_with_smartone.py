import os
import re
from typing import Dict, Tuple

from ..domain import InputPluginAbstract, DeviceInfo

"""
这个插件是分析的从OSmartOne平台获取的输入文件
文件名格式为: A_FOO_BAR_DR01_127.0.0.1_20220221180010.diag
文件内容格式为:
-------------------------show version-------------------------

H3C Comware Platform Software
Comware Software, Version 5.20, Release 2202
Copyright (c) 2004-2010 Hangzhou H3C Tech. Co., Ltd. All rights reserved.
H3C S5500-28C-EI uptime is 1 weeks, 1 day, 1 hours, 1 minutes

H3C S5500-28C-EI with 1 Processor
256M    bytes SDRAM
32768K  bytes Flash Memory
"""

device_info_reg = r'(?P<name>\S+)\_(?P<ip>(?:\d+\.){3}(?:\d+)).*'
command_line_reg = r'-------------------------(?P<cmd>[^-]+)-------------------------'


class InputPluginWithSmarOne(InputPluginAbstract):

    def _run(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        match = re.match(device_info_reg, os.path.basename(file_path))
        device_info = DeviceInfo(
            name=match.group('name'), ip=match.group('ip'))

        cmd_dict = {}
        content = []
        command = ''

        for line in stream.splitlines():
            if re.match(command_line_reg, line):
                if command:  # 当有命令的时候，说明是上一个命令的结尾，要保存
                    cmd_dict[command] = '\n'.join(content)
                command = re.match(command_line_reg, line).group('cmd')
                content.clear()  # 清空内容
                continue

            content.append(line)

        if command:  # 当有命令的时候，说明是上一个命令的结尾，要保存
            cmd_dict[command] = '\n'.join(content)

        return (cmd_dict, device_info)
