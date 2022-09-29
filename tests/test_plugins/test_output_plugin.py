import pytest
from net_inspect.domain import OutputPluginAbstract, DeviceList, Device
from net_inspect import exception


class OutputPluginWithTest(OutputPluginAbstract):
    def main(self):
        self.check_args('title', 'name')


def test_output_check_args():
    """测试检查参数"""
    plugin = OutputPluginWithTest()
    device_list = DeviceList()
    device_list.append(Device())
    plugin.run(device_list, path='', output_params={'title': 'test', 'name': 'test'})


def test_output_check_args_with_no_args():
    """测试检查参数不存在的情况"""
    plugin = OutputPluginWithTest()
    device_list = DeviceList()
    device_list.append(Device())
    with pytest.raises(exception.OutputParamsNotGiven):
        plugin.run(device_list, path='', output_params={})
