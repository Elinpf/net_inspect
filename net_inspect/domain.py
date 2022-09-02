from __future__ import annotations

import re
import abc
from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple, Type

from . import exception
from .data import pystr, pyoption
from .func import print_log, pascal_case_to_snake_case, NoneSkip
from .vendor import DefaultVendor
from .base_info import BaseInfo, EachVendorDeviceInfo


class Cluster:
    """作为设备的集合"""

    def __init__(self):
        self._plugin_manager: PluginManagerAbc = None
        self.devices: DeviceList[Device] = DeviceList()
        self.base_info_handler = EachVendorDeviceInfo()

    def parse(self):
        """递归对每个设备的命令进行解析"""
        self.devices.parse(base_info_handler=self.base_info_handler)

    def analysis(self):
        """递归对每个设备进行分析"""
        self.devices.analysis(base_info_handler=self.base_info_handler)

    @property
    def plugin_manger(self) -> PluginManagerAbc:
        return self._plugin_manager

    @plugin_manger.setter
    def plugin_manager(self, obj: PluginManagerAbc):
        self._plugin_manager = obj

    def search(self, device_name: str) -> List[Device]:
        """搜索设备

        :param device_name: 搜索字符串
        :return: 设备列表"""
        return self.devices.search(device_name)

    def input_dir(self, dir_path: str, expend: str | List[str] = None):
        """输入整个目录，对目录中的文件进行提取设备和命令, 并保存到self.devices中

        :param dir_path: 目录路径
        :param expend: 包含的文件后缀"""
        devices_list = self.plugin_manager.input_dir(dir_path, expend)

        for cmd_contents_and_device_info in devices_list:
            self.save_device_with_cmds(cmd_contents_and_device_info)

    def input(self, file_path: str):
        """输入文件，对文件中的设备和命令进行提取，并保存到self.devices中

        :param file_path: 文件路径"""
        cmd_contents_and_deviceinfo = self.plugin_manager.input(file_path)
        self.save_device_with_cmds(cmd_contents_and_deviceinfo)

    def save_device_with_cmds(self,
                              cmd_contents_and_deviceinfo: Tuple[Dict[str, str], DeviceInfo]):
        """将设备和命令保存到self.devices中

        :param device_cmds_and_deviceinfo: 命令和内容的字典 和 设备信息"""
        device_cls = Device()
        device_cls._plugin_manager = self.plugin_manager
        device_cls.save_to_cmds(cmd_contents_and_deviceinfo[0])  # 保存命令信息
        device_cls._device_info = cmd_contents_and_deviceinfo[1]  # 保存设备简单信息
        self.devices.append(device_cls)

    def output(self, file_path: str = '', params: Dict[str, str] = {}):
        """输出到文件

        :param file_path: 文件路径"""
        self.plugin_manager._output_plugin.run(self.devices, file_path, params)


class DeviceList(list):
    """设备列表"""

    def __init__(self):
        self._devices: List[Device] = []

    def __getitem__(self, index: int) -> Device:
        return self._devices[index]

    def __iter__(self) -> Iterator[Device]:
        return self._devices.__iter__()

    def __len__(self):
        return len(self._devices)

    def append(self, device: Device):
        """添加设备

        :param device: 设备"""
        self._devices.append(device)

    def parse(self, base_info_handler: EachVendorDeviceInfo):
        """递归对每个设备的命令进行解析"""
        for device in self._devices:
            device.parse()
            # 将分析到的基础信息放到Device.info中
            device.info = base_info_handler.run_baseinfo_func(device)

    def analysis(self, base_info_handler: EachVendorDeviceInfo):
        """递归对每个设备进行分析, 必须在parse之后执行"""
        for device in self._devices:
            device.analysis()
            # 将分析到的状态信息放到Device.info.analysis中
            base_info_handler.run_analysis_info(device)

    def search(self, device_name: str) -> List[Device]:
        """查找设备

        :param device_name: 设备信息
        :return: 设备列表"""
        return [device for device in self._devices if device_name in device._device_info.name]


