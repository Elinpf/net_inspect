from __future__ import annotations

import abc
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Type


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

    def output(self, file_path: str):
        """输出到文件

        :param file_path: 文件路径"""
        self.plugin_manager._output_plugin.run(self.devices, file_path)


class DeviceList(list):
    """设备列表"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def _devices(self) -> List[Device]:
        return self

    def parse(self):
        """递归对每个设备的命令进行解析"""
        for device in self._devices:  # type: Device
            device.parse()


@dataclass
class DeviceInfo:
    """设备信息"""
    name: str
    ip: str = ''  # manager_ip


class Device:
    """作为设备的抽象"""

    def __init__(self):
        self.cmds: Dict[str, Cmd] = {}
        self._manufacturer: DefaultManufacturer = DefaultManufacturer
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

        if self.manufacturer is DefaultManufacturer:
            self.check_manufacturer()

    def check_manufacturer(self):
        """检查厂商"""
        manufacturer = self.manufacturer.check_manufacturer(self.cmds)
        self._manufacturer = manufacturer

    @property
    def manufacturer(self) -> Type[DefaultManufacturer]:
        """返回厂商类"""
        return self._manufacturer

    def parse(self):

        for cmd in self.cmds:
            parse_result = self._plugin_manager.parse(
                cmd, self.manufacturer.PLATFORM)
            cmd.update_parse_result(parse_result)


class DefaultManufacturer:
    """默认厂商"""

    PLATFORM = 'default'
    VERSION_COMMAND = None
    KEYWORD_REG = None

    @classmethod
    def check_manufacturer(cls, cmds: Dict[str, Cmd]) -> Type[DefaultManufacturer]:
        """检查确认设备的厂商"""
        for handler in cls.__subclasses__():
            if handler._check_manufacturer(cmds):
                return handler

        return cls

    @classmethod
    def _check_manufacturer(cls, cmds: Dict[str, Cmd]) -> bool:
        """子类用于检查设备的厂商"""
        # TODO 需要有一个方法确认最小命令长度
        if cls.VERSION_COMMAND in cmds.keys():
            return (True if
                    re.search(cls.KEYWORD_REG,
                              cmds[cls.VERSION_COMMAND].content, re.IGNORECASE)
                    else False)

        return False


class Huawei(DefaultManufacturer):

    PLATFORM = 'huawei_os'
    VERSION_COMMAND = 'display version'
    KEYWORD_REG = r'Huawei'


class Cmd:
    """用于存放命令名称，以及命令的内容，等待后续的解析
    在解析完成后删除命令的内容,并存放应有的解析内容"""

    def __init__(self, cmd: str):
        """ :params: cmd: 命令的完整名称"""
        self.command: str = cmd
        self._content: str = ''
        self._parse_result: dict = {}

    @property
    def content(self):
        return self._content

    @content.setter
    def content(self, stream: str):
        self._content = stream

    def parse_reslut(self, result: Dict[str, str]):
        """在取到解析结果后，更新解析结果，并且删除命令的内容释放空间"""
        self._parse_result.update(result)
        self._content = ''


class PluginManagerAbc(abc.ABC):
    """对插件的管理的抽象接口, 管理output和parse"""

    def __init__(self,
                 input_plugin: InputPluginAbstract = None,
                 output_plugin: OutputPluginAbstract = None,
                 parse_plugin: ParsePluginAbstract = None):
        self._input_plugin = input_plugin
        self._output_plugin = output_plugin
        self._parse_plugin = parse_plugin

    def parse(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        """对单个命令的内容进行解析"""
        return self._parse_plugin.run(cmd, platform)

    def input(self, file_path: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """对单个文件进行设备输入"""
        return self._input_plugin.run(file_path)

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

    def _run(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:
        """输入插件的具体实现
        :params: file_path: 文件的路径
        :params: stream: 文件的内容"""

        raise NotImplementedError


class OutputPluginAbstract(PluginAbstract):
    def run(self, devices: DeviceList[Device], file_path: str):
        return self._run(devices, file_path)

    def _run(self, devices: DeviceList[Device], file_path: str):
        raise NotImplementedError


class ParsePluginAbstract(PluginAbstract):
    def run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        return self._run(cmd, platform)

    def _run(self, cmd: Cmd, platform: str) -> Dict[str, str]:
        raise NotImplementedError
