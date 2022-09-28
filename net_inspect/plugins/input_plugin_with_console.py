from typing import Dict, Tuple
import re

from ..domain import InputPluginAbstract, DeviceInfo, InputPluginResult

# 类思科的情况
# device>show version
# device(config)# sh version
similar_cisco_reg = re.compile(
    r'^(?P<device_name>[\w\-_\.]+)(?:\(.*?\))?[#|>]\s*(?P<cmd>sh(?:o(?:w)?)?\s+.*)$',
    re.IGNORECASE,
)

# 类华为的情况
# <device>display version
# [device] dis version
simialr_huawei_reg = re.compile(
    r'[\<|\[](?P<device_name>[\w\-_\.]+)(?:\-(?:.+?))?[\]|>]\s*(?P<cmd>dis(?:p(?:l(?:a(?:y)?)?)?)?\s+.*)$',
    re.IGNORECASE,
)

prompt_reg = r'\S+[>|\]|\)|#]'


class InputPluginWithConsole(InputPluginAbstract):
    """通过Console或者vty获取命令的输出"""

    def main(self, file_path: str, stream: str) -> InputPluginResult:
        command = ''
        content = []

        prompt = ''  # 用于记录当前的提示符

        result = InputPluginResult()

        for line in stream.splitlines():
            match = re.match(similar_cisco_reg, line) or re.match(
                simialr_huawei_reg, line
            )  # 判断是否为命令的行
            if match:
                if not result.hostname:  # 如果没有设备名称就记录
                    result.hostname = match.group('device_name')

                prompt = re.match(prompt_reg, line).group(0)  # 获取当前的提示符

                if content and command:  # 如果有内容，且有命令，则保存
                    result.add_cmd(command, '\n'.join(content))

                command = match.group('cmd').strip()
                content.clear()
                continue

            else:  # 如果没有匹配到，有可能是只有命令提示符，此时也要保存
                if prompt:  # 如果保存有提示符
                    # 如果行开始是提示符，且有内容，且有命令，则保存
                    if line.startswith(prompt) and content and command:
                        result.add_cmd(command, '\n'.join(content))

                        command = ''  # 清空状态
                        content.clear()
                        continue

                content.append(line)  # 如果没有匹配到，则添加到内容中

        if content and command:  # 最后将没有保存的内容保存
            result.add_cmd(command, '\n'.join(content))

        return result