@dataclass
class DeviceInfo:
    """用于InputPlugin中获取到的设备信息"""
    name: str
    ip: str = ''  # manager_ip


class Device:
    """作为设备的抽象"""

    def __init__(self):
        self.cmds: Dict[str, Cmd] = {}
        self._vendor = DefaultVendor
        self._plugin_manager: PluginManagerAbc = None
        self._device_info: DeviceInfo = None
        self._base_info: BaseInfo = None

        self._analysis_result = AnalysisResult()

    @property
    def info(self) -> BaseInfo:
        """设备基础信息，会在parse和analysis后更新"""
        if self._base_info is None:
            return BaseInfo()
        return self._base_info

    @info.setter
    def info(self, obj: BaseInfo):
        """设置设备基础信息"""
        self._base_info = obj

    @property
    def analysis_result(self) -> AnalysisResult:
        return self._analysis_result

    def parse_result(self, cmd: str) -> List[dict] | None:
        """解析命令结果

        :param cmd: 命令
        :return: 命令结果"""
        command = self.search_cmd(cmd)
        if not command:
            return None

        return command._parse_result

    def save_to_cmds(self, cmd_contents: Dict[str, str]):
        """将分割好的命令字典保存到设备的命令列表中"""
        for command, content in cmd_contents.items():
            cmd = Cmd(command)
            cmd.content = content
            self.cmds[command] = cmd

        if self.vendor is DefaultVendor:  # 最后再检查厂商
            self.check_vendor()

    def check_vendor(self):
        """检查厂商"""
        vendor = self.vendor.check_vendor(self.cmds)
        self._vendor = vendor

    @property
    def vendor(self) -> Type[DefaultVendor]:
        """返回厂商类"""
        return self._vendor

    def parse(self):
        """对每条cmd进行解析"""
        for _, cmd in self.cmds.items():
            try:
                # 首先判断是否为无效命令
                if not cmd.is_vaild(self._vendor.INVALID_STR):
                    if pyoption.verbose_level > 3:
                        raise exception.TemplateError(
                            f'platform: {self._vendor.PLATFORM!r} cmd: {cmd.command!r} content is invaild or blank')
                    continue
                parse_result = self._plugin_manager.parse(
                    cmd, self.vendor.PLATFORM)
                cmd.update_parse_reslut(parse_result)
            except exception.TemplateError as e:
                print_log(
                    f"{pystr.parse_waning_prefix} device:{self._device_info.name!r} {str(e)}",
                    verbose=1)
                continue
            except exception.Continue:
                continue

    def analysis(self):
        """对设备进行分析, 需要在parse之后"""
        res = self._plugin_manager.analysis(self)
        self._analysis_result.merge(res)

    def search_cmd(self, cmd_name: str) -> Cmd | NoneSkip:
        """
        查找命令, 返回Cmd类

        Args:

            cmd_name: 命令名
        Return
            Cmd类 或者 None
        """
        res = None  # type: Tuple[Cmd, int]
        cmd_name_split = cmd_name.split()
        cmd_name_len = len(cmd_name_split)

        for command in self.cmds.keys():

            score = 0  # 匹配得分
            is_match = True  # 是否匹配的标签

            # 切分命令
            command_split = command.split()
            if not len(command_split) == cmd_name_len:  # 当命令长度不一致就跳过
                continue

            # 对每个单词进行匹配并打分
            for i, each_command in enumerate(command_split):
                if is_match == False:
                    break
                # 排序长命令与短的命令
                if len(each_command) > len(cmd_name_split[i]):
                    long_each_cmd, short_each_cmd = each_command, cmd_name_split[i]
                else:
                    long_each_cmd, short_each_cmd = cmd_name_split[i], each_command

                # 匹配单词
                if not long_each_cmd.startswith(short_each_cmd):
                    is_match = False
                    break
                score += len(short_each_cmd)

            if is_match:
                # 比较得分, 取最高的
                if (not res) or score > res[1]:
                    res = (self.cmds[command], score)

        return res[0] if res else NoneSkip()


