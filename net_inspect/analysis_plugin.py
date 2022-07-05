from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, List, Iterator, Type

from . import exception
from .domain import AlarmLevel, AnalysisPluginAbstract, AnalysisResult
from .func import get_command_from_textfsm
from .logger import log

if TYPE_CHECKING:
    from .domain import DefaultVendor, Device

TEMPLATE = str  # ntc-templates 模板文件名称
KEY = str  # ntc-templates 模板文件中的变量名称
PLUGIN_NAME = str  # 分析模块的类名称


class StoreTemplateKey:
    """
    用于存放分析插件的支持厂商和需要模板的值
    这个实例时独立于分析插件的实例，分析插件的run方法会调用这个实例对应Plugin和Vendor的分析函数
    """

    def __init__(self):
        self.store: Dict[PLUGIN_NAME,
                         Dict[DefaultVendor,
                              Dict[Callable[[Dict[TEMPLATE, List[KEY]], AnalysisResult]],
                                   TemplateKey]]] = {}
        self._temp_store = []
        self._only_run_plugins: List[str] = []  # 只运行指定的插件

    def set_only_run_plugins(self, plugins: List[Type[AnalysisPluginAbstract]]):
        """
        设置只运行指定的插件

        Args:
            - plugins: 指定的插件列表
        """
        self._only_run_plugins = [plugin.__name__ for plugin in plugins]

    def temp_store(self, template_name: TEMPLATE, keys: List[KEY]):
        """
        将模板名称和变量名称存入临时存储器中

        Args:
            - template_name: 模板名称
            - keys: 变量名称列表
        """
        self._temp_store.append((template_name, keys))

    def prune_plugins(self, plugins: List[AnalysisPluginAbstract]):
        """
        只保留指定的插件

        Args:
            - plugins: 指定的插件列表
        """
        plugin_list = [plugin.__name__ for plugin in plugins]  # 将插件名称存入列表
        store_plugin_list = list(self.store.keys())  # 取出所有的插件名称
        for self_plugin in store_plugin_list:
            if self_plugin not in plugin_list:
                del self.store[self_plugin]

    def get_funcs(self, plugin_cls: PLUGIN_NAME, vendor: DefaultVendor
                  ) -> Iterator[Callable, TemplateKey]:
        """
        获取指定厂商的分析函数, 并且返回模板名称和变量名称的迭代器

        如果设置了only_run_plugins，则只运行指定的插件

        Args:
            - plugin_cls: 分析插件类名称
            - vendor: 厂商

        Return:
            - 分析函数和TemplateKey的迭代器
        """
        for func, template_key in self.store[plugin_cls][vendor].items():
            if self._only_run_plugins and plugin_cls not in self._only_run_plugins:
                continue
            yield func, template_key

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
            self.store[klass][vendor][func] = TemplateKey(vendor.PLATFORM)

        for template_name, keys in self._temp_store:
            self.store[klass][vendor][func].append(template_name, keys)

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

    def template_key(self, template: TEMPLATE, keys: List[KEY]):
        """
        方法的装饰器，用来确定装饰的方法需要使用哪些模板和内容

        Args:
            - template: 模板文件名
            - keys: 变量名称列表
        """
        def func_init(func):
            self.temp_store(template, keys)
            return func
        return func_init


analysis = StoreTemplateKey()


class AlarmLevel(AlarmLevel):

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level: int):
        if level < AlarmLevel.NORMAL or level > AlarmLevel.WARNING:
            raise exception.AnalysisLevelError
        self._level = level


class TemplateKey:
    def __init__(self, vendor_platform: str):
        """
        用于存放ntc-templates模板名称和里面的变量以及变量对应的值

        Args:
            - vendor_platform: 厂商平台的字符串
        """
        self._vendor_platform = vendor_platform  # 平台名称字符串
        self._key_store: Dict[TEMPLATE,
                              Dict[KEY, List[str]]] = {}  # 存储模板的名称和变量对应关系

    def append(self, template: TEMPLATE, keys: List[KEY]):
        """
        增加ntc-template模板名称和对应的变量列表
        """
        self._key_store[template] = keys


@dataclass
class TemplateInfo:
    """
    用于存放将要给到各个分析方法的数据
    """

    template_key_value: Dict[TEMPLATE, List[Dict[KEY, str]]]  # 模板变量和值的字典
    vendor_platform: str  # 厂商平台的字符串

    def __getitem__(self, name: TEMPLATE) -> List[Dict[KEY, str]]:
        """获取模板值"""
        name = self._from_command_to_template_file(name)
        if not name in self.template_key_value:
            raise exception.NtcTemplateNotDefined(name)
        return self.template_key_value[name]

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
        if not command.startswith(self.vendor_platform):
            command = self.vendor_platform + '_' + command

        if not command.endswith('.textfsm'):
            command += '.textfsm'

        return command


class AnalysisPluginAbc(AnalysisPluginAbstract):

    def _get_template_key_value(
        self,
        template_keys: TemplateKey,
        device: Device,
    ) -> Dict[TEMPLATE, List[Dict[KEY, str]]]:
        """
        更新对应模板中的对应变量的值
        搜索Device中的cmd，将需要用到的模板和值取出来放到返回值中

        Args:
            - template_keys: 模板和值字典
            - device: 设备对象

        Return:
            - 模板和值的字典

        Exception:
            - exception.AnalysisTemplateNameError  名称后缀不是.textfsm
            - KeyError

        """
        ret = {}

        for template_file, keys in template_keys._key_store.items():
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
                    _ = {key.lower(): row[key.lower()]
                         for key in keys}
                    temp_list.append(_)
                except KeyError as e:
                    raise KeyError(
                        f'{self.__class__.__name__}模板中的键值{str(e)}不存在')

            ret[template_file] = temp_list
        return ret

    def run(self, device: Device) -> AnalysisResult:
        try:
            result = AnalysisResult()

            klass_name = self.__class__.__name__
            for func, template_keys in analysis.get_funcs(klass_name, device.vendor):
                # 执行对应厂商的分析方法
                template_key_value = self._get_template_key_value(
                    template_keys, device)

                # 放到数据类中
                template_info = TemplateInfo(template_key_value=template_key_value,
                                             vendor_platform=device.vendor.PLATFORM)

                each_result = AnalysisResult()

                func(template_info, each_result)

                # 当没有分析结果的时候，说明没有问题，给出一个正常级别提示
                if not each_result._result:
                    result.add_normal()

                # 将分析结果放到总结果中
                result.merge(each_result)

        # 如果分析模板不支持厂商，则给出一个关注级别的提示
        except exception.AnalysisVendorNotSupport:
            result.add_focus('{} not support this vendor'.format(
                self.__class__.__name__))
        except exception.NtcTemplateNotDefined:
            # log.debug(f'{device.device_info.name} 没有找到模板')
            ...

        for alarm in iter(result):  # 设置告警所属插件类
            if not alarm.plugin_cls:
                alarm.plugin_cls = self.__class__

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
    for name, key in res:
        if name == '__qualname__':
            return key.split('.')[0]
