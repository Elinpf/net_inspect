from typing import Dict, Tuple
import re

from ..domain import InputPluginAbstract, DeviceInfo

# 类思科的情况
# device>show version
# device(config)# sh version
similar_cisco_reg = re.compile(
    r'^(?P<device_name>[\w\-_\.]+)(?:\(.*?\))?[#|>]\s*(?P<cmd>sh(?:o(?:w)?)?\s+.*)$', re.IGNORECASE)

# 类华为的情况
# <device>display version
# [device] dis version
simialr_huawei_reg = re.compile(
    r'[\<|\[](?P<device_name>[\w\-_\.]+)(?:\-(?:.+?))?[\]|>]\s*(?P<cmd>dis(?:p(?:l(?:a(?:y)?)?)?)?\s+.*)$', re.IGNORECASE)


class InputPluginWithConsole(InputPluginAbstract):
    """通过Console或者vty获取命令的输出"""

    def main(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        device_name = ''
        command = ''
        cmd_dict = {}
        content = []
        for line in stream.splitlines():
            match = re.match(similar_cisco_reg, line) or \
                re.match(simialr_huawei_reg, line)  # 判断是否为命令的行
            if match:
                if not device_name:
                    device_name = match.group('device_name')

                if content and command:  # 如果有内容，且有命令，则保存
                    cmd_dict[command] = '\n'.join(content)

                command = match.group('cmd').strip()
                content.clear()
                continue

            content.append(line)

        if content and command:
            cmd_dict[command] = '\n'.join(content)

        return cmd_dict, DeviceInfo(device_name, '')
