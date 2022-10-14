import pytest
import re
from net_inspect.domain import Cluster
from net_inspect import vendor
from net_inspect.plugins.parse_plugin_with_ntc_templates import (
    ParsePluginWithNtcTemplates,
)
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne
from net_inspect.plugin_manager import PluginManager
from net_inspect.analysis_plugin import (
    AnalysisPluginAbc,
    AnalysisResult,
    TemplateInfo,
    AlarmLevel,
    analysis,
)
import net_inspect.exception as exception
from net_inspect.plugins.analysis_plugin_with_power_status import (
    AnalysisPluginWithPowerStatus,
)


class AnalysisPluginWithTest(AnalysisPluginAbc):
    """
    Test for AnalysisPlugin Doc.
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key(
        'huawei_vrp_display_version.textfsm', ['VRP_VERSION', 'product_version']
    )
    def huawei(template: TemplateInfo, result: AnalysisResult):
        """
        Test for huawei version status
        """
        version_reg = r'\d\.\d{3}'
        assert re.match(
            version_reg,
            template['huawei_vrp_display_version.textfsm'][0]['VRP_VERSION'],
        )
        assert re.match(
            version_reg, template['display version'][0]['VRP_VERSION']
        )  # 简写支持

        with pytest.raises(KeyError):
            template['display version'][0]['vrp_version']  # 与给出的大小写应该对应

        with pytest.raises(KeyError):
            template['display version'][0]['PRODUCT_VERSION']  # 与给出的大小写应该对应

        with pytest.raises(exception.NtcTemplateNotDefined):  # 不支持简写
            template['dis ver']

        assert template['display version'][0].get('model') is None  # 不在需求范围内值会被排除

        with pytest.raises(exception.NtcTemplateNotDefined):  # 测试报错
            template['display cpu']

        result.add(AlarmLevel(AlarmLevel.FOCUS, 'test_focus'))
        result.add(AlarmLevel(AlarmLevel.WARNING, 'test_warning'))

    @analysis.vendor(vendor.Cisco)
    @analysis.template_key(
        'cisco_ios_show_processes_memory_sorted.textfsm',
        ['memory_total', 'memory_used'],
    )
    @analysis.template_key(
        'cisco_ios_show_processes_memory.textfsm', ['memory_total', 'memory_used']
    )
    def cisco(template: TemplateInfo, result: AnalysisResult):
        """
        测试多个模板
        """
        # 这个是存在的
        assert template['cisco_ios_show_processes_memory.textfsm']
        assert template['cisco_ios_show_processes_memory.textfsm'][0]['memory_used']

        # sotred 这个是不存在的，但是会给个空列表，if 会判定为 False
        assert not template['cisco_ios_show_processes_memory_sorted.textfsm']

    @analysis.vendor(vendor.Huawei)
    @analysis.base_info('version', 'cpu_usage')
    def huawei_vrp_test(template: TemplateInfo, result: AnalysisResult):
        """
        测试基础信息
        """
        assert template.base_info['version']
        assert template.base_info['cpu_usage']

        with pytest.raises(KeyError):
            template.base_info['memory_usage']

        result.add_normal('test_base_info_normal')


def init_analysis_plugin(
    shared_datadir, file: str = '', analysis_plugins: list = []
) -> Cluster:
    """通用初始化Cluster函数"""
    file = file or 'B_FOO_BAR_AR01_21.1.1.1.diag'  # huawei_vrp

    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    analysis_plugins = analysis_plugins or [AnalysisPluginWithTest]
    plugin_manager = PluginManager(
        input_plugin=input_plugin,
        parse_plugin=parse_plugin,
        analysis_plugin=analysis_plugins,
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
        shared_datadir,
        'HUAWEI_BAD_POWER_21.1.1.1.diag',
        [AnalysisPluginWithPowerStatus],
    )

    device = cluster.devices[0]
    assert len(device._analysis_result) > 0


def test_analysis_result_get_function(shared_datadir):
    """测试AnalysisResult类的get()"""
    cluster = init_analysis_plugin(
        shared_datadir,
        'HUAWEI_BAD_POWER_21.1.1.1.diag',
        [AnalysisPluginWithPowerStatus],
    )
    result = cluster.devices[0].analysis_result
    assert (
        result.get('AnalysisPluginWithPowerStatus')[0].plugin_name
        == 'AnalysisPluginWithPowerStatus'
    )

    assert (
        result.get('analysis_plugin_with_power_status')[0].plugin_name
        == 'AnalysisPluginWithPowerStatus'
    )
    assert (
        result.get('analysispluginwithpowerstatus')[0].plugin_name
        == 'AnalysisPluginWithPowerStatus'
    )
    assert result.get('power status')[0].plugin_name == 'AnalysisPluginWithPowerStatus'


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


def test_analysis_plugin_with_two_templates(shared_datadir):
    """测试有两个template的AnalysisPlugin"""
    cluster = init_analysis_plugin(shared_datadir, 'CISCO_BAD_MEMORY_21.2.2.2.diag')
    result = cluster.devices[0].analysis_result


def test_analysis_plugin_with_base_info(shared_datadir):
    """测试base_info的提取情况"""
    cluster = init_analysis_plugin(shared_datadir)
    result = cluster.devices[0].analysis_result
    for alarm in result:
        if alarm.message == 'test_base_info_normal':
            assert alarm.plugin_name == 'AnalysisPluginWithTest'
            assert alarm.level == AlarmLevel.NORMAL
            return

    assert False
