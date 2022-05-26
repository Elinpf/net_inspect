from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple, Type, Optional, Iterator
from thefuzz import process, fuzz

from .vendor import DefaultVendor
from .exception import TemplateError, NotPluginError
from .logger import log


class Cluster:
    """作为设备的集合"""

    def __init__(self):
        self._plugin_manager: PluginManagerAbc = None
        self.devices: DeviceList[Device] = DeviceList()

    def parse(self):
        """递归对每个设备的命令进行解析"""
        self.devices.parse()

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
        device_cls.device_info = cmd_contents_and_deviceinfo[1]  # 保存设备信息
        self.devices.append(device_cls)

    def output(self, file_path: str, params: Optional[Dict[str, str]] = None):
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

    def parse(self):
        """递归对每个设备的命令进行解析"""
        for device in self._devices:  # type: Device
            device.parse()

    def search(self, device_name: str) -> List[Device]:
        """查找设备

        :param device_name: 设备信息
        :return: 设备列表"""
        return [device for device in self._devices if device_name in device.device_info.name]


@dataclass
class DeviceInfo:
    """设备信息"""
    name: str
    ip: str = ''  # manager_ip


class Device:
    """作为设备的抽象"""

    def __init__(self):
        self.cmds: Dict[str, Cmd] = {}
        self._vendor: DefaultVendor = DefaultVendor
        self._plugin_manager: PluginManagerAbc = None
        self._device_info: DeviceInfo = None

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    @device_info.setter
    def device_info(self, device_info: DeviceInfo):
        self._device_info = device_info

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

        for _, cmd in self.cmds.items():
            try:
                parse_result = self._plugin_manager.parse(
                    cmd, self.vendor.PLATFORM)
                cmd.update_parse_reslut(parse_result)
            except TemplateError as e:
                log.debug(str(e))
                continue

    def search_cmd(self, cmd_name: str) -> Cmd:
        """使用模糊查询

        :param cmd_name: 命令名称
        :return: 命令"""
        search_result = process.extract(cmd_name, self.cmds.keys(
        ), scorer=fuzz.token_set_ratio)
        cmd_len = len(cmd_name.strip().split(' '))

        for cmd, score in search_result:  # 判断命令的长度是否符合
            if score >= 60 and len(cmd.split(' ')) == cmd_len:
                return self.cmds[cmd]

        return None


class Cmd:
    """用于存放命令名称，以及命令的内容，等待后续的解析
    在解析完成后删除命令的内容,并存放应有的解析内容"""

    def __init__(self, cmd: str):
        """ :params: cmd: 命令的完整名称"""
        self.command: str = cmd
        self._content: str = ''
        self._parse_result: List[Dict[str, str]] = {}

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, stream: str):
        self._content = stream

    def update_parse_reslut(self, result: List[Dict[str, str]]):
        """在取到解析结果后，更新解析结果，并且删除命令的内容释放空间"""
        self._parse_result = result
        self._content = ''


class PluginManagerAbc(abc.ABC):
    """对插件的管理的抽象接口, 管理output和parse"""

    def __init__(self,
                 input_plugin: Optional[Type[InputPluginAbstract]] = None,
                 output_plugin: Optional[Type[OutputPluginAbstract]] = None,
                 parse_plugin: Optional[Type[ParsePluginAbstract]] = None):
        self._input_plugin: Optional[InputPluginAbstract] = None
        self._output_plugin: Optional[OutputPluginAbstract] = None
        self._parse_plugin: Optional[ParsePluginAbstract] = None

        if input_plugin:
            self.input_plugin = input_plugin
        if output_plugin:
            self.output_plugin = output_plugin
        if parse_plugin:
            self.parse_plugin = parse_plugin

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

    def parse(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """对单个命令的内容进行解析"""
        if self._parse_plugin is None:
            raise NotPluginError('parse plugin is None')
        return self._parse_plugin.run(cmd, platform)

    def input(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """对单个文件进行设备输入"""
        if self._input_plugin is None:
            raise NotPluginError('input plugin is None')
        return self._input_plugin.run(file_path)

    def output(self, devices: DeviceList, file_path: str):
        """对设备列表进行输出"""
        if self._output_plugin is None:
            raise NotPluginError('output plugin is None')
        self._output_plugin.run(devices, file_path)

    @abc.abstractmethod
    def input_dir(self, dir_path: str, expend: str | List = None) -> List[Tuple[Dict[str, str], DeviceInfo]]:
        """对目录中的文件进行设备输入"""
        raise NotImplementedError


class PluginAbstract(abc.ABC):
    """插件的抽象"""

    def run(self):
        return self.run()

    @abc.abstractmethod
    def _run(self):
        raise NotImplementedError


class InputPluginAbstract(PluginAbstract):
    def run(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """对单个文件进行设备输入"""

        with open(file_path, 'r') as f:
            stream = f.read()
        return self._run(file_path, stream)

    @abc.abstractmethod
    def _run(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """输入插件的具体实现
        :params: file_path: 文件的路径
        :params: stream: 文件的内容"""

        raise NotImplementedError


class OutputPluginAbstract(PluginAbstract):
    def run(self, devices: DeviceList[Device], path: str, params: Optional[Dict[str, str]] = None):
        """对设备列表进行输出
        :params: devices: 设备列表
        :params: path: 输出文件的路径
        :params: params: 输出文件的参数"""
        return self._run(devices, path, params)

    @abc.abstractmethod
    def _run(self, devices: DeviceList[Device], path: str, params: Optional[Dict[str, str]] = None):
        raise NotImplementedError


class ParsePluginAbstract(PluginAbstract):
    def run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        return self._run(cmd, platform)

    @abc.abstractmethod
    def _run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        raise NotImplementedError
