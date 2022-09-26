import pytest
from net_inspect.bootstrap import bootstrap, PluginRepository
from net_inspect.exception import PluginNotSpecify


def test_bootstrap():
    plugins = bootstrap()
    assert type(plugins) == PluginRepository
    assert len(plugins.input_plugins) >= 2
    assert len(plugins.output_plugins) >= 0
    assert len(plugins.parse_plugins) >= 0


def test_plugin_repository_get_plugin():
    """正确获取插件"""
    plugins = bootstrap()
    plugin = plugins.get_input_plugin('input_plugin_with_smartone')
    assert plugin.__name__ == 'InputPluginWithSmartOne'


def test_plugin_repository_get_with_short_name():
    """正确获取简写名字的插件"""
    plugins = bootstrap()
    plugin = plugins.get_input_plugin('smartone')
    assert plugin.__name__ == 'InputPluginWithSmartOne'


def test_plugin_reporsitory_get_plugin_not_found():
    """当名字错误时"""
    plugins = bootstrap()
    with pytest.raises(PluginNotSpecify):
        plugins.get_input_plugin('not_found')


def test_plugin_repository_get_error_type_plugin():
    """当取得类型错误时"""
    plugins = bootstrap()
    with pytest.raises(PluginNotSpecify):
        plugins.get_parse_plugin('input_plugin_with_smartone')
