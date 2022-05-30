from __future__ import annotations
import os
import re
from typing import TYPE_CHECKING, Dict, List
from ntc_templates.parse import parse_output, __file__ as model_file

from ..domain import ParsePluginAbstract
from ..exception import TemplateError
from ..func import reg_extend

if TYPE_CHECKING:
    from ..domain import Cmd


class ParsePluginWithNtcTemplates(ParsePluginAbstract):
    def __init__(self):
        self.index_commands: Dict[str, List[str]] = self._get_index_commands()

    def _get_index_commands(self) -> Dict[str, List[str]]:
        """将ntc-templates中的index文件提取出来，
        并将命令按照平台分类"""

        ntc_template_path = os.path.dirname(model_file)
        index_file = os.path.join(ntc_template_path, 'templates', 'index')
        commands = {}
        with open(index_file, 'r') as f:
            for line in f.readlines():
                if line == '\n':
                    continue
                elif line.startswith('#'):
                    continue
                elif "Template, Hostname, Platform, Command" in line:
                    continue

                e = line.split(',')
                if len(e) != 4:  # 判断是有效行
                    continue

                platform = e[2].strip()
                if platform not in commands:
                    commands[platform] = []

                commands[platform].append(e[-1].strip())

        return commands

    def main(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """对命令进行解析
        :param cmd: 命令对象
        :param platform: 命令所属平台, e.g. huawei_os"""
        command = cmd.command
        if platform not in self.index_commands:
            raise TemplateError(f'{platform} platform not support')

        platform_commands_reg = self.index_commands[platform]
        match_command = ''
        for cmd_reg in platform_commands_reg:
            if re.match(reg_extend(cmd_reg), command):
                match_command = re.sub(r'[\[|\]]', '', cmd_reg)
                break

        if match_command == '':
            raise TemplateError(f'"{command}" command not support')

        try:
            return parse_output(platform=platform, command=match_command, data=cmd.content)
        except Exception as e:
            raise TemplateError(str(e))
