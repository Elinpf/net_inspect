from net_inspect.domain import Cluster, Device, DeviceList, OutputPluginAbstract
from net_inspect.plugin_manager import PluginManager
from net_inspect.plugins.parse_plugin_with_ntc_templates import (
    ParsePluginWithNtcTemplates,
)
from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne


class OutputPluginForTest(OutputPluginAbstract):
    def main(self, devices: DeviceList, output_path: Device):
        ...


def test_cluster_for_input_file(shared_datadir):
    """输入单个文件"""
    input_plugin = InputPluginWithSmartOne
    plugin_manager = PluginManager(input_plugin=input_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(
        shared_datadir / 'log_files/B_FOO_BAR_DS02_21.2.3.4_20220221170516.diag'
    )
    assert len(cluster.devices) == 1
    assert cluster.devices[0]._device_info.name == 'B_FOO_BAR_DS02'
    assert cluster.devices[0]._device_info.ip == '21.2.3.4'


def test_cluster_for_inputdir(shared_datadir):
    """输入目录"""
    input_plugin = InputPluginWithSmartOne
    plugin_manager = PluginManager(input_plugin=input_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input_dir(shared_datadir / 'log_files')
    assert len(cluster.devices) >= 2  # 获得多个设备


def test_cluster_search_device(shared_datadir):
    input_plugin = InputPluginWithSmartOne
    plugin_manager = PluginManager(input_plugin=input_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input_dir(shared_datadir / 'log_files')
    assert len(cluster.devices) >= 2  # 获得多个设备
    device_list = cluster.search('B_FOO_BAR_DS02')
    assert device_list[0]._device_info.name == 'B_FOO_BAR_DS02'


def test_cluster_for_parse_file(shared_datadir):
    """测试设备搜索功能"""
    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    plugin_manager = PluginManager(input_plugin=input_plugin, parse_plugin=parse_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')
    cluster.parse()
    res = cluster.devices[0].cmds['dis version']._parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_cluster_cmd_search_function(shared_datadir):
    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    plugin_manager = PluginManager(input_plugin=input_plugin, parse_plugin=parse_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')
    cluster.parse()
    cmd = cluster.devices[0].search_cmd('dis ver')
    assert cmd.command == 'dis version'
    res = cmd._parse_result
    assert res[0]['vrp_version'] == '8.180'


def test_cluster_parse_base_info(shared_datadir):
    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    plugin_manager = PluginManager(input_plugin=input_plugin, parse_plugin=parse_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / 'log_files/B_FOO_BAR_AR01_21.1.1.1.diag')
    cluster.parse()
    device1 = cluster.devices[0]
    assert device1.info.hostname == 'B_FOO_BAR_AR01'
    assert device1.info.ip == '21.1.1.1'
    assert device1.info.cpu_usage == '13%'


def test_cluster_parse_not_found_vendor(shared_datadir):
    """测试当遇到不支持的设备时的处理, 会给出一个通用信息，但不会有更多了"""
    input_plugin = InputPluginWithSmartOne
    parse_plugin = ParsePluginWithNtcTemplates
    plugin_manager = PluginManager(input_plugin=input_plugin, parse_plugin=parse_plugin)

    cluster = Cluster()
    cluster.plugin_manager = plugin_manager
    cluster.input(shared_datadir / 'log_files/Default_Vendor_21.1.1.1.diag')
    cluster.parse()
    device1 = cluster.devices[0]
    assert device1.info.hostname == 'Default_Vendor'
    assert device1.info.ip == '21.1.1.1'
    assert device1.info.cpu_usage == ''
