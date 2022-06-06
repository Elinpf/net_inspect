import pytest
from net_inspect.domain import Device, Cluster
from net_inspect.vendor import Huawei
from net_inspect.plugins.parse_plugin_with_ntc_templates import ParsePluginWithNtcTemplates
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne
from net_inspect.plugin_manager import PluginManager
from net_inspect.analysis_plugin import (
    AnalysisPluginAbc,
    AnalysisResult,
    AlarmLevel
)


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

    def main(self, vendor, template, result) -> AnalysisResult:
        assert vendor == Huawei
        assert template['huawei_vrp_display_version.textfsm'][0]['vrp_version'] == '8.180'
        assert template['display version'][0]['vrp_version'] == '8.180'

        with pytest.raises(KeyError):  # 不支持简写
            template['dis ver']

        assert template['display version'][0].get(
            'model') is None  # 不在需求范围内值会被排除

        with pytest.raises(KeyError):  # 测试报错
            template['display cpu']

        result.add(AlarmLevel(AlarmLevel.FOCUS, 'test_focus'))
        result.add(AlarmLevel(AlarmLevel.WARNING, 'test_warning'))

        return result


def test_analysis_plugin_abstract():
    """测试抽象类"""
    analysis = TestAnalysisPlugin()
    assert analysis._ntc_templates.get(Huawei)


def init_analysis_plugin(shared_datadir, file: str = '', analysis_plugins: list = []) -> Cluster:
    """通用初始化Cluster函数"""
    file = file or 'B_FOO_BAR_AR01_21.1.1.1.diag'

    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    analysis_plugins = analysis_plugins or [TestAnalysisPlugin]
    plugin_manager = PluginManager(
        input_plugin=input_plugin,
        parse_plugin=parse_plugin,
        analysis_plugin=analysis_plugins
    )

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / file)
    cluster.parse()
    cluster.analysis()
    return cluster


def test_analysis_plugin_with_cluster(shared_datadir):
    """测试AnalysisPlugin插件，能够正确获取templates中的信息"""
    cluster = init_analysis_plugin(shared_datadir)
    res = cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'

    result = cluster.devices[0]._analysis_result
    assert len(result) >= 1  # 判断有结果


def test_analysis_plugin_reslut(shared_datadir):
    """测试AnalysisResult类"""
    cluster = init_analysis_plugin(shared_datadir)
    result = cluster.devices[0]._analysis_result
    assert result[0].level == AlarmLevel.FOCUS
    assert result[0].message == 'test_focus'
    assert result[0].plugin_name == 'TestAnalysisPlugin'


def test_analysis_plugin_with_power(shared_datadir):
    """测试AnalysisPluginWithPower插件，能够正确识别Power异常信息"""
    from net_inspect.plugins.analysis_plugin_with_power import AnalysisPluginWithPower
    cluster = init_analysis_plugin(
        shared_datadir, 'HUAWEI_BAD_POWER_21.1.1.1.diag', [AnalysisPluginWithPower])

    device = cluster.devices[0]
    assert len(device._analysis_result) > 0
