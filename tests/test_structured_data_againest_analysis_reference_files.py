import glob
import os
import re
from typing import Dict, List, Tuple

import pytest
import yaml
from net_inspect.analysis_plugin import analysis
from net_inspect.base_info import EachVendorDeviceInfo
from net_inspect.bootstrap import bootstrap
from net_inspect.data import pypath
from net_inspect.domain import (
    AnalysisResult,
    Device,
    InputPluginAbstract,
    InputPluginResult,
)
from net_inspect.func import pascal_case_to_snake_case
from net_inspect.plugin_manager import PluginManager
from net_inspect.plugins.parse_plugin_with_ntc_templates import (
    ParsePluginWithNtcTemplates,
)
from net_inspect.vendor import DefaultVendor

command_line_reg = (
    r'^-------------------------(?P<cmd>[^-].*?)-------------------------$'
)


class InputPluginWithTestRawFile(InputPluginAbstract):
    def main(self, file_path: str, stream: str) -> InputPluginResult:
        result = InputPluginResult()

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

        result.cmd_dict = cmd_dict
        result.hostname = 'TestDevice'
        return result


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

    correct_number_of_entries_test(processed, reference)
    all_entries_have_the_same_keys_test(processed, reference)
    correct_data_in_entries_test(processed, reference)


def raw_analysis_test(raw_file: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """创建设备，设置分析插件，运行分析，返回分析结果和参考结果"""
    device = analysis_device_with_raw_file(raw_file)
    return analysis_result_load(device, raw_file)


def analysis_device_with_raw_file(raw_file: str) -> Device:
    """执行分析测试"""
    plugin_name = raw_file.split(os.path.sep)[2]
    device = set_device(raw_file)
    set_analysis_plugin(device, plugin_name)
    base_info_handler = EachVendorDeviceInfo()
    device.parse()
    device.info = base_info_handler.run_baseinfo_func(device)
    device.analysis()
    return device


def set_device(raw_file: str) -> Device:
    """设置初始的设备"""
    platform = re.match(r'(.*?)\d*\.raw', os.path.basename(raw_file)).group(1)
    vendor_class = None
    for vendor in DefaultVendor.__subclasses__():
        if vendor.PLATFORM == platform:
            vendor_class = vendor
            break

    if vendor_class is None:
        raise ValueError('No vendor class found for raw file: {}'.format(raw_file))

    device = Device()
    device._vendor = vendor_class
    device._plugin_manager = PluginManager(
        input_plugin=InputPluginWithTestRawFile,
        parse_plugin=ParsePluginWithNtcTemplates,
    )
    input_result = device._plugin_manager.input(raw_file)

    device.save_to_cmds(input_result.cmd_dict)  # 保存命令信息
    device._device_info = input_result._device_info  # 保存设备信息
    return device


def set_analysis_plugin(device: Device, plugin_name: str):
    """设置分析的插件"""
    plugin_repository = bootstrap()
    plugin_class = plugin_repository.get_analysis_plugin(plugin_name)
    device._plugin_manager.analysis_plugin = [plugin_class]


def analysis_result_load(device: Device, raw_file: str) -> Tuple[dict, dict]:
    yml_file = raw_file.replace('.raw', '.yml')
    structured = transform_to_dict(device.analysis_result)
    with open(yml_file, 'r', encoding='utf-8') as data:
        reference = yaml.safe_load(data.read())
    return structured, reference['analysis_sample']


def transform_to_dict(analysis_result: AnalysisResult) -> List[dict]:
    """将分析结果转换成字典"""
    result_dict = []
    for result in analysis_result:
        result_dict.append({'level': result.level, 'message': result.message})
    return result_dict


def correct_number_of_entries_test(processed, reference):
    """Test that the number of entries returned are the same as the control.

    This will create a test for each of the files in the test_collection
    variable.
    """
    assert len(processed) == len(reference)


def all_entries_have_the_same_keys_test(processed, reference):
    """Test that the keys of the returned data are the same as the control.

    This will create a test for each of the files in the test_collection
    variable.
    """
    for i in range(len(processed)):
        proc = set(processed[i].keys())
        ref = set(reference[i].keys())
        diff = proc.symmetric_difference(ref)
        assert not diff, "Key diffs: " + ", ".join(diff)


def correct_data_in_entries_test(processed, reference):
    """Test that the actual data in each entry is the same as the control.

    This will create a test for each of the files in the test_collection
    variable.
    """
    # Can be uncommented if we don't care that the parsed data isn't
    # in the same order as the raw data
    # reference = sorted(reference)
    # processed = sorted(processed)

    for i in range(len(reference)):
        for key in reference[i].keys():
            assert (
                str(processed[i][key]) == reference[i][key]
            ), "entry #{0}, key: {1}".format(i, key)


def test_all_functions_has_a_test():
    """所有AnalysisPlugin中的测试函数至少需要一个raw测试"""
    bootstrap()
    for func_info in analysis.store:
        if 'test' in func_info.plugin_name.lower():  # 跳过做测试的插件
            continue

        plugin_name, func_name = func_info.plugin_name, func_info.function_name

        # 如果是分析函数，则检查是否有测试文件
        template_name_snake_case = pascal_case_to_snake_case(plugin_name)
        test_raw_file_path = os.path.join(
            pypath.project_path,
            'tests',
            'check_analysis_plugins',
            template_name_snake_case,
            func_name + '.raw',
        )

        assert os.path.exists(test_raw_file_path)
