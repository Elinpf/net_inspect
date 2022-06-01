from __future__ import annotations
import abc
from typing import Dict, TYPE_CHECKING, List, Tuple

from . import exception
from .domain import AnalysisPluginAbstract
from .logger import log

if TYPE_CHECKING:
    from .domain import DefaultVendor, Cmd, Device

TEMPLATE = str
VALUE = str

Level_1 = 0
Level_2 = 1
Level_3 = 2


class Level:
    def __init__(self, level: int, desc: str):
        self._level = level
        self.desc = desc

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level: int):
        if level < Level_1 or level > Level_3:
            raise exception.AnalysisLevelError
        self._level = level


class TemplateValue:
    def __init__(self):
        self._value_store = {}  # type: Dict[TEMPLATE, List[Dict[VALUE, str]]]
        self._vendor_platform = ''  # 平台字符串

    def __getitem__(self, name: TEMPLATE) -> List[Dict[VALUE, str]]:
        """获取模板值"""
        name = self._from_command_to_template_file(name)
        return self._value_store[name]

    def update(self, template: TEMPLATE, value_list: List[Dict[VALUE, str]]):
        """存储模板和值"""
        self._value_store[template] = value_list

    def get_command(self, vendor_platform: str, template: TEMPLATE) -> str:
        """从模板文件名中获得命令
        :param vendor_platform: 平台名称
        :param template: 模板文件名

        :return: 命令

        >>> self.get_command('huawei_os', 'huawei_os_display_interface_status.textfsm')
        'display interface status'
        """

        template = template.replace(vendor_platform + '_', '')
        template = template.replace('.textfsm', '')
        return template.replace('_', ' ')

    def _from_command_to_template_file(self, command: str) -> TEMPLATE:
        """将命令还原为模板文件名
        :param command: 命令

        :return: 模板文件名

        >>> self._from_command_to_template_file('display interface status')
        'huawei_os_display_interface_status.textfsm'
        """
        command = command.lower()
        command = command.replace(' ', '_')
        if not command.startswith(self._vendor_platform):
            command = self._vendor_platform + '_' + command

        if not command.endswith('.textfsm'):
            command += '.textfsm'

        return command


class AnalysisPluginAbc(AnalysisPluginAbstract):

    def __init__(self, ntc_templates:
                 Dict[DefaultVendor, Dict[TEMPLATE, List[VALUE]]]):
        self._ntc_templates = ntc_templates
        self.template = TemplateValue()

    def _init_templates_value(self, device: Device):
        """初始化模板值
        搜索Device中的cmd，将需要用到的模板和值取出来放到self.template中"""
        for vendor, templates_dict in self._ntc_templates.items():
            if vendor.PLATFORM == device.vendor.PLATFORM:  # 判断是否为同一个平台
                for template_file, values in templates_dict.items():
                    # 当结尾不是.textfsm时，报错
                    if not template_file.endswith('.textfsm'):
                        raise exception.AnalysisTemplateError

                    cmd = self.template.get_command(  # 通过模板文件名获得命令
                        vendor.PLATFORM, template_file)
                    cmd_find = device.search_cmd(cmd)  # 搜索命令
                    if cmd_find is None:
                        log.debug(f'{device.device_info.name} 没有找到 {cmd} 命令')
                        continue

                    temp_list = []
                    for row in cmd_find._parse_result:  # 将需要的键值取出来
                        _ = {value.lower(): row[value.lower()]
                             for value in values}
                        temp_list.append(_)

                    self.template.update(template_file, temp_list)

    def run(self, device: Device) -> Level:
        self._init_templates_value(device)
        self.template._vendor_platform = device.vendor.PLATFORM
        return self.main(device.vendor, self.template)

    @abc.abstractmethod
    def main(self, vendor: DefaultVendor, template: TemplateValue) -> Level:
        raise NotImplementedError
