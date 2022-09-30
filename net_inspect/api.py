from __future__ import annotations

import os
from typing import TYPE_CHECKING, Dict, List, Optional, Type

from .bootstrap import bootstrap
from .data import pyoption, pystr
from .domain import Cluster
from .logger import LoggerConfig, logger
from .plugin_manager import PluginManager

if TYPE_CHECKING:
    from .base_info import BaseInfo, EachVendorDeviceInfo
    from .domain import (
        Device,
        InputPluginAbstract,
        InputPluginResult,
        OutputPluginAbstract,
        ParsePluginAbstract,
        PluginAbstract,
    )


class NetInspect:
    def __init__(self):
        self._plugins = bootstrap()
        self._plugin_manager = PluginManager()
        self.cluster = Cluster()
        self._logconfig = LoggerConfig()

        self._plugin_manager.parse_plugin = self._plugins.get_parse_plugin(
            pystr.default_parse_plugin
        )
        self._plugin_manager.analysis_plugin = self._plugins.get_analysis_plugin_list()
        self.cluster._plugin_manager = self._plugin_manager

    def enbale_console_log(self, level: str = '', log_format: str = ''):
        """启用控制台日志

        Args:
            level: 日志级别
            log_format: 日志格式，可以为空使用默认值
        """
        self._logconfig.enable_console_log(
            level=level or pyoption.console_log_level,
            log_format=log_format or pyoption.console_format,
        )

    def enable_file_log(
        self,
        file_path: str = '',
        level: str = '',
        rotation: str = '',
        log_format: str = '',
    ):
        """启用文件日志

        Args:
            file_path: 日志文件路径, 为空使用默认值
            level: 日志级别, 为空使用默认值
            rotation: 日志轮转, 为空使用默认值
            log_format: 日志格式, 为空使用默认值
        """

        self._logconfig.enable_file_log(
            file_path or pyoption.logfile_name,
            level=level or 'DEBUG',
            rotation=rotation or pyoption.logfile_rotation,
            log_format=log_format or pyoption.logfile_format,
        )

    def get_all_plugins(self) -> Dict[str, Dict[str, Type[PluginAbstract]]]:
        """获取所有插件

        Returns:
            所有插件以字典的形式返回
        """
        return {
            'input_plugins': self.get_input_plugins(),
            'output_plugins': self.get_output_plugins(),
            'parse_plugins': self.get_parse_plugins(),
            'analysis_plugins': self.get_analysis_plugins(),
        }

    def get_input_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的输入插件"""
        return self._plugins.input_plugins

    def get_output_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的输出插件"""
        return self._plugins.output_plugins

    def get_parse_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的解析插件"""
        return self._plugins.parse_plugins

    def get_analysis_plugins(self) -> Dict[str, Type[PluginAbstract]]:
        """取得所有的分析插件"""
        return self._plugins.analysis_plugins

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

    def set_plugins(
        self,
        input_plugin: Optional[Type[InputPluginAbstract] | str] = None,
        output_plugin: Optional[Type[OutputPluginAbstract] | str] = None,
        parse_plugin: Optional[Type[ParsePluginAbstract] | str] = None,
    ):
        """设置插件

        Args:
            input_plugin: 输入插件
            output_plugin: 输出插件
            parse_plugin: 解析插件
        """
        if input_plugin:
            self.set_input_plugin(input_plugin)
        if output_plugin:
            self.set_output_plugin(output_plugin)
        if parse_plugin:
            self.set_parse_plugin(parse_plugin)

    def set_external_templates(self, templates_dir: str):
        """设置外部模板目录"""
        self._plugin_manager.parse_plugin.set_external_templates(templates_dir)

    @logger.catch(reraise=True)
    def run_input(self, path: str) -> Cluster:
        """运行输入插件, 如果没有指定输入插件则跳过

        Args:
            path: 输入路径

        Returns:
            Cluster: 集群对象
        """

        if not self._plugin_manager.input_plugin:
            logger.info('未指定`input_plugin`, 跳过 `run_input` 函数.')
            return self.cluster

        if os.path.isfile(path):
            self.cluster.input(path)
        elif os.path.isdir(path):
            self.cluster.input_dir(path)
        else:
            raise ValueError('`path`必须是文件或者目录')

        logger.info('输入插件运行完成, 总共发现 {} 台设备.', len(self.cluster.devices))
        return self.cluster

    @logger.catch(reraise=True)
    def run_parse(self) -> Cluster:
        """运行解析插件

        Returns:
            Cluster: 解析后的集群
        """
        self.cluster.parse()
        return self.cluster

    @logger.catch(reraise=True)
    def run_analysis(self) -> Cluster:
        """运行分析插件

        Returns:
            Cluster: 分析后的集群
        """
        self.cluster.analysis()
        return self.cluster

    @logger.catch(reraise=True)
    def run_output(self, file_path: str = '', params: Dict[str, str] = {}):
        """运行输出插件

        Args:
            file_path: 输出文件路径, 为空使用默认值
            params: 传递给output_plugin的参数
        """
        if self._plugin_manager.output_plugin:  # 当有output插件的时候执行
            logger.info(
                f'start run output, plugin is {self._plugin_manager.output_plugin!r}.'
            )
            logger.complete()
            self.cluster.output(file_path, params)
        else:
            logger.info('未指定`output_plugin`, 跳过 `run_output` 函数.')

    def run(
        self,
        input_path: str = '',
        output_file_path: str = '',
        output_plugin_params: Dict[str, str] = {},
        path: str = '',
    ) -> Cluster:
        """执行所有插件

        Args:
            input_path: 输入路径，可以为空
            output_file_path: 输出文件路径, 可以为空
            output_plugin_params: 传递给output_plugin的参数, 可以为空
            path: 废弃参数

        Returns:
            Cluster: 集群对象
        """

        if path:
            import rich

            rich.print('[red]NetInspect.run: `path`参数已废弃, 请使用`input_path`参数代替.[/]')
            input_path = path

        self.run_input(input_path)
        self.run_parse()
        self.run_analysis()
        self.run_output(output_file_path, output_plugin_params)

        return self.cluster

    def add_device_with_raw_data(
        self, hostname: str, ip: str = '', cmd_contents: Dict[str, str] = {}
    ):
        """添加设备到集群中

        Args:
            hostname: 主机名
            ip: 管理ip, 可以为空
            cmd_contents: 命令内容
        """
        self.cluster.add_device_with_raw_data(hostname, ip, cmd_contents)

    def add_device(self, input_plugin_result: InputPluginResult):
        """添加设备到集群中

        Args:
            input_plugin_result: InputPluginResult的实例
        """
        self.cluster.add_device_use_input_plugin_result(input_plugin_result)

    def search(self, device_name: str) -> List[Device]:
        """搜索设备

        Args:
            device_name: 设备名称

        Returns:
            设备列表
        """

        return self.cluster.search(device_name)

    def get_base_info(self) -> List[BaseInfo]:
        """获取所有设备的基本信息

        Returns:
            List[BaseInfo]: 基本信息列表
        """

        ret = []
        for device in self.cluster.devices:
            ret.append(device.info)

        return ret

    def set_base_info_handler(self, handler: Type[EachVendorDeviceInfo]):
        """设置设备基本信息处理器

        Args:
            handler: 设备基本信息处理器
        """
        self.cluster.base_info_handler = handler()
