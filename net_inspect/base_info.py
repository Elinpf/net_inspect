from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING, Dict, Callable, List, Tuple, Optional
from rich import print
from . import vendor


if TYPE_CHECKING:
    from .domain import Device


class Singleton(object):
    """单例类继承"""
    _instance = None

    def __new__(class_, *args, **kwargs):
        if not isinstance(class_._instance, class_):
            class_._instance = object.__new__(class_, *args, **kwargs)
        return class_._instance


class EachVendorDeviceInfo(Singleton):
    """可以重载这个类，实现不同的输出格式, 重写或者增加以`do_`开头的方法"""

    analysis_items = [
        ('cpu_status', 'cpu'),
        ('memory_status', 'memory'),
        ('fan_status', 'fan'),
        ('power_status', 'power')
    ]

    @dataclass
    class AnalysisInfo:
        cpu: Optional[bool] = None  # CPU利用率是否正常
        memory: Optional[bool] = None  # Memory 利用率是否正常
        fan: Optional[bool] = None  # 风扇是否正常
        power: Optional[bool] = None  # 电源是否正常

    @dataclass
    class BaseInfo:
        hostname: str = ''  # 主机名
        vendor_platform = ''  # 厂商平台
        model: str = ''  # 型号
        version: str = ''  # 版本
        uptime: str = ''  # 启动时间
        ip: str = ''  # IP地址
        sn = []  # type: List[Tuple[str, str]] # 序列号
        cpu_usage: str = ''  # CPU使用率
        memory_usage: str = ''  # 内存使用率
        analysis: EachVendorDeviceInfo.AnalysisInfo = None  # 检查项目结果

    def run_fun(self, platform: vendor.DefaultVendor, type_name: str, device: Device) -> Dict[str, str]:
        """获取输出的内容"""
        try:
            func = self.get_func(platform, type_name)
            return func(device)
        except AttributeError:
            print(f'{platform} {type_name} is not implemented')
            return {}

    def run_baseinfo_func(self, device: Device) -> BaseInfo:
        """获取基本信息"""

        base_info = self.BaseInfo()
        base_info.hostname = device.info.name
        base_info.vendor_platform = device.vendor.PLATFORM
        base_info.ip = device.info.ip
        base_info.sn = []
        base_info.analysis = self.AnalysisInfo()

        platform = device.vendor
        try:
            func = self.get_func(platform, 'baseinfo')
        except AttributeError:
            print(f'{platform.PLATFORM} baseinfo is not implemented')
            return base_info

        func(device, base_info)
        return base_info

    def get_func(self, platform: vendor.DefaultVendor, type_name: str) -> Callable[[str], Dict[str, str]]:
        return getattr(self, f'do_{platform.PLATFORM}_{type_name}')

    def do_huawei_vrp_baseinfo(self, device: Device, info: BaseInfo):
        """获取华为设备基本信息"""

        with device.search_cmd_with('display version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = row.get('vrp_version')
                info.uptime = row.get('uptime')

        # 获取序列号
        with device.search_cmd_with('display device manufacture-info') as cmd:
            for row in cmd.parse_result:
                info.sn.append((row.get('type'), row.get('serial')))

        # 如果没有获取到序列号，就从 display esn 和 display elabel brief里面找
        if not info.sn:
            with device.search_cmd_with('display esn') as cmd:
                if cmd.parse_result:
                    sn = cmd.parse_result[0].get('esn')
                    info.sn.append(('chassis', sn))

            with device.search_cmd_with('display elabel brief') as cmd:
                for row in cmd.parse_result:
                    info.sn.append((row.get('slot'), row.get('bar_code')))

        # CPU利用率
        with device.search_cmd_with('display cpu-usage') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd_with('display memory-usage') as cmd:
            if cmd.parse_result:
                info.memory_usage = cmd.parse_result[0].get(
                    'memory_using_percent') + '%'

        device.analysis_result

    def do_hp_comware_baseinfo(self, device: Device, info: BaseInfo):
        """获取华三设备基本信息"""

        with device.search_cmd_with('display version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = row.get('software_version') + \
                    ' Release: ' + row.get('release')
                info.uptime = row.get('uptime')

        with device.search_cmd_with('display device manuinfo') as cmd:
            for row in cmd.parse_result:
                if row.get('device_serial_number').lower() == 'none':
                    continue
                info.sn.append(
                    (row.get('device_name'), row.get('device_serial_number')))

        # CPU利用率
        with device.search_cmd_with('display cpu-usage') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd_with('display memory') as cmd:
            if cmd.parse_result:
                info.memory_usage = cmd.parse_result[0].get(
                    'used_rate') + '%'

    def do_maipu_mypower_baseinfo(self, device: Device, info: BaseInfo):
        """获取迈普设备基本信息"""

        with device.search_cmd_with('show version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = row.get('software_version')
                info.uptime = row.get('uptime')

        with device.search_cmd_with('show system module brief') as cmd:
            for row in cmd.parse_result:
                if row.get('name') != '/':
                    info.sn.append((row.get('name'), row.get('sn')))

        # CPU 利用率
        with device.search_cmd_with('show cpu monitor') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd_with('show memory') as cmd:
            if cmd.parse_result:
                info.memory_usage = cmd.parse_result[0].get(
                    'used_percent') + '%'

    def do_ruijie_os_baseinfo(self, device: Device, info: BaseInfo):
        """获取锐捷设备基本信息"""

        with device.search_cmd_with('show version') as cmd:
            if cmd.parse_result:
                temp = cmd.parse_result[0]
                info.model = temp.get('model')
                info.version = temp.get('soft_version')
                info.uptime = temp.get('uptime')

            for row in cmd.parse_result:
                if row.get('serial_number'):
                    info.sn.append(
                        (row.get('slot_name'), row.get('serial_number')))

        # CPU 利用率
        with device.search_cmd_with('show cpu') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd_with('show memory') as cmd:
            if cmd.parse_result:
                info.memory_usage = cmd.parse_result[0].get(
                    'system_memory_used_rate_precent') + '%'

    def do_cisco_ios_baseinfo(self, device: Device, info: BaseInfo):
        """获取思科设备基本信息"""

        with device.search_cmd_with('show version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('hardware')[0]
                info.version = row.get('version')
                info.uptime = row.get('uptime')

        with device.search_cmd_with('show inventory') as cmd:
            for row in cmd.parse_result:
                info.sn.append((row.get('name'), row.get('sn')))

        # CPU 利用率
        with device.search_cmd_with('show processes cpu') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd_with('show processes memory') as cmd:
            if cmd.parse_result:
                total = cmd.parse_result[0].get('memory_total')
                used = cmd.parse_result[0].get('memory_used')
                info.memory_usage = str(
                    int(int(used) / int(total) * 100)) + '%'

    def run_analysis_info(self, device: Device, info: BaseInfo):
        """更新设备检查信息"""

        for item in self.analysis_items:
            ar = device.analysis_result.get(item[0])
            if not ar._result:  # 如果没有检查结果，则不更新
                continue
            elif ar.include_warning:  # 如果有检查结果，但是包含warning，则更新为False
                setattr(info.analysis, item[1], False)
            else:  # 如果检查的结果不包含warning， 则更新为True
                setattr(info.analysis, item[1], True)


def get_base_info(device: Device) -> EachVendorDeviceInfo.BaseInfo:
    """获取设备基本信息"""
    info = EachVendorDeviceInfo()
    base_info = info.run_baseinfo_func(device)
    info.run_analysis_info(device, base_info)
    return base_info
