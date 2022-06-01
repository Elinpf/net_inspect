import pytest
from net_inspect.domain import Device, Cluster
from net_inspect.analysis_plugin import AnalysisPluginAbc, Level
from net_inspect.vendor import Huawei
from net_inspect.plugins.parse_plugin_with_ntc_templates import ParsePluginWithNtcTemplates
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne
from net_inspect.plugin_manager import PluginManager


class TestAnalysisPlugin(AnalysisPluginAbc):
    def __init__(self):
        super().__init__(
            ntc_templates={
                Huawei: {
                    'huawei_vrp_display_version.textfsm':
                        [
                            'VRP_VERSION',
                            'PRODUCT_VERSION'
                        ]
                }
            }
        )

    def main(self, vendor, template) -> Level:
        assert vendor == Huawei
        assert template['huawei_vrp_display_version.textfsm'][0]['vrp_version'] == '8.180'
        assert template['display version'][0]['vrp_version'] == '8.180'

        with pytest.raises(KeyError):  # 不支持简写
            template['dis ver']

        assert template['display version'][0].get(
            'model') is None  # 不在需求范围内值会被排除

        with pytest.raises(KeyError):  # 测试报错
            template['display cpu']


def test_analysis_plugin_abstract():
    """测试抽象类"""
    analysis = TestAnalysisPlugin()
    assert analysis._ntc_templates.get(Huawei)


def test_analysis_plugin_with_device(shared_datadir):
    """测试AnalysisPlugin插件，能够正确获取templates中的信息"""
    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    analysis_plugin = TestAnalysisPlugin
    plugin_manager = PluginManager(
        input_plugin=input_plugin,
        parse_plugin=parse_plugin,
        analysis_plugin=analysis_plugin
    )

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir /
                  'B_FOO_BAR_AR01_21.1.1.1.diag')
    cluster.parse()
    res = cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'

    cluster.analysis()
