import os
import re

from net_inspect import InputPluginAbstract, InputPluginResult, NetInspect
from net_inspect.exception import InputFileTypeError

device_info_reg = r'(?P<hostname>\S+)\_(?P<ip>(?:\d+\.){3}(?:\d+)).*'  # 日志文件名正则表达式
command_line_reg = (
    r'^-------------------------(?P<cmd>[^-].*?)-------------------------$'  # 命令行正则表达式
)


class CustomInputPlugin(InputPluginAbstract):  # 继承了 InputPluginAbstract
    def main(self, file_path: str, stream: str) -> InputPluginResult:
        result = InputPluginResult()  # 创建一个 InputPluginResult 对象

        match = re.match(
            device_info_reg, os.path.basename(file_path)
        )  # 获取文件名，然后匹配正则表达式

        if not match:  # 如果文件名不符合正则表达式
            raise InputFileTypeError(file_path)  # 抛出异常，给 net_inspect 处理

        result.hostname = match.group('hostname')  # 保存获取的设备名
        result.ip = match.group('ip')  # 保存获取设备的 IP, 可选, 如果没有也可以不设置

        command = ''  # 用于存储命令
        content = []  # 用于存储命令输出内容

        for line in stream.splitlines():  # 逐行处理
            """
            逐行处理，如果匹配到命令行，就保存上一个命令的内容，然后清空内容，继续处理下一行
            如果匹配到非命令行，就直接存储内容
            """
            if re.match(command_line_reg, line):  # 如果匹配到命令行
                if command:  # 当有命令的时候，说明是上一个命令的结尾，要保存
                    result.add_cmd(command, '\n'.join(content))  # 保存命令和内容到 result 中

                command = re.match(command_line_reg, line).group('cmd')  # 获取命令
                content = []  # 清空内容
                continue

            content.append(line)  # 匹配到非命令行，就直接存储内容

        if content:  # 最后一个命令由于没有保存，所以要单独保存一下
            result.add_cmd('command', '\n'.join(content))

        return result


if __name__ == '__main__':

    net = NetInspect()  # 实例化 NetInspect 对象

    net.set_input_plugin(CustomInputPlugin)  # 设置输入插件为自定义的插件
    net.run(input_path='log_custom')  # 执行文件夹内的解析

    for device in net.cluster.devices:
        clock = ''
        for row in device.parse_result('dis clock'):  # 获取 display clock 的解析结果
            clock = f"{row['year']}-{row['month']}-{row['day']} {row['time']}"

        print(
            '[+]',
            device.info.hostname,
            device.info.vendor,
            device.info.model,
            'clock:',
            clock,
        )
