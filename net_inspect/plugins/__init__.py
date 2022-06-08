from __future__ import annotations
import os
import re

from typing import Dict, TYPE_CHECKING, List, Optional, Type

from . import __file__ as plugin_file

from ..data import pystr
from ..logger import log
from ..domain import PluginAbstract
from ..exception import NotPluginError

if TYPE_CHECKING:
    from ..domain import (
        InputPluginAbstract,
        OutputPluginAbstract,
        ParsePluginAbstract,
        AnalysisPluginAbstract
    )


def autoload_plugin():
    plugin_dir = os.path.dirname(plugin_file)

    for file in os.listdir(plugin_dir):
        if file.endswith(".py") and file != "__init__.py":
            module_name = file[:-3]
            try:
                __import__('.'.join([pystr.software, 'plugins', module_name]))
            except ImportError:
                log.error('Failed to import plugin: {}'.format(module_name))


Input = 'input'
Output = 'output'
Parse = 'parse'
Analysis = 'analysis'


class PluginRepository():
    """插件仓库，存放插件并且提供插件的获取"""

    def __init__(self,
                 input_plugins: Dict[str, InputPluginAbstract],
                 output_plugins: Dict[str, OutputPluginAbstract],
                 parse_plugins: Dict[str, ParsePluginAbstract],
                 analysis_plugins: Dict[str, AnalysisPluginAbstract]):
        self.input_plugins = input_plugins
        self.output_plugins = output_plugins
        self.parse_plugins = parse_plugins
        self.analysis_plugins = analysis_plugins
        self._easy_plugin_name = self._to_easy_plugin_name()

    def _to_easy_plugin_name(self) -> Dict[str, PluginAbstract]:
        """变成一个简单的dict，方便查找"""
        ret = {}
        for plugins in [self.input_plugins, self.output_plugins,
                        self.parse_plugins, self.analysis_plugins]:
            for plugin_name, plugin in plugins.items():
                ret[self._lower_name(plugin_name)] = plugin

        return ret

    def _lower_name(self, name: str):
        """将插件名称转换为小写"""
        name = name.lower()
        name = re.sub(r'[-|_]', '', name)
        name = name.replace('.py', '')
        return name

    def get_plugin(self, ptype: str, name: str) -> PluginAbstract:
        """获取插件
        :param ptype: 插件类型
        :param name: 插件名称"""
        lower_name = self._lower_name(name)

        # 支持简写
        if not lower_name.startswith(f"{ptype}pluginwith"):
            lower_name = f"{ptype}pluginwith{lower_name}"

        if lower_name not in self._easy_plugin_name:
            raise NotPluginError('not found plugin: {}'.format(name))

        plugin = self._easy_plugin_name[lower_name]
        if ptype == Input:
            self._check_plugin(self.input_plugins, plugin)

        elif ptype == Output:
            self._check_plugin(self.output_plugins, plugin)

        elif ptype == Parse:
            self._check_plugin(self.parse_plugins, plugin)

        elif ptype == Analysis:
            self._check_plugin(self.analysis_plugins, plugin)

        else:
            raise ValueError('type must be input, output or parse')

        return plugin

    def _check_plugin(self, plugin_dict: Dict[str, PluginAbstract], plugin: PluginAbstract):
        """检查这个插件是否在plugin_dict中"""
        if plugin not in plugin_dict.values():
            raise NotPluginError(
                'plugin `{}` not in this plugin type list'.format(plugin))

    def get_input_plugin(self, name: str) -> InputPluginAbstract:
        """获取输入插件
        :param name: 插件名称"""
        return self.get_plugin(Input, name)

    def get_output_plugin(self, name: str) -> OutputPluginAbstract:
        """获取输出插件
        :param name: 插件名称"""
        return self.get_plugin(Output, name)

    def get_parse_plugin(self, name: str) -> ParsePluginAbstract:
        """获取解析插件
        :param name: 插件名称"""
        return self.get_plugin(Parse, name)

    def get_analysis_plugin(self, name: str) -> AnalysisPluginAbstract:
        """获取分析插件
        :param name: 插件名称"""
        return self.get_plugin(Analysis, name)

    def get_analysis_plugin_list(self) -> List[AnalysisPluginAbstract]:
        """获取分析插件列表"""
        return list(self.analysis_plugins.values())

    def plugin_list(self, type: str) -> List[str]:
        """获取名称插件列表
        :param type: 插件类型"""
        if type == Input:
            return list(self.input_plugins.keys())
        elif type == Output:
            return list(self.output_plugins.keys())
        elif type == Parse:
            return list(self.parse_plugins.keys())
        elif type == Analysis:
            return list(self.analysis_plugins.keys())
        else:
            raise ValueError('type must be input, output or parse')

    def input_plugin_list(self) -> List[str]:
        """获取输入插件列表"""
        return self.plugin_list(Input)

    def output_plugin_list(self) -> List[str]:
        """获取输出插件列表"""
        return self.plugin_list(Output)

    def parse_plugin_list(self) -> List[str]:
        """获取解析插件列表"""
        return self.plugin_list(Parse)

    def analysis_plugin_list(self) -> List[str]:
        """获取分析插件列表"""
        return self.plugin_list(Analysis)

    def get_plugins(self, input_plugin_name: Optional[str] = None,
                    output_plugin_name: Optional[str] = None,
                    parse_plugin_name: Optional[str] = None
                    ) -> List[Optional[PluginAbstract]]:
        """同时获取三个插件
        :param input_plugin_name: 输入插件名称
        :param output_plugin_name: 输出插件名称
        :param parse_plugin_name: 解析插件名称"""
        return [self.get_input_plugin(input_plugin_name) if input_plugin_name else None,
                self.get_output_plugin(
                    output_plugin_name) if output_plugin_name else None,
                self.get_parse_plugin(parse_plugin_name) if parse_plugin_name else None]
