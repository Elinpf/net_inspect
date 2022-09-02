from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

from ntc_templates.parse import __file__ as model_file
from ntc_templates.parse import parse_output

from .. import exception
from ..data import pyoption
from ..domain import ParsePluginAbstract
from ..func import reg_extend

if TYPE_CHECKING:
    from ..domain import Cmd

try:
    from ntc_templates import __author__ as ntc_author
    CHECK_NTC_TEMPLATES = (ntc_author == 'elinpf')

except ImportError:
    CHECK_NTC_TEMPLATES = False


class ParsePluginWithNtcTemplates(ParsePluginAbstract):
    """
    使用ntc-templates解析命令
    仓库地址：
        https://github.com/Elinpf/ntc-templates
    """

    @dataclass
    class TextFsmInfo:
        """textFSM模板信息"""
        dir: str = ''
        index_commands: Dict[str, List[str]] = field(
            default_factory=lambda: {})

    def __init__(self):

        if not CHECK_NTC_TEMPLATES:
            msg = """
net_inspect 使用的是`ntc_templates_elinpf`这个包，与原`ntc_templates`不兼容，
请删除原`ntc_templates`包: `pip uninstall ntc_templates`,
然后安装`ntc_templates_elinpf`包: `pip install ntc_templates_elinpf`
"""
            raise ImportError(msg)

        ntc_templates_dir = os.path.join(
            os.path.dirname(model_file), 'templates')
        self.textfms_info_dict = {
            'external': self.TextFsmInfo(),
            'ntc_templates': self.TextFsmInfo(
                dir=ntc_templates_dir,
                index_commands=self._get_index_commands(ntc_templates_dir))
        }

    def set_external_templates(self, template_dir: str):
        """设置外部的textFSM模板目录
        Args:
            textfsm_dir: textFSM模板目录
        """
        if not os.path.isdir(template_dir):
            raise exception.TemplateError(
                f'textfsm_dir:{template_dir!r} not exist')

        self.textfms_info_dict['external'].dir = template_dir
        self.textfms_info_dict['external'].index_commands = self._get_index_commands(
            template_dir)

    def _get_index_commands(self, textfsm_dir: str) -> Dict[str, List[str]]:
        """将ntc-templates中的index文件提取出来，
        并将命令按照平台分类
        Args:
            textfsm_dir: textFSM的模板目录
        """

        index_file = os.path.join(textfsm_dir, 'index')

        if not os.path.exists(index_file):
            raise exception.TemplateError(
                f'textFSM dir{textfsm_dir!r}must include `index` file')

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
        for type, textfsm_info in self.textfms_info_dict.items():
            if platform not in textfsm_info.index_commands:  # 检查是否有匹配的平台
                if type == 'external':  # 如果是外部的textFSM模板，则进入ntc_templates中
                    continue
                else:
                    if pyoption.verbose_level >= 3:
                        raise exception.TemplateError(
                            f'platform:{platform!r} not support')
                    raise exception.Continue

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
                    if pyoption.verbose_level >= 3:
                        raise exception.TemplateError(
                            f'platform:{platform!r} cmd:{command!r} command not support')
                    raise exception.Continue

            try:
                res = parse_output(platform=platform,
                                   command=match_command, data=cmd.content, template_dir=textfsm_info.dir)
            except Exception as e:
                raise exception.TemplateError(
                    f'platform: {platform!r} cmd: {command!r} {str(e)}')

            if not res:  # 如果没有解析到结果，则抛出异常提示
                raise exception.TemplateError(
                    f'platform:{platform!r} cmd:{command!r} no parse result')
            return res
