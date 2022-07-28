from __future__ import annotations

import re
from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis
from ..func import match_lower

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithPowerStatus(AnalysisPluginAbc):
    """
    要求设备所有在位电源模块运行在正常状态。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_power.textfsm', ['mode', 'id', 'present', 'state'])
    def huawei_vrp(template: TemplateInfo, result: AnalysisResult):
        """模块状态在线，并且状态不为Normal或者Supply时告警"""
        power = template['display power']
        for row in power:
            # 当没有电源插入的时候，不关注
            if not match_lower(row['present'], r'yes|present'):
                result.add_focus(f"Power {row['id']} 电源不在位")
            elif not match_lower(row['state'], r'normal|supply'):
                result.add_warning(
                    f'Power {row["id"]} 电源状态异常')

    @analysis.vendor(vendor.Cisco)
    @analysis.template_key('cisco_ios_show_power_status.textfsm', ['ps', 'model', 'status', 'fan_sensor'])
    def cisco_ios(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为good时，报警"""
        for row in template['show power status']:
            if row['status'] != 'good':
                result.add_warning(
                    f'{row["ps"]}: {row["model"]} 电源状态异常')

    @analysis.vendor(vendor.Ruijie)
    @analysis.template_key('ruijie_os_show_power.textfsm', ['power_id', 'power_type', 'status'])
    def ruijie_os(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为ok时，报警"""
        for row in template['show power']:
            if row['power_type'] == 'N/A':
                continue
            if row['status'] != 'ok':
                result.add_warning(
                    f'Power {row["power_id"]} 电源状态异常')

    @analysis.vendor(vendor.Maipu)
    @analysis.template_key('maipu_mypower_show_system_power.textfsm', ['power_id', 'status', 'work_status', 'power_in'])
    def maipu_mypower(template: TemplateInfo, result: AnalysisResult):
        """
        迈普的show system power 分为两种:
        一种为长的信息，``status``的信息为online， ``work_status`` 和 ``power_in`` 均为Normal为正常，
        另外一种是短信息，只有 ``status``, 判断模块是否正常
        """
        for row in template['show system power']:
            if row['status'].lower() == 'online':
                if row['work_status'].lower() != 'normal' or row['power_in'].lower() != 'normal':
                    result.add_warning(
                        f'Power {row["power_id"]} 状态异常')
            else:
                if row['status'].lower() != 'normal':
                    result.add_warning(
                        f'Power {row["power_id"]} 状态异常')

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_power.textfsm', ['slot', 'id', 'status'])
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为Normal的时候告警"""
        for row in template['display power']:
            if row['status'].lower() != 'normal':
                result.add_warning(
                    f'Slot {row["slot"]} Power {row["id"]} 状态异常' if row['slot'] else f'{row["id"]} 状态异常')
