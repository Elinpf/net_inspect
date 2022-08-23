from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, List, Iterator, Type, Tuple

from . import exception
from .domain import AlarmLevel, AnalysisPluginAbstract, AnalysisResult
from .func import get_command_from_textfsm, snake_case_to_pascal_case, print_log
from .data import pystr

if TYPE_CHECKING:
    from .domain import DefaultVendor, Device

TEMPLATE = str  # ntc-templates 模板文件名称
KEY = str  # ntc-templates 模板文件中的变量名称
PLUGIN_NAME = str  # 分析模块的类名称


@dataclass(unsafe_hash=True)
class AnalysisFunctionInfo:
    plugin_name: str  # 分析插件的名称
    vendor_platform: str  # 分析模块的类名称
    vendor: Type[DefaultVendor]  # 厂商的类
    function_name: str  # 分析函数名称
    function: Callable[[Dict[TEMPLATE, List[KEY]],
                        AnalysisResult]]    # 存放执行的分析函数
    template_keys_list: List[Tuple[TEMPLATE, List[KEY]]]  # 模板文件中的变量名称列表
    template_keys_value: TemplateKeyValue  # 存放模板文件中的变量名称和变量值
    doc: str  # 分析函数的注释文档


class StoreTemplateKey:
    """
    用于存放分析插件的支持厂商和需要模板的值
    这个实例时独立于分析插件的实例，分析插件的run方法会调用这个实例对应Plugin和Vendor的分析函数
    """

    def __init__(self):
        self.store: List[AnalysisFunctionInfo] = []
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

    def get_funcs(self, plugin_name: PLUGIN_NAME, vendor: Type[DefaultVendor]
                  ) -> Iterator[Callable, TemplateKeyValue]:
        """
        获取指定厂商的分析函数, 并且返回模板名称和变量名称的迭代器

        如果设置了only_run_plugins，则只运行指定的插件

        Args:
            - plugin_name: 分析插件类名称
            - vendor: 厂商

        Return:
            - 分析函数和TemplateKey的迭代器
        """
        vendor_name = vendor.PLATFORM
        func_list = []

        for info in self.filter(plugin_name=plugin_name, vendor_platform=vendor_name):
            if self._only_run_plugins and plugin_name not in self._only_run_plugins:  # 如果设置了only_run_plugins，则只运行指定的插件
                continue
            func_list.append((info.function, info.template_keys_value))

        for func, temp_keys in func_list:
            yield func, temp_keys

    def filter(
        self,
        plugin_name: PLUGIN_NAME = None,
        vendor_platform: str = None,
        function_name: str = None
    ) -> List[AnalysisFunctionInfo]:
        """
        返回指定的分析函数列表

        Args:
            - plugin_name: 分析插件类名称
            - vendor_platform: 厂商平台名称
            - function_name: 分析函数名称

        Return:
            - 分析函数的列表
        """
        res = []
        for info in self.store:

            # 如果名称是以蛇形命名，则转换为驼峰命名
            if '_' in plugin_name:
                plugin_name = snake_case_to_pascal_case(plugin_name)

            if plugin_name and info.plugin_name != plugin_name:
                continue
            if vendor_platform and info.vendor_platform != vendor_platform:
                continue
            if function_name and info.function_name != function_name:
                continue
            res.append(info)
        return res

    def store_vendor(self, vendor: Type[DefaultVendor], func: Callable):
        """
        将存储的模板名称和变量名称放入对应的厂商存储器中

        Args:
            - vendor: 厂商类
            - func: 厂商的分析函数
        """
        plugin_name, function_name = func.__qualname__.split('.', maxsplit=2)
        template_keys_value = TemplateKeyValue(vendor.PLATFORM)
        for template_name, keys in self._temp_store:
            template_keys_value.append(template_name, keys)

        af = AnalysisFunctionInfo(
            plugin_name=plugin_name,
            vendor_platform=vendor.PLATFORM,
            vendor=vendor,
            function_name=function_name,
            function=func,
            template_keys_list=list(self._temp_store),
            template_keys_value=template_keys_value,
            doc=func.__doc__.strip()
        )

        self.store.append(af)
        self._temp_store = []

    def vendor(self, vendor: DefaultVendor):
        """
        方法的装饰器，用来确定装饰的方法是对哪个厂商的分析

        Args:
            - vendor: 厂商
        """
        def func_init(func):
            self.store_vendor(vendor, func)
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


class TemplateKeyValue:
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
    用于存放只给到各个分析函数的数据
    """

    template_key_value: Dict[TEMPLATE, List[Dict[KEY, str]]]  # 模板变量和值的字典
    vendor_platform: str  # 厂商平台的字符串

    def __getitem__(self, name: TEMPLATE) -> List[Dict[KEY, str]]:
        """
        通过模板名称获取模板变量和值的字典列表
        模板名称可以使用的形式：
        e.g:
        - 完整形式: huawei_vrp_display_version.textfsm
        - 完整命令: display version

        Args:
            - name: 模板名称

        Return:
            - 模板变量和值的字典列表

        Exception:
            - exception.NtcTemplateNotDefined: 使用缩写或者不存在的模板名称时抛出异常
        """
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
        template_keys: TemplateKeyValue,
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
                raise exception.AnalysisTemplateNameError(
                    '请正确填写文件名称以及扩展名')  # pragma: no cover

            cmd = get_command_from_textfsm(  # 通过模板文件名获得命令
                device.vendor.PLATFORM, template_file)
            cmd_find = device.search_cmd(cmd)  # 搜索命令
            if not cmd_find:  # 当插件中需要，但是设备命令中不存在时, 给出提示
                print_log(
                    f'{pystr.analysis_warning_prefix} device:{device._device_info.name!r} cmd:{cmd!r} no found this command',
                    verbose=2)
                ret[template_file] = []  # 并且返回一个空的列表，作为占位符
                continue

            temp_list = []
            for row in cmd_find._parse_result:  # 将需要的键值取出来
                try:
                    _ = {key: row[key.lower()]
                         for key in keys}
                    temp_list.append(_)
                except KeyError as e:  # pragma: no cover
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

                # 没有数据时，说明不存在可以分析的命令，跳过
                skip_flag = True
                for k, v in template_key_value.items():
                    if v:
                        skip_flag = False
                        break
                if skip_flag:
                    continue

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

        except exception.NtcTemplateNotDefined as e:
            raise exception.NtcTemplateNotDefined(
                f"{self.__class__.__name__} 中无法识别对应模板 {e}, 请检查分析方法中调用的模板名是否正确。")

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
