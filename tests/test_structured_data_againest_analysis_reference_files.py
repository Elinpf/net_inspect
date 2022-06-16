from ast import parse
import glob
import os
import re
from turtle import st
from typing import List, Tuple, Dict
import pytest
import yaml

from net_inspect.domain import Device, InputPluginAbstract, DeviceInfo, AnalysisResult
from net_inspect.vendor import DefaultVendor
from net_inspect.plugin_manager import PluginManager
from net_inspect.plugins.parse_plugin_with_ntc_templates import ParsePluginWithNtcTemplates
from net_inspect.bootstrap import bootstrap

command_line_reg = r'^-------------------------(?P<cmd>[^-].*?)-------------------------$'


class InputPluginWithTestRawFile(InputPluginAbstract):

    def main(self, file_path: str, stream: str) -> Tuple[Dict[str, str], DeviceInfo]:

        cmd_dict = {}
        content = []
        command = ''

        for line in stream.splitlines():
            if re.match(command_line_reg, line):
                if command:  # 当有命令的时候，说明是上一个命令的结尾，要保存
                    cmd_dict[command] = '\n'.join(content)
                command = re.match(command_line_reg, line).group('cmd')
                content.clear()  # 清空内容
                continue
            content.append(line)

        if content:
            cmd_dict[command] = '\n'.join(content)

        return cmd_dict, DeviceInfo('TestDevice', '')


def return_test_raw_files() -> List[str]:
    check_plugins_path = os.path.join('tests', 'check_analysis_plugins')
    return glob.glob(os.path.join(check_plugins_path, '*', '*.raw'))


@pytest.fixture(scope="function", params=return_test_raw_files())
def load_analysis_test(request):
    """Return each *.raw file to run tests on."""
    return request.param


def test_raw_against_mock(load_analysis_test):
    """Test that the raw file is parsed correctly."""
    processed, reference = raw_analysis_test(load_analysis_test)


def raw_analysis_test(raw_file: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    plugin_name = raw_file.split(os.path.sep)[2]
    device = set_device(raw_file)
    set_analysis_plugin(device, plugin_name)
    device.parse()
    device.analysis()
    analysis_result_load(device, raw_file)


def set_device(raw_file: str) -> Device:
    """设置初始的设备"""
    platform = re.match(r'(.*?)\d*\.raw', os.path.basename(raw_file)).group(1)
    vendor_class = None
    for vendor in DefaultVendor.__subclasses__():
        if vendor.PLATFORM == platform:
            vendor_class = vendor
            break

    if vendor_class is None:
        raise ValueError(
            'No vendor class found for raw file: {}'.format(raw_file))

    device = Device()
    device._plugin_manager = PluginManager(
        input_plugin=InputPluginWithTestRawFile, parse_plugin=ParsePluginWithNtcTemplates)
    cmd_contents_and_deviceinfo = device._plugin_manager.input(raw_file)

    device.save_to_cmds(cmd_contents_and_deviceinfo[0])  # 保存命令信息
    device.device_info = cmd_contents_and_deviceinfo[1]  # 保存设备信息
    return device


def set_analysis_plugin(device: Device, plugin_name: str):
    """设置分析的插件"""
    plugin_repository = bootstrap()
    plugin_class = plugin_repository.get_analysis_plugin(plugin_name)
    device._plugin_manager.analysis_plugin = [plugin_class]


def analysis_result_load(device: Device, raw_file: str) -> Tuple[dict, dict]:
    yml_file = raw_file.replace('.raw', '.yml')
    structured = transform_to_dict(device.analysis_result)
    with open(yml_file, 'r') as data:
        reference = yaml.safe_load(data.read())
    return structured, reference['analysis_sample']


def transform_to_dict(analysis_result: AnalysisResult) -> List[dict]:
    """将分析结果转换成字典"""
    result_dict = []
    for result in analysis_result:
        result_dict.append({'level': result.level, 'message': result.message})
    return result_dict
