from net_inspect.plugin_manager import PluginManager
from net_inspect.bootstrap import bootstrap


def test_plugin_manager_get_plugins():
    """测试获取插件"""
    plugins = bootstrap()
    p = plugins.get_plugins('input_plugin_with_smartone',
                            parse_plugin_name='parse_plugin_with_ntc_templates')
    manager = PluginManager(*p)
    assert manager._input_plugin.__class__.__name__ == 'InputPluginWithSmartOne'
