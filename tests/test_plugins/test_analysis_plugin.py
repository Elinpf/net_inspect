import pytest
import logging
from net_inspect.domain import Cluster
from net_inspect import vendor
from net_inspect.plugins.parse_plugin_with_ntc_templates import ParsePluginWithNtcTemplates
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne
from net_inspect.plugin_manager import PluginManager
from net_inspect.analysis_plugin import (
    AnalysisPluginAbc,
    AnalysisResult,
    TemplateInfo,
    AlarmLevel,
    analysis
)
import net_inspect.exception as exception
from net_inspect.plugins.analysis_plugin_with_power_status import AnalysisPluginWithPowerStatus


class AnalysisPluginWithTest(AnalysisPluginAbc):
    """
    Test for AnalysisPlugin Doc.
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_version.textfsm', ['VRP_VERSION', 'PRODUCT_VERSION'])
    def huawei(template: TemplateInfo, result: AnalysisResult):
        """
        Test for huawei version status
        """
        assert template['huawei_vrp_display_version.textfsm'][0]['vrp_version'] == '8.180'
        assert template['display version'][0]['vrp_version'] == '8.180'

        with pytest.raises(exception.NtcTemplateNotDefined):  # 不支持简写
            template['dis ver']

        assert template['display version'][0].get(
            'model') is None  # 不在需求范围内值会被排除

        with pytest.raises(exception.NtcTemplateNotDefined):  # 测试报错
            template['display cpu']

        result.add(AlarmLevel(AlarmLevel.FOCUS, 'test_focus'))
        result.add(AlarmLevel(AlarmLevel.WARNING, 'test_warning'))


def init_analysis_plugin(shared_datadir, file: str = '', analysis_plugins: list = []) -> Cluster:
    """通用初始化Cluster函数"""
    file = file or 'B_FOO_BAR_AR01_21.1.1.1.diag'

    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    analysis_plugins = analysis_plugins or [AnalysisPluginWithTest]
    plugin_manager = PluginManager(
        input_plugin=input_plugin,
        parse_plugin=parse_plugin,
        analysis_plugin=analysis_plugins
    )

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / file)
    cluster.parse()
    analysis.set_only_run_plugins(analysis_plugins)
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
    assert result[0].plugin_name == 'AnalysisPluginWithTest'


def test_analysis_plugin_with_power(shared_datadir):
    """测试AnalysisPluginWithPower插件，能够正确识别Power异常信息"""
    cluster = init_analysis_plugin(
        shared_datadir, 'HUAWEI_BAD_POWER_21.1.1.1.diag', [AnalysisPluginWithPowerStatus])

    device = cluster.devices[0]
    assert len(device._analysis_result) > 0


def test_analysis_result_get_function(shared_datadir):
    """测试AnalysisResult类的get()"""
    cluster = init_analysis_plugin(
        shared_datadir, 'HUAWEI_BAD_POWER_21.1.1.1.diag', [AnalysisPluginWithPowerStatus])
    result = cluster.devices[0].analysis_result
    assert result.get(
        'AnalysisPluginWithPowerStatus')[0].plugin_name == 'AnalysisPluginWithPowerStatus'

    assert result.get(
        'analysis_plugin_with_power_status')[0].plugin_name == 'AnalysisPluginWithPowerStatus'
    assert result.get(
        'analysispluginwithpowerstatus')[0].plugin_name == 'AnalysisPluginWithPowerStatus'
    assert result.get(
        'power status')[0].plugin_name == 'AnalysisPluginWithPowerStatus'


def test_analysi_result_get_function_have_multiple_alarm_level(shared_datadir):
    """测试AnalysisResult.get()方法返回为AnalysisResult类"""
    cluster = init_analysis_plugin(shared_datadir)
    result = cluster.devices[0].analysis_result
    test_result = result.get('AnalysisPluginWithTest')
    assert type(test_result) == AnalysisResult


def test_analysis_plugin_function_doc(shared_datadir):
    """测试AnalysisPlugin类的注释信息"""
    cluster = init_analysis_plugin(shared_datadir)
    result = cluster.devices[0].analysis_result
    doc = result.get('AnalysisPluginWithTest')[0].doc
    assert doc == 'Test for AnalysisPlugin Doc.'


def test_analysis_plugin_get_func_with_error_plugin_or_vendor(caplog):
    """测试StoreTemplateKey.get_func()输入不存在的插件或者vendor"""
    caplog.set_level(logging.DEBUG)

    for func, template in analysis.get_funcs('AnalysisPluginWithNotExist', vendor.Huawei):
        ...  # pragma: no cover
    assert caplog.messages[0] == 'AnalysisWarning -- not found AnalysisPluginWithNotExist in store'
    caplog.clear()

    for func, template in analysis.get_funcs('AnalysisPluginWithTest', vendor.Ruijie):
        ...  # pragma: no cover
    assert caplog.messages[0] == 'AnalysisWarning -- AnalysisPluginWithTest not support vendor Ruijie'
