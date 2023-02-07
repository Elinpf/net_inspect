from __future__ import annotations

import os
import re
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

from ntc_templates.parse import __file__ as model_file
from ntc_templates.parse import get_clitable, parse_output

from .. import exception
from ..domain import ParsePluginAbstract
from ..func import reg_extend

if TYPE_CHECKING:
    from ..domain import Cmd

try:
    from ntc_templates import __author__ as ntc_author

    CHECK_NTC_TEMPLATES = ntc_author == 'elinpf'

except ImportError:
    CHECK_NTC_TEMPLATES = False


class ParsePluginWithNtcTemplates(ParsePluginAbstract):
    """
    使用ntc-templates-elinpf解析命令
    仓库地址：
        https://github.com/Elinpf/ntc-templates
    """

    @dataclass
    class TextFsmInfo:
        """textFSM模板信息"""

        dir: str = ''
        index_commands: Dict[str, List[str]] = field(default_factory=lambda: {})

    def __init__(self):

        if not CHECK_NTC_TEMPLATES:
            msg = (
                "net_inspect 使用的是`ntc_templates_elinpf`这个包，与原`ntc_templates`命名空间重复造成冲突，\n"
                "请删除原`ntc_templates`包: `pip uninstall ntc_templates`,\n"
                "然后安装`ntc_templates_elinpf`包: `pip install ntc_templates_elinpf`"
            )
            raise ImportError(msg)

        ntc_templates_dir = os.path.join(os.path.dirname(model_file), 'templates')
        self.textfms_info_dict = {
            'external': self.TextFsmInfo(),
            'ntc_templates': self.TextFsmInfo(
                dir=ntc_templates_dir,
                index_commands=self._get_index_commands(ntc_templates_dir),
            ),
        }

    def set_external_templates(self, template_dir: str):
        """设置外部的textFSM模板目录
        Args:
            textfsm_dir: textFSM模板目录
        """
        if not os.path.isdir(template_dir):
            raise exception.TemplateError(f'外部模板路径:{template_dir!r} 不存在.')

        self.textfms_info_dict['external'].dir = template_dir
        self.textfms_info_dict['external'].index_commands = self._get_index_commands(
            template_dir
        )

    def _get_index_commands(self, textfsm_dir: str) -> Dict[str, List[str]]:
        """将ntc-templates中的index文件提取出来，
        并将命令按照平台分类
        Args:
            textfsm_dir: textFSM的模板目录
        """

        index_file = os.path.join(textfsm_dir, 'index')

        if not os.path.exists(index_file):
            raise exception.TemplateError(f'外部模板文件夹{textfsm_dir!r}中必须包含`index`文件.')

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

    @contextmanager
    def _pre_parse(self, command: str, platform: str):
        """预处理重复内容

        Args:
            command: 命令
            platform: 命令所属平台
        """
        for type, textfsm_info in self.textfms_info_dict.items():
            if platform not in textfsm_info.index_commands:  # 检查是否有匹配的平台
                if type == 'external':  # 如果是外部的textFSM模板，则进入ntc_templates中
                    continue
                else:
                    raise exception.TemplateNotSupperThisPlatform(platform)

            platform_commands_reg = textfsm_info.index_commands[platform]
            match_command = ''
            for cmd_reg in platform_commands_reg:
                if re.match(f'^{reg_extend(cmd_reg)}$', command):
                    match_command = re.sub(r'[\[|\]]', '', cmd_reg)
                    break

            if match_command == '':  # 检查是否有匹配的命令
                if type == 'external':
                    continue
                else:
                    raise exception.TemplateNotSupperThisCommand(platform, command)

            yield (match_command, textfsm_info)
            break

    def main(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """识别是否为index中的命令，如果是则使用textFSM解析

        Args:
            cmd: Cmd类
            platform: 命令所属平台, e.g. huawei_os

        Returns:
            解析后的结果
        """
        command = cmd.command

        with self._pre_parse(command, platform) as (match_command, textfsm_info):
            try:
                res = parse_output(
                    platform=platform,
                    command=match_command,
                    data=cmd.content,
                    template_dir=textfsm_info.dir,
                )
            except Exception as e:
                raise exception.TemplateError(
                    f'platform: {platform!r} cmd:{command!r} {str(e)}'
                )

            if not res:  # 如果没有解析到结果，则抛出异常提示
                raise exception.NotParseAnyResult(platform, command)
            return res

    def get_clitable(self, command: str, platform: str) -> dict:
        """通过执行一个空内容的textfsm文件，获得一个字典

        Args:
            command: 命令
            platform: 命令所属平台

        Returns:
            {'command': str, 'platform': str, 'clitable': CliTable}
        """
        with self._pre_parse(command, platform) as (match_command, textfsm_info):
            try:
                clitable = get_clitable(
                    platform=platform, command=command, template_dir=textfsm_info.dir
                )
            except Exception as e:
                raise exception.TemplateError(
                    f'platform: {platform!r} cmd:{command!r} {str(e)}'
                )

            res = {'command': match_command, 'platform': platform, 'clitable': clitable}

            return res
