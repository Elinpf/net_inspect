import pytest
from net_inspect.api import NetInspect
from net_inspect.base_info import BaseInfo, EachVendorDeviceInfo
from net_inspect.domain import Device, InputPluginResult
from net_inspect import vendor
from net_inspect.exception import PluginNotSpecify
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne


def test_run_input(shared_datadir):
    """测试单个文件输入插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.run_input(
        shared_datadir / 'log_files/B_FOO_BAR_DS02_21.2.3.4_20220221170516.diag'
    )
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
    with pytest.raises(PluginNotSpecify):
        net.set_input_plugin('not_found')
        net.run_input(shared_datadir / 'log_files')


def test_run_parse(shared_datadir):
    """显示的测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.set_parse_plugin('ntc_templates')
    net.run_input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    net.run_parse()
    res = net.cluster.devices[0].cmds['dis version'].parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_run_parse_with_default(shared_datadir):
    """测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.run_input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    net.run_parse()
    res = net.cluster.devices[0].cmds['dis version'].parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_run_parse_with_default2(shared_datadir):
    """测试单个文件解析插件"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    cluster = net.run_input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')

    cluster.parse()
    res = cluster.devices[0].cmds['dis version'].parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_run_analysis(shared_datadir):
    """执行分析测试"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    cluster = net.run_input(shared_datadir / 'log_files/HUAWEI_BAD_POWER_21.1.1.1.diag')

    cluster.parse()
    cluster.analysis()
    result = cluster.devices[0].analysis_result
    assert len(result) > 0  # 保证至少有一个结果


def test_add_device_with_input_plugin_result():
    """使用InputPluginResult手动添加设备"""

    result = InputPluginResult()
    result.hostname = 'Device1'
    result.ip = '192.168.1.1'
    result.add_cmd('cmd1', 'content1')
    result.add_cmd('cmd2', 'content2')
    result.add_cmd('display clock', "2021-03-19 10:23:08+08:00")
    result.vendor = vendor.Huawei

    net = NetInspect()
    net.add_device(result)
    assert len(net.cluster.devices) == 1

    device = net.search('Device1')
    assert device[0].search_cmd('cmd1').content == 'content1'

    assert device[0].vendor == vendor.Huawei


def test_add_device_with_raw_data():
    """使用字典方式添加设备"""
    cmds = {'cmd1': 'content1', 'cmd2': 'content2'}
    net = NetInspect()
    net.add_device_with_raw_data(
        hostname='Device1', ip='192.168.1.1', cmd_contents=cmds
    )

    assert len(net.cluster.devices) == 1

    device = net.search('Device1')
    assert device[0].search_cmd('cmd1').content == 'content1'


class AppendClock(BaseInfo):
    clock: str = ''  # 巡检时间


class EachVendorWithClock(EachVendorDeviceInfo):

    base_info_class = AppendClock

    def do_huawei_vrp_baseinfo_2(self, device: Device, info: AppendClock):
        with device.search_cmd('display clock') as cmd:
            if cmd.parse_result:
                row = cmd.parse_result[0]
                info.clock = f'{row["year"]}-{row["month"]}-{row["day"]} {row["time"]}'


def test_set_base_info_handler(shared_datadir):
    """测试设置扩展基本信息处理器, 添加了新的clock信息"""
    net = NetInspect()
    net.set_input_plugin('smartone')
    net.set_base_info_handler(EachVendorWithClock)
    cluster = net.run_input(shared_datadir / 'log_files/HUAWEI_BAD_POWER_21.1.1.1.diag')

    cluster.parse()
    cluster.analysis()

    info = net.cluster.devices[0].info  # type: AppendClock
    assert info.clock == '2022-02-21 16:22:26'