class Cmd:
    """用于存放命令名称，以及命令的内容，等待后续的解析
    在解析完成后删除命令的内容,并存放应有的解析内容"""

    def __init__(self, cmd: str):
        """ :params: cmd: 命令的完整名称"""
        self._command: str = ''
        self._content: str = ''
        self._parse_result: List[Dict[str, str]] = []

        self.command = cmd

    def __enter__(self):
        return self

    def __exit__(self, type, value, tace):
        pass

    @property
    def command(self) -> str:
        return self._command

    @command.setter
    def command(self, cmd: str):
        """设置命令名称
        自动合并多个空格"""
        self._command = ' '.join(cmd.split())

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, stream: str):
        self._content = stream

    def update_parse_reslut(self, result: List[Dict[str, str]]):
        """在取到解析结果后，更新解析结果"""
        self._parse_result = result

    def is_vaild(self, invalid_str: Optional[str] = None) -> bool:
        """判断命令的内容是否为有效内容
        Args:
            invalid_str: 如果命令的内容包含这个字符串，则认为命令无效

        Returns:
            bool: 命令是否有效
        """
        if bool(self.content.strip()) == False:  # 如果为空则认为无效
            return False
        elif invalid_str and re.search(invalid_str, self.content):  # 如果包含无效字符串则认为无效
            return False
        return True

    @property
    def parse_result(self) -> List[Dict[str, str]]:
        return self._parse_result


