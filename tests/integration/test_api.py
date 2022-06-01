import pytest
from net_inspect.api import NetInspect
from net_inspect.exception import NotPluginError
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne


def test_run_input(shared_datadir):
    """测试单个文件输入插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.run_input(shared_datadir /
                  'log_files/B_FOO_BAR_DS02_21.2.3.4_20220221170516.diag')
    assert len(net.cluster.devices) == 1


def test_run_input2(shared_datadir):
    """测试多个文件输入插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.run_input(shared_datadir / 'log_files')
    assert len(net.cluster.devices) >= 2


def test_run_input_with_class(shared_datadir):
    """测试类型的输入插件"""
    net = NetInspect()
    net.set_input_plugin(InputPluginWithSmartOne)
    net.run_input(shared_datadir / 'log_files')
    assert len(net.cluster.devices) >= 2


def test_run_input_with_wrong_name(shared_datadir):
    """测试错误的输入插件"""
    net = NetInspect()
    with pytest.raises(NotPluginError):
        net.set_input_plugin('not_found')
        net.run_input(shared_datadir / 'log_files')


def test_run_parse(shared_datadir):
    """显示的测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.set_parse_plugin('ntc_templates')
    net.run_input(shared_datadir /
                  'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    net.run_parse()
    res = net.cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_run_parse_with_default(shared_datadir):
    """测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.run_input(shared_datadir /
                  'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    net.run_parse()
    res = net.cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_run_parse_with_default2(shared_datadir):
    """测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    cluster = net.run_input(shared_datadir /
                            'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    cluster.parse()
    res = cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'
