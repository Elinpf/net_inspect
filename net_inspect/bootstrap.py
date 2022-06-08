from __future__ import annotations

from .plugins import autoload_plugin, PluginRepository
from .domain import (
    InputPluginAbstract,
    OutputPluginAbstract,
    ParsePluginAbstract
)

from .analysis_plugin import AnalysisPluginAbc


def bootstrap() -> PluginRepository:
    """加载启动项"""
    autoload_plugin()

    plugin_abc = (InputPluginAbstract, OutputPluginAbstract,
                  ParsePluginAbstract, AnalysisPluginAbc)
    plugins = []
    for plugin_abstract in plugin_abc:
        temp = plugin_abstract.__subclasses__()
        plugins.append({t.__name__: t for t in temp})

    return PluginRepository(*plugins)
