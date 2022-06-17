from __future__ import annotations
import os
import glob
import shlex
from rich import print
from typing import Dict, List, Type, TYPE_CHECKING, Tuple
from argparse import ArgumentParser, Namespace

from net_inspect.bootstrap import bootstrap
from net_inspect.analysis_plugin import AnalysisPluginAbc
from net_inspect.func import get_command_from_textfsm
from tests.test_structured_data_againest_analysis_reference_files import \
    analysis_device_with_raw_file, transform_to_dict

if TYPE_CHECKING:
    from net_inspect.domain import Device

PLUGIN_DIR = os.path.join('net_inspect', 'plugins')
TEST_ANALYSIS_PLUGIN_DIR = os.path.join('tests', 'check_analysis_plugins')


class NotFoundErr(Exception):
    ...


def parse_args(command: str = '') -> Namespace:
    args = ArgumentParser()
    args.add_argument('-n', '--name', type=str,
                      help='模块名称，必须指定', required=True)
    args.add_argument('-g', '--generate', action='store_true',
                      help='创建Analysis模块文件')

    args.add_argument('-v', '--vendor', type=str, help='创建指定的厂商的测试文件')
    args.add_argument('-i', '--index', type=int,
                      help='创建第几个测试文件, 可以配合--vendor使用', default=0)
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


def get_plugin_instance(plugin_name: str) -> AnalysisPluginAbc:
    """获取Analysis插件实例"""
    plugin_repository = bootstrap()
    plugin = plugin_repository.get_analysis_plugin(
        plugin_name)  # type: Type[AnalysisPluginAbc]
    if not plugin:
        raise NotFoundErr
    return plugin()  # type: AnalysisPluginAbc


def generate_file(plugin_name: str, give_vendor: str | None, index: int):
    """当没有插件文件的时候，创建插件文件，
    当有插件文件的时候，读取插件文件的插件，并且创建对应的测试文件"""
    file_name = plugin_name + '.py'
    if not os.path.exists(os.path.join(PLUGIN_DIR, file_name)):  # 如果没有插件文件，则创建插件文件
        open(os.path.join(PLUGIN_DIR, file_name), 'w').write('')
        return

    # 如果有插件文件，则读取插件文件的插件，并且创建对应的测试文件
    # 插件仓库

    plugin = get_plugin_instance(plugin_name)
    vendors: Dict[str, List[str]] = {}

    for vendor, fsm_dict in plugin._ntc_templates.items():
        cmd_list = []
        for fsm_name in fsm_dict.keys():
            cmd_list.append(get_command_from_textfsm(
                vendor.PLATFORM, fsm_name))
        vendors[vendor.PLATFORM] = cmd_list

    # 创建测试文件目录
    if not os.path.exists(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)):
        os.mkdir(os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name))

    for vendor_platform, cmd_list in vendors.items():
        # 当给出了厂商的时候，只创建对应的厂商的测试文件
        if give_vendor and vendor_platform != give_vendor:
            continue

        # 创建测试raw文件
        index_str = str(index) if index > 1 else ''
        raw_file = os.path.join(TEST_ANALYSIS_PLUGIN_DIR,
                                plugin_name, vendor_platform + index_str + '.raw')
        if not os.path.exists(raw_file):
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


def main(plugin_name: str, vendor_platform: str = '', index: int = 0) -> List[Tuple[str, Device]]:
    raw_dir = os.path.join(TEST_ANALYSIS_PLUGIN_DIR, plugin_name)
    need_raw_list = []
    for raw_file in glob.iglob(os.path.join(raw_dir, f'*.raw')):
        # 当给出了厂商， 按照index
        if vendor_platform:
            if index == 0:
                need_raw_list.append(raw_file)
            elif index == 1:
                if raw_file.endswith(f'{vendor_platform}.raw'):
                    need_raw_list.append(raw_file)
            elif index > 1:
                if raw_file.endswith(f'{vendor_platform}{index}.raw'):
                    need_raw_list.append(raw_file)
        else:
            need_raw_list.append(raw_file)

    result = []

    for raw_file in need_raw_list:
        device = analysis_device_with_raw_file(raw_file)
        result.append((raw_file, device))

    return result


if __name__ == '__main__':
    command = "-n 'power status' -y"
    args = parse_args(command)
    plugin_name = long_plugin_name(args.name)

    if args.generate:
        generate_file(plugin_name, args.vendor, args.index)
        exit()

    if args.test:
        raw_file_and_devices = main(plugin_name, args.vendor, args.index)
        for raw_file, device in raw_file_and_devices:
            analysis_result = device.analysis_result
            print(raw_file)
            print(transform_to_dict(analysis_result))
            print()
        exit()

    if args.yml:
        generate_yml_file(plugin_name)
        exit()
