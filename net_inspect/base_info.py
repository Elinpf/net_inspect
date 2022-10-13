from __future__ import annotations
from dataclasses import dataclass, field
import re

from typing import TYPE_CHECKING, Callable, List, Tuple, Optional
from .func import match_lower, Singleton
from .logger import logger


if TYPE_CHECKING:
    from .domain import Device
    from . import vendor


@dataclass
class AnalysisInfo:
    cpu: Optional[bool] = None  # CPU利用率是否异常
    memory: Optional[bool] = None  # Memory 利用率是否异常
    fan: Optional[bool] = None  # 风扇是否异常
    power: Optional[bool] = None  # 电源是否异常

    def __getitem__(self, item: str):
        return self.__getattribute__(item)


@dataclass
class BaseInfo:
    hostname: str = ''  # 主机名
    file_path: str = ''  # 文件路径
    vendor: str = ''  # 厂商名称
    vendor_platform: str = ''  # 厂商软件平台
    model: str = ''  # 型号
    version: str = ''  # 版本
    uptime: str = ''  # 启动时间
    ip: str = ''  # IP地址
    sn: List[Tuple[str, str]] = field(default_factory=lambda: [])  # 序列号
    cpu_usage: str = ''  # CPU使用率
    memory_usage: str = ''  # 内存使用率
    analysis: AnalysisInfo = None  # 检查项目结果

    def __getitem__(self, item: str):
        return self.__getattribute__(item)