class PluginManagerAbc(abc.ABC):
    """对插件的管理的抽象接口, 管理output和parse"""

    def __init__(self,
                 input_plugin: Optional[Type[InputPluginAbstract]] = None,
                 output_plugin: Optional[Type[OutputPluginAbstract]] = None,
                 parse_plugin: Optional[Type[ParsePluginAbstract]] = None,
                 analysis_plugin: List[Type[AnalysisPluginAbstract]] = []):
        self._input_plugin: Optional[InputPluginAbstract] = None
        self._output_plugin: Optional[OutputPluginAbstract] = None
        self._parse_plugin: Optional[ParsePluginAbstract] = None
        self._analysis_plugin: List[AnalysisPluginAbstract] = []

        if input_plugin:
            self.input_plugin = input_plugin
        if output_plugin:
            self.output_plugin = output_plugin
        if parse_plugin:
            self.parse_plugin = parse_plugin
        if analysis_plugin:
            self.analysis_plugin = analysis_plugin

    def check_cls(check_type: str):
        """装饰器用来检测插件的类型, 如果插件不是指定的类型, 则抛出异常
        如果是传入的是实例，改为类再传入
        """

        def wrapper(func):
            def inner(self, plugin_cls: Type[PluginAbstract]):
                if not hasattr(plugin_cls, '__name__'):  # 如果是实例
                    plugin_cls = plugin_cls.__class__
                # 如果不是指定的类型
                if not issubclass(plugin_cls, globals()[check_type]):
                    raise TypeError(
                        f'{plugin_cls.__name__} is not {check_type}')
                return func(self, plugin_cls)
            return inner
        return wrapper

    def check_cls_list(check_type: str):
        """装饰器用来检测插件的类型, 如果插件不是指定的类型, 则抛出异常
        如果是传入的是实例，改为类再传入
        """

        def wrapper(func):
            def inner(self, plugin_cls_list: List[Type[PluginAbstract]]):
                cls_list = []
                for plugin_cls in plugin_cls_list:
                    if not hasattr(plugin_cls, '__name__'):  # 如果是实例
                        plugin_cls = plugin_cls.__class__
                    # 如果不是指定的类型
                    if not issubclass(plugin_cls, globals()[check_type]):
                        raise TypeError(
                            f'{plugin_cls.__name__} is not {check_type}')
                    cls_list.append(plugin_cls)
                return func(self, cls_list)
            return inner
        return wrapper

    @property
    def input_plugin(self) -> Optional[InputPluginAbstract]:
        return self._input_plugin

    @input_plugin.setter
    @check_cls("InputPluginAbstract")
    def input_plugin(self, plugin_cls: Type[InputPluginAbstract]):
        self._input_plugin = plugin_cls()

    @property
    def output_plugin(self) -> Optional[OutputPluginAbstract]:
        return self._output_plugin

    @output_plugin.setter
    @check_cls("OutputPluginAbstract")
    def output_plugin(self, plugin_cls: Type[OutputPluginAbstract]):
        self._output_plugin = plugin_cls()

    @property
    def parse_plugin(self) -> Optional[ParsePluginAbstract]:
        return self._parse_plugin

    @parse_plugin.setter
    @check_cls("ParsePluginAbstract")
    def parse_plugin(self, plugin_cls: Type[ParsePluginAbstract]):
        self._parse_plugin = plugin_cls()

    @property
    def analysis_plugin(self) -> Optional[AnalysisPluginAbstract]:
        return self._analysis_plugin

    @analysis_plugin.setter
    @check_cls_list("AnalysisPluginAbstract")
    def analysis_plugin(self, plugin_cls_list: List[Type[AnalysisPluginAbstract]]):
        self._analysis_plugin = [plugin_cls()
                                 for plugin_cls in plugin_cls_list]

    def parse(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """对单个命令的内容进行解析"""
        if self._parse_plugin is None:
            raise exception.NotPluginError('parse plugin is None')
        return self._parse_plugin.run(cmd, platform)

    def analysis(self, device: Device) -> AnalysisResult:
        """对设备进行分析, 返回分析结果列表"""
        res = AnalysisResult()
        if not self._analysis_plugin:
            raise exception.NotPluginError('analysis plugin list is empty')
        for plugin in self._analysis_plugin:
            res.merge(plugin.run(device))

        return res

    def input(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """对单个文件进行设备输入"""
        if self._input_plugin is None:
            raise exception.NotPluginError('input plugin is None')
        return self._input_plugin.run(file_path)

    def output(self, devices: DeviceList, file_path: str):
        """对设备列表进行输出"""
        if self._output_plugin is None:
            raise exception.NotPluginError('output plugin is None')
        self._output_plugin.run(devices, file_path)

    @abc.abstractmethod
    def input_dir(self, dir_path: str, expend: str | List = None) -> List[Tuple[Dict[str, str], DeviceInfo]]:
        """对目录中的文件进行设备输入"""
        raise NotImplementedError


class AlarmLevel:
    """告警级别"""
    NORMAL = 0
    FOCUS = 1
    WARNING = 2

    def __init__(self, level: int, message: str = '', plugin_cls: Type[AnalysisPluginAbstract] = None):
        self._level = level
        self.message = message
        self.plugin_cls = plugin_cls

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, level: int):
        if level < AlarmLevel.NORMAL or level > AlarmLevel.WARNING:
            raise exception.AnalysisLevelError
        self._level = level

    @property
    def plugin_name(self) -> str:
        if self.plugin_cls is None:
            return ''
        return self.plugin_cls.__name__

    @property
    def is_warning(self) -> bool:
        """是否为警告级别"""
        return self._level == AlarmLevel.WARNING

    @property
    def is_focus(self) -> bool:
        """是否为关注级别"""
        return self._level == AlarmLevel.FOCUS

    @property
    def is_normal(self) -> bool:
        """是否为正常级别"""
        return self._level == AlarmLevel.NORMAL

    @property
    def above_focus(self) -> bool:
        """是否包含关注级别, 即至少包含关注级别"""
        return self._level >= AlarmLevel.FOCUS

    @property
    def level_str(self) -> str:
        """级别描述"""
        if self._level == AlarmLevel.NORMAL:
            return 'NORMAL'
        elif self._level == AlarmLevel.FOCUS:
            return 'FOCUS'
        elif self._level == AlarmLevel.WARNING:
            return 'WARNING'

    @property
    def doc(self) -> str:
        """返回分析模块的文档"""
        return self.plugin_cls.__doc__.strip() if self.plugin_cls else ''


class AnalysisResult:
    """分析结果"""

    def __init__(self):
        self._result: List[AlarmLevel] = []

    def merge(self, result: AnalysisResult):
        """合并分析结果"""
        self._result.extend(result._result)

    def add(self, level: AlarmLevel):
        """添加分析结果"""
        self._result.append(level)

    def add_normal(self, message: str = ''):
        """添加正常结果"""
        self.add(AlarmLevel(AlarmLevel.NORMAL, message))

    def add_focus(self, message: str = ''):
        """添加关注结果"""
        self.add(AlarmLevel(AlarmLevel.FOCUS, message))

    def add_warning(self, message: str = ''):
        """添加警告结果"""
        self.add(AlarmLevel(AlarmLevel.WARNING, message))

    def get(self, plugin_name: str) -> AnalysisResult:
        """
        获取指定插件的结果

        ``plugin_name`` 可以写的形式：
        - 完整插件名称 (e.g 'AnalysisPluginWithPowerStatus)
        - 下划线 (e.g 'analysis_plugin_with_power_status')
        - 全小写 (e.g 'analysispluginwithpowerstatus')
        - 简写 (e.g 'power status')

        Args:
            - plugin_name: 插件名称

        Return:
            - AlarmLevel: AlarmLevel对象
        """
        ret = AnalysisResult()
        for alarm in self._result:
            if self._short(alarm.plugin_name) == self._short(plugin_name):
                ret.add(alarm)
        return ret

    def _short(self, plugin_name: str) -> str:
        """获取指定插件的简写
        e.g: AnalysisPluginWithPower -> power
        """
        name = plugin_name.lower()
        name = name.replace(' ', '')
        name = name.replace('_', '')
        name = name.replace('analysispluginwith', '')
        return name

    def __getitem__(self, index) -> AlarmLevel:
        return self._result[index]

    def __iter__(self) -> Iterator[AlarmLevel]:
        return iter(self._result)

    def __len__(self) -> int:
        return len(self._result)

    @property
    def include_warning(self) -> bool:
        """是否包含警告级别"""
        for alarm in self._result:
            if alarm.is_warning:
                return True
        return False


class PluginAbstract(abc.ABC):
    """插件的抽象"""

    @abc.abstractmethod
    def run(self):
        raise NotImplementedError

    @property
    def doc(self) -> str:
        """返回分析模块的文档"""
        return self.__doc__.strip() if self.__doc__ else ''

    @property
    def short_name(self) -> str:
        """返回模块的简写"""
        return pascal_case_to_snake_case(self.__class__.__name__.split('With', 1)[-1])


class InputPluginAbstract(PluginAbstract):
    def run(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """对单个文件进行设备输入"""

        with open(file_path, 'r', encoding='gb18030', errors='ignore') as f:
            stream = f.read()
        return self.main(file_path, stream)

    @abc.abstractmethod
    def main(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """输入插件的具体实现
        :params: file_path: 文件的路径
        :params: stream: 文件的内容"""

        raise NotImplementedError


class OutputPluginAbstract(PluginAbstract):

    @dataclass
    class OutputArgs:

        devices: DeviceList  # 设备列表
        path: str  # 输出文件的路径
        output_params: Dict[str, str]  # 输出文件的参数

    def run(self, devices: DeviceList[Device], path: str, output_params: Optional[Dict[str, str]]):
        """对设备列表进行输出
        :params: devices: 设备列表
        :params: path: 输出文件的路径
        :params: output_params: 传递输出文件的参数"""

        self.args = self.OutputArgs(
            devices=devices, path=path, output_params=output_params)
        return self.main()

    @abc.abstractmethod
    def main(self):
        raise NotImplementedError


class ParsePluginAbstract(PluginAbstract):
    def run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        return self.main(cmd, platform)

    @abc.abstractmethod
    def main(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        raise NotImplementedError

    @abc.abstractmethod
    def set_external_templates(self, template_dir: str):
        raise NotImplementedError


class AnalysisPluginAbstract(PluginAbstract):

    @abc.abstractmethod
    def run(self, device: Device) -> AnalysisResult:
        raise NotImplementedError
