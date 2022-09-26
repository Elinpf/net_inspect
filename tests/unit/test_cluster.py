from net_inspect.domain import Cluster, InputPluginResult, DeviceInfo
from net_inspect.plugin_manager import PluginManager


def test_cluster_save_device_with_cmds():
    """测试保存设备"""
    cluster = Cluster()
    input_result = InputPluginResult()
    input_result.add_cmd('cmd1', 'content1')
    input_result.add_cmd('cmd2', 'content2')
    input_result.hostname = 'device1'
    cluster.save_device_with_cmds(input_result)

    assert len(cluster.devices) == 1
    assert cluster.devices[0].cmds['cmd1'].content == 'content1'
    assert cluster.devices[0].cmds['cmd2'].content == 'content2'
    assert cluster.devices[0]._device_info.name == 'device1'


def test_cluster_input(mocker):
    """测试输入"""
    from net_inspect.plugins.input_plugin_with_smartone import InputPluginWithSmartOne
    input_plugin = InputPluginWithSmartOne
    plugin_manager = PluginManager(input_plugin=input_plugin)
    cluster = Cluster()
    cluster.plugin_manager = plugin_manager

    input_result = InputPluginResult()
    input_result.add_cmd('cmd1', 'content1')
    input_result.add_cmd('cmd2', 'content2')
    input_result.hostname = 'device1'

    mocker.patch('net_inspect.domain.InputPluginAbstract.run',
                 return_value=input_result)

    cluster.input('file_path')
    assert len(cluster.devices) == 1
    assert cluster.devices[0].cmds['cmd1'].content == 'content1'
    assert cluster.devices[0].cmds['cmd2'].content == 'content2'
    assert cluster.devices[0]._device_info.name == 'device1'
