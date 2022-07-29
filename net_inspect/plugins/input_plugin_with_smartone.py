import os
import re
from typing import Dict, Tuple

from ..domain import InputPluginAbstract, DeviceInfo

"""
这个插件是分析的从OSmartOne平台获取的输入文件，有两种情况

情况一：
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

情况二：
文件名格式为: A_FOO_BAR_DR01_127.0.0.1.diag
文件内容格式为：
------------------------------------------------------------
dis version
Huawei Versatile Routing Platform Software
VRP (R) software, Version 8.180 (NE20E V800R010C10SPC500)
Copyright (C) 2012-2018 Huawei Technologies Co., Ltd.
HUAWEI NE20E-S4 uptime is 169 days, 13 hours, 50 minutes 
Patch Version: V800R010SPH120

NE20E-S4 version information:
"""

device_info_reg = r'(?P<name>\S+)\_(?P<ip>(?:\d+\.){3}(?:\d+)).*'
command_line_reg = r'^-------------------------(?P<cmd>[^-].*?)-------------------------$'
command_line_reg2 = r'^------------------------------------------------------------$'


class InputPluginWithSmartOne(InputPluginAbstract):
    """通过iSmartOne平台获取的输出"""

    def main(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        match = re.match(device_info_reg, os.path.basename(file_path))
        device_info = DeviceInfo(
            name=match.group('name'), ip=match.group('ip'))

        cmd_dict = {}
        content = []
        command = ''

        lines = stream.splitlines()
        if re.match(command_line_reg, lines[0]):
            state = 1  # 当开头是以----开头的时候，是情况一

        else:
            state = 2  # 否则是情况二

        if state == 1:
            for line in lines:
                if re.match(command_line_reg, line):  # 当遇到的是第一种情况
                    if command:  # 当有命令的时候，说明是上一个命令的结尾，要保存
                        cmd_dict[command] = '\n'.join(content)
                    command = re.match(command_line_reg, line).group('cmd')
                    content.clear()  # 清空内容
                    continue
                content.append(line)

        if state == 2:
            for line in lines:
                if not command:
                    command = line.strip()  # 第一行为命令
                    continue
                if re.match(command_line_reg2, line):
                    cmd_dict[command] = '\n'.join(content)
                    command = ''
                    content.clear()
                    continue
                content.append(line)

        if content:
            cmd_dict[command] = '\n'.join(content)

        return (cmd_dict, device_info)
