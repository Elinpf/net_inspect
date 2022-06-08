from __future__ import annotations

from typing import Dict, TYPE_CHECKING, Type, List, Optional
import os

from .bootstrap import bootstrap
from .plugin_manager import PluginManager
from .domain import Cluster
from .data import pystr

if TYPE_CHECKING:
    from .domain import (PluginAbstract, InputPluginAbstract,
                         OutputPluginAbstract, ParsePluginAbstract, Device)


class NetInspect:

    def __init__(self):
        self._plugins = bootstrap()
        self._plugin_manager = PluginManager()
        self.cluster = Cluster()

        self._plugin_manager.parse_plugin = self._plugins.get_parse_plugin(
            pystr.default_parse_plugin)
        self._plugin_manager.analysis_plugin = self._plugins.get_analysis_plugin_list()
        self.cluster._plugin_manager = self._plugin_manager

    def get_all_plugins(self) -> Dict[str, Dict[str, Type[PluginAbstract]]]:
        """获取所有插件"""
        return {'input_plugins': self.get_input_plugins(),
                'output_plugins': self.get_output_plugins(),
                'parse_plugins': self.get_parse_plugins()}

    def get_input_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的输入插件"""
        return self._plugins.input_plugins

    def get_output_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的输出插件"""
        return self._plugins.output_plugins

    def get_parse_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的解析插件"""
        return self._plugins.parse_plugins

    def set_input_plugin(self, plugin_cls: Type[InputPluginAbstract] | str):
        """设置输入插件
        :param plugin_cls: 插件类或者插件名称"""
        if type(plugin_cls) == str:
            plugin_cls = self._plugins.get_input_plugin(plugin_cls)
        self._plugin_manager.input_plugin = plugin_cls

    def set_output_plugin(self, plugin_cls: Type[OutputPluginAbstract] | str):
        """设置输出插件
        :param plugin_cls: 插件类或者插件名称"""
        if type(plugin_cls) == str:
            plugin_cls = self._plugins.get_output_plugin(plugin_cls)
        self._plugin_manager.output_plugin = plugin_cls

    def set_parse_plugin(self, plugin_cls: Type[ParsePluginAbstract] | str):
        """设置解析插件
        :param plugin_cls: 插件类或者插件名称"""
        if type(plugin_cls) == str:
            plugin_cls = self._plugins.get_parse_plugin(plugin_cls)
        self._plugin_manager.parse_plugin = plugin_cls

    def set_plugins(self,
                    input_plugin: Type[InputPluginAbstract] | str,
                    output_plugin: Type[OutputPluginAbstract] | str,
                    parse_plugin: Optional[Type[ParsePluginAbstract]] | str = None):
        """设置插件
        :param input_plugin: 输入插件
        :param output_plugin: 输出插件
        :param parse_plugin: 解析插件"""
        self.set_input_plugin(input_plugin)
        self.set_output_plugin(output_plugin)
        if parse_plugin:
            self.set_parse_plugin(parse_plugin)

    def run_input(self, path: str) -> Cluster:
        """运行输入插件
        :param path: 文件或者目录路径"""

        if os.path.isfile(path):
            self.cluster.input(path)
        elif os.path.isdir(path):
            self.cluster.input_dir(path)
        else:
            raise ValueError('path must be a file or directory')

        return self.cluster

    def run_parse(self) -> Cluster:
        """运行解析插件"""
        self.cluster.parse()
        return self.cluster

    def run_analysis(self) -> Cluster:
        """运行分析插件"""
        self.cluster.analysis()
        return self.cluster

    def run_output(self, file_path: str, params: Optional[Dict[str, str]] = None):
        """运行输出插件"""
        self.cluster.output(file_path, params)

    def run(self, path: str, output_file_path: str, output_plugin_params: Optional[Dict[str, str]] = None) -> Cluster:
        """运行输入解析输出插件
        :param path: 文件或者目录路径
        :param output_file_path: 输出文件路径
        :param output_plugin_params: 输出插件参数

        :return Cluster: 设备列表"""
        self.run_input(path)
        self.run_parse()
        self.run_analysis()
        self.run_output(output_file_path, output_plugin_params)

        return self.cluster

    def search(self, device_name: str) -> List[Device]:
        """搜索设备
        :param device_name: 设备名称
        :return: 设备列表"""
        return self.cluster.search(device_name)