class EachVendorDeviceInfo(Singleton):
    """可以重载这个类，实现不同的输出格式, 重写或者增加以`do_`开头的方法"""

    analysis_items = [
        ('cpu_status', 'cpu'),
        ('memory_status', 'memory'),
        ('fan_status', 'fan'),
        ('power_status', 'power'),
    ]

    # 可用于重载的信息
    base_info_class = BaseInfo
    analysis_info_class = AnalysisInfo
    append_analysis_items = []

    def run_general_information(self, device: Device) -> BaseInfo:
        """配置通用基础信息"""
        base_info = self.base_info_class()
        base_info.hostname = device._device_info.name
        base_info.file_path = device._device_info.file_path
        base_info.vendor = str(device.vendor).split('.')[-1][:-2]
        base_info.vendor_platform = device.vendor.PLATFORM
        base_info.ip = device._device_info.ip
        base_info.sn = []
        base_info.analysis = self.analysis_info_class()

        return base_info

    def run_baseinfo_func(self, device: Device) -> BaseInfo:
        """获取基本信息"""
        base_info = self.run_general_information(device)

        platform = device.vendor
        funcs = self.get_funcs(platform, 'baseinfo')
        if not funcs:
            logger.warning(f'{platform} baseinfo is not implemented')

        for func in funcs:
            func(device, base_info)

        return base_info

    def get_funcs(
        self, platform: vendor.DefaultVendor, type_name: str
    ) -> List[Callable[[Device, BaseInfo]]]:
        """取设备厂商所有的方法"""
        ret = []
        for i in dir(self):
            if re.match(f'do_{platform.PLATFORM}_{type_name}.*', i):
                ret.append(getattr(self, i))
        return ret

    def do_huawei_vrp_baseinfo(self, device: Device, info: BaseInfo):
        """获取华为设备基本信息"""

        # Manager IP
        if not info.ip:
            with device.search_cmd('display ip interface brief') as cmd:
                for row in cmd.parse_result:
                    if match_lower(row.get('interface'), 'loopback0'):
                        info.ip = row.get('ip')
                        break  # 取到后可以立即返回

                    # 有些设备没有loopback0, 用 vlanif 代替
                    elif match_lower(row.get('interface'), 'vlanif'):
                        if not info.ip:
                            info.ip = row.get('ip')

        # Model & Version & Uptime
        with device.search_cmd('display version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = row.get('vrp_version')
                info.uptime = row.get('uptime')

        # 获取序列号
        with device.search_cmd('display device manufacture-info') as cmd:
            for row in cmd.parse_result:
                info.sn.append((row.get('type'), row.get('serial')))

        # 如果没有获取到序列号，就从 display esn 和 display elabel brief里面找
        if not info.sn:
            with device.search_cmd('display esn') as cmd:
                if cmd.parse_result:
                    sn = cmd.parse_result[0].get('esn')
                    info.sn.append(('chassis', sn))

            with device.search_cmd('display elabel brief') as cmd:
                for row in cmd.parse_result:
                    info.sn.append((row.get('slot'), row.get('bar_code')))

        # CPU利用率
        with device.search_cmd('display cpu-usage') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd('display memory-usage') as cmd:
            if cmd.parse_result:
                info.memory_usage = (
                    cmd.parse_result[0].get('memory_using_percent') + '%'
                )

        device.analysis_result

    def do_hp_comware_baseinfo(self, device: Device, info: BaseInfo):
        """获取华三设备基本信息"""

        # Manager IP
        if not info.ip:
            with device.search_cmd('display ip interface brief') as cmd:
                for row in cmd.parse_result:
                    if match_lower(row.get('interface'), 'loop0|loopback0'):
                        info.ip = row.get('ip')
                        break

                    # 有些设备没有loopback0, 用 vlanif 代替
                    elif match_lower(row.get('interface'), 'vlan'):
                        if not info.ip:
                            info.ip = row.get('ip')

        # Model & Version & Uptime
        with device.search_cmd('display version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = (
                    row.get('software_version') + ' Release: ' + row.get('release')
                )
                info.uptime = row.get('uptime')

        # SN
        with device.search_cmd('display device manuinfo') as cmd:
            for row in cmd.parse_result:
                if row.get('device_serial_number').lower() == 'none':
                    continue
                info.sn.append(
                    (row.get('device_name'), row.get('device_serial_number'))
                )

        # CPU利用率
        with device.search_cmd('display cpu-usage') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd('display memory') as cmd:
            if cmd.parse_result:
                row = cmd.parse_result[0]
                if row.get('used_rate'):
                    info.memory_usage = row.get('used_rate') + '%'

                # 当是free rate 的情况，需要转换
                elif row.get('free_rate'):
                    info.memory_usage = f"{(100 - float(row.get('free_rate'))):.1f}%"

    def do_maipu_mypower_baseinfo(self, device: Device, info: BaseInfo):
        """获取迈普设备基本信息"""

        # Manager IP
        if not info.ip:
            with device.search_cmd('show ip interface brief') as cmd:
                for row in cmd.parse_result:
                    if match_lower(row.get('interface'), 'loopback0'):
                        info.ip = row.get('ip')
                        break

                    elif match_lower(row.get('interface'), 'vlan'):
                        if not info.ip:
                            info.ip = row.get('ip')

        # Model & Version & Uptime
        with device.search_cmd('show version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('model')
                info.version = row.get('software_version')
                info.uptime = row.get('uptime')

        with device.search_cmd('show system module brief') as cmd:
            for row in cmd.parse_result:
                if row.get('name') != '/':
                    info.sn.append((row.get('name'), row.get('sn')))

        # CPU 利用率
        with device.search_cmd('show cpu monitor') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd('show memory') as cmd:
            if cmd.parse_result:
                info.memory_usage = cmd.parse_result[0].get('used_percent') + '%'

    def do_ruijie_os_baseinfo(self, device: Device, info: BaseInfo):
        """获取锐捷设备基本信息"""

        # Manager IP
        if not info.ip:
            with device.search_cmd('show ip interface brief') as cmd:
                for row in cmd.parse_result:
                    if match_lower(row.get('interface'), 'loopback 0'):
                        info.ip = row.get('ip')
                        break

                    elif match_lower(row.get('interface'), 'vlan'):
                        if not info.ip:
                            info.ip = row.get('ip')

        # Model & Version & Uptime
        with device.search_cmd('show version') as cmd:
            if cmd.parse_result:
                temp = cmd.parse_result[0]
                info.model = temp.get('model')
                info.version = temp.get('soft_version')
                info.uptime = temp.get('uptime')

            # SN
            for row in cmd.parse_result:
                if row.get('serial_number'):
                    info.sn.append((row.get('slot_name'), row.get('serial_number')))

        # CPU 利用率
        with device.search_cmd('show cpu') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd('show memory') as cmd:
            if cmd.parse_result:
                info.memory_usage = (
                    cmd.parse_result[0].get('system_memory_used_rate_precent') + '%'
                )

    def do_cisco_ios_baseinfo(self, device: Device, info: BaseInfo):
        """获取思科设备基本信息"""

        # Manager IP
        if not info.ip:
            with device.search_cmd('show ip interface brief') as cmd:
                for row in cmd.parse_result:
                    if match_lower(row.get('intf'), 'loopback0'):
                        info.ip = row.get('ipaddr')
                        break

                    elif match_lower(row.get('intf'), 'vlan'):
                        if not info.ip:
                            info.ip = row.get('ipaddr')

        # Model & Version & Uptime
        with device.search_cmd('show version') as cmd:
            for row in cmd.parse_result:
                info.model = row.get('hardware')[0]
                info.version = row.get('version')
                info.uptime = row.get('uptime')

        # SN
        with device.search_cmd('show inventory') as cmd:
            for row in cmd.parse_result:
                info.sn.append((row.get('name'), row.get('sn')))

        # CPU 利用率
        with device.search_cmd('show processes cpu') as cmd:
            if cmd.parse_result:
                info.cpu_usage = cmd.parse_result[0].get('cpu_5_min') + '%'

        # Memory 利用率
        with device.search_cmd('show processes memory') as cmd:
            if cmd.parse_result:
                total = cmd.parse_result[0].get('memory_total')
                used = cmd.parse_result[0].get('memory_used')
                info.memory_usage = (
                    str(round(float(used) / float(total) * 100, 1)) + '%'
                )

        if not info.memory_usage:  # 有些设备没有show processes memory命令
            for row in device.parse_result('show processes memory sorted'):
                total = row.get('memory_total')
                used = row.get('memory_used')
                info.memory_usage = (
                    str(round(float(used) / float(total) * 100, 1)) + '%'
                )

    def run_analysis_info(self, device: Device):
        """
        更新设备检查信息, 重载追加的内容也会添加进来

        如果没有检查信息，则为``None``，
        如果检查信息为告警级别，则为``True``
        如果检查信息为正常或者关注级别，则为``False``
        """
        info = device.info

        for item in self.analysis_items + self.append_analysis_items:
            ar = device.analysis_result.get(item[0])
            if not ar._result:  # 如果没有检查结果，则不更新
                continue
            elif ar.include_warning:  # 如果有检查结果，但是包含warning，则更新为True
                setattr(info.analysis, item[1], True)
            else:  # 如果检查的结果不包含warning， 则更新为False
                setattr(info.analysis, item[1], False)


def get_base_info(device: Device, device_info_handler=EachVendorDeviceInfo) -> BaseInfo:
    """获取设备基本信息"""
    info = (
        device_info_handler()
        if type(device_info_handler) == type
        else device_info_handler
    )
    base_info = info.run_baseinfo_func(device)
    info.run_analysis_info(device)
    return base_info
