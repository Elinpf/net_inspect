from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Callable, Dict, List, Tuple

from . import exception
from .domain import AlarmLevel, AnalysisPluginAbstract, AnalysisResult
from .func import get_command_from_textfsm
from .logger import log

if TYPE_CHECKING:
    from .domain import DefaultVendor, Device

TEMPLATE = str  # ntc-templates 模板文件名称
VALUE = str  # ntc-templates 模板文件中的变量名称
PLUGIN_NAME = str  # 分析模块的类名称


class StoreTemplateValue:
    """
    用于存放分析插件的支持厂商和需要模板的值
    """

    def __init__(self):
        self.store: Dict[PLUGIN_NAME,
                         Dict[DefaultVendor,
                              Dict[Callable[[Dict[TEMPLATE, List[VALUE]], AnalysisResult]],
                                   Dict[TEMPLATE, List[VALUE]]]]] = {}
        self._temp_store: List[Tuple[TEMPLATE, List[VALUE]]] = []

    def temp_store(self, template_name: TEMPLATE, values: List[VALUE]):
        """
        将模板名称和变量名称存入临时存储器中

        Args:
            - template_name: 模板名称
            - value: 变量名称列表
        """
        self._temp_store.append((template_name, values))

    def store_vendor(self, klass: PLUGIN_NAME,  vendor: DefaultVendor, func: Callable):
        """
        将存储的模板名称和变量名称放入对应的厂商存储器中

        Args:
            - vendor: 厂商类
            - func: 厂商的分析函数
        """
        if not self.store.get(klass):
            self.store[klass] = {}

        if not self.store[klass].get(vendor):
            self.store[klass][vendor] = {}

        if not self.store[klass][vendor].get(func):
            self.store[klass][vendor][func] = {}

        for template_name, values in self._temp_store:
            self.store[klass][vendor][func][template_name] = values

        self._temp_store = []

    def vendor(self, vendor: DefaultVendor):
        """
        方法的装饰器，用来确定装饰的方法是对哪个厂商的分析

        Args:
            - vendor: 厂商
        """
        def func_init(func):
            klass = get_func_class_name(func)
            self.store_vendor(klass, vendor, func)
            return func

        return func_init

    def template_value(self, template: TEMPLATE, value: List[VALUE]):
        """
        方法的装饰器，用来确定装饰的方法需要使用哪些模板和内容

        Args:
            - template: 模板文件名
            - value: 变量名称列表
        """
        def func_init(func):
            self.temp_store(template, value)
            return func
        return func_init


analysis = StoreTemplateValue()


class AlarmLevel(AlarmLevel):

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level: int):
        if level < AlarmLevel.NORMAL or level > AlarmLevel.WARNING:
            raise exception.AnalysisLevelError
        self._level = level


class TemplateValue:
    def __init__(self, vendor_platform: str):
        """
        用于存放ntc-templates模板名称和里面的变量以及变量对应的值

        Args:
            - vendor_platform: 厂商平台的字符串
        """
        self._value_store = {}  # type: Dict[TEMPLATE, List[Dict[VALUE, str]]]
        self._vendor_platform = vendor_platform  # 平台字符串

    def __getitem__(self, name: TEMPLATE) -> List[Dict[VALUE, str]]:
        """获取模板值"""
        name = self._from_command_to_template_file(name)
        if not name in self._value_store:
            raise exception.NtcTemplateNotDefined(name)
        return self._value_store[name]

    def update(self, template: TEMPLATE, value_list: List[Dict[VALUE, str]]):
        """存储模板和值"""
        self._value_store[template] = value_list

    def _from_command_to_template_file(self, command: str) -> TEMPLATE:
        """
        将命令还原为模板文件名
        Args:
            - command 命令

        Return:
            - 模板文件名

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

    def _init_templates_value(
        self,
        device: Device,
        template_values: Dict[TEMPLATE, List[VALUE]]
    ) -> TemplateValue:
        """
        初始化模板和值
        搜索Device中的cmd，将需要用到的模板和值取出来放到返回值中

        Args:
            - device: 设备对象
            - template_values: 模板和值字典

        Return:
            - TemplateValue: 模板和值对象

        Exception:
            - exception.AnalysisTemplateNameError  名称后缀不是.textfsm
            - KeyError

        """

        template = TemplateValue(device.vendor.PLATFORM)
        for template_file, values in template_values.items():
            # 当结尾不是.textfsm时，报错
            if not template_file.endswith('.textfsm'):
                raise exception.AnalysisTemplateNameError

            cmd = get_command_from_textfsm(  # 通过模板文件名获得命令
                device.vendor.PLATFORM, template_file)
            cmd_find = device.search_cmd(cmd)  # 搜索命令
            if cmd_find is None:
                log.debug(
                    str(f'{device.device_info.name} 没有找到 {cmd} 命令'))
                continue

            temp_list = []
            for row in cmd_find._parse_result:  # 将需要的键值取出来
                try:
                    _ = {value.lower(): row[value.lower()]
                         for value in values}
                    temp_list.append(_)
                except KeyError as e:
                    raise KeyError(
                        f'{self.__class__.__name__}模板中的键值{str(e)}不存在')

            template.update(template_file, temp_list)
        return template

    def run(self, device: Device) -> AnalysisResult:
        try:
            result = AnalysisResult()
            # self._init_templates_value(device)
            # self.template._vendor_platform = device.vendor.PLATFORM
            # result = self.main(device.vendor, self.template, result)

            klass_name = self.__class__.__name__
            for func, template_values in analysis.store[klass_name][device.vendor].items():
                # 执行对应厂商的分析方法
                template = self._init_templates_value(device, template_values)
                func(self, template, result)

            # 当没有分析结果的时候，说明没有问题，给出一个正常级别提示
            if not result._result:
                result.add_normal()

        # 如果分析模板不支持厂商，则给出一个关注级别的提示
        except exception.AnalysisVendorNotSupport:
            result.add_focus('{} not support this vendor'.format(
                self.__class__.__name__))
        except exception.NtcTemplateNotDefined:
            # log.debug(f'{device.device_info.name} 没有找到模板')
            ...

        for alarm in result:  # 设置告警所属插件名称
            if not alarm.plugin_name:
                alarm.plugin_name = self.__class__.__name__

        return result


def get_func_class_name(func: Callable) -> str:
    """
    通过方法获取分析模块的类名称
    Args:
        func: AnalysisPluginAbc 中的方法

    Return:
        AnalysisPluginAbc 子类的字符串
    """
    res = inspect.getmembers(func)
    for name, value in res:
        if name == '__qualname__':
            return value.split('.')[0]
