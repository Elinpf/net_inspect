from __future__ import annotations

import glob
import os
import shlex
from argparse import ArgumentParser, Namespace
from typing import TYPE_CHECKING, List, Tuple

from rich import print

from net_inspect.analysis_plugin import analysis
from net_inspect.bootstrap import bootstrap
from net_inspect.func import get_command_from_textfsm, snake_case_to_pascal_case
from tests.test_structured_data_againest_analysis_reference_files import (
    analysis_device_with_raw_file, transform_to_dict)

if TYPE_CHECKING:
    from net_inspect.domain import Device

PLUGIN_DIR = os.path.join('net_inspect', 'plugins')
TEST_ANALYSIS_PLUGIN_DIR = os.path.join('tests', 'check_analysis_plugins')


class NotFoundErr(Exception):
    ...


def parse_args(command: str = '') -> Namespace:
    args = ArgumentParser()
    args.add_argument('-p', '--plugin-name', type=str,
                      help='模块名称，必须指定', required=True)
    args.add_argument('-g', '--generate', action='store_true',
                      help='创建Analysis模块文件')
    args.add_argument('-v', '--vendor-platform', type=str, help='指定厂商平台')
    args.add_argument('-f', '--function', type=str, help='指定测试文件的分析函数')
    args.add_argument('-i', '--index', type=int,
                      help='创建第几个测试文件', default=0)
    args.add_argument('-t', '--test', help='测试模块', action='store_true')
    args.add_argument('-y', '--yml', help='创建yml文件', action='store_true')

    if command:
        return args.parse_args(shlex.split(command))

    return args.parse_args()


def long_plugin_name(name: str) -> str:
    """将模块名称转化为文件名的格式"""
    name = name.lower()
    name = name.replace(' ', '_')
    if not name.startswith('analysis_plugin_with_'):
        name = 'analysis_plugin_with_' + name

    return name


def plugin_file_content(plugin_name: str) -> str:
    content = f'''from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis
from ..func import match_lower

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class {snake_case_to_pascal_case(plugin_name)}(AnalysisPluginAbc):
    """
    在这里填写插件检查信息
    """'''
    return content


def generate_file(plugin_name: str, give_function: str | None, index: int):
    """当没有插件文件的时候，创建插件文件，
    当有插件文件的时候，读取插件文件的插件，并且创建对应的测试文件"""
    file_name = plugin_name + '.py'
    if not os.path.exists(os.path.join(PLUGIN_DIR, file_name)):  # 如果没有插件文件，则创建插件文件
        open(os.path.join(PLUGIN_DIR, file_name), 'w').write(
            plugin_file_content(plugin_name))
        return

    # 如果有插件文件，则读取插件文件的插件，并且创建对应的测试文件
    # 获取所需要的分析函数信息
    if not give_function:
        func_list = analysis.filter(plugin_name=plugin_name)
    else:
        func_list = analysis.filter(
            plugin_name=plugin_name, function_name=give_function)

    if not func_list:
        print('[-] 没有找到对应的分析函数')
        exit()

    # 创建测试文件目录
    if not os.path.exists(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)):
        os.mkdir(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name))

    for func_info in func_list:

        # 拼接测试raw文件名称
        index_str = str(index) if index > 1 else ''
        raw_file = os.path.join(TEST_ANALYSIS_PLUGIN_DIR,
                                plugin_name, func_info.vendor_platform + index_str + '.raw')

        # 如果没有创建过，则创建
        if not os.path.exists(raw_file):
            textfsm_list = [row[0] for row in func_info.template_keys_list]
            cmd_list = [get_command_from_textfsm(
                func_info.vendor_platform, textfsm) for textfsm in textfsm_list]
            open(raw_file, 'w').write(write_cmds(cmd_list))


def write_cmds(cmd_list: list):
    """插入命令到文件中"""
    for i, cmd in enumerate(cmd_list):
        cmd_list[i] = f'-------------------------{cmd}-------------------------'

    return '\n\n\n\n'.join(cmd_list)


def generate_yml_file(plugin_name: str):
    """创建供于参考的yml文件"""
    from generate_yaml import ensure_yaml_standards
    raw_dir = os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)
    for raw_file in glob.iglob(os.path.join(raw_dir, '*.raw')):
        device = analysis_device_with_raw_file(raw_file)
        yml_file = raw_file.replace('.raw', '.yml')
        ret = transform_to_dict(device.analysis_result)
        with open(yml_file, 'w') as f:
            ensure_yaml_standards({'analysis_sample': ret}, yml_file)
        # 打印写入的内容
        print(yml_file)
        print(ret)
        print()


def main(plugin_name: str, function_name: str = '', index: int = 0) -> List[Tuple[str, Device]]:
    raw_dir = os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)
    need_raw_list = []
    for raw_file in glob.iglob(os.path.join(raw_dir, f'*.raw')):
        # 当给出了明确需要测试的分析函数名称， 按照index来测试
        if function_name:
            if index > 1:
                if raw_file.endswith(f'{function_name}{index}.raw'):
                    need_raw_list.append(raw_file)
            else:
                if raw_file.endswith(f'{function_name}.raw'):
                    need_raw_list.append(raw_file)
        else:
            need_raw_list.append(raw_file)

    result = []

    for raw_file in need_raw_list:
        device = analysis_device_with_raw_file(raw_file)
        result.append((raw_file, device))

    return result


if __name__ == '__main__':
    bootstrap()
    command = ''
    # command = "-p 'power status' -f 'maipu_mypower' -t"
    args = parse_args(command)
    plugin_name = long_plugin_name(args.plugin_name)

    if args.generate:
        generate_file(plugin_name, args.function, args.index)
        exit()

    if args.test:
        raw_file_and_devices = main(
            plugin_name, args.function, args.index)
        for raw_file, device in raw_file_and_devices:
            analysis_result = device.analysis_result
            print(raw_file)
            print(transform_to_dict(analysis_result))
            print()
        exit()

    if args.yml:
        generate_yml_file(plugin_name)
        exit()
