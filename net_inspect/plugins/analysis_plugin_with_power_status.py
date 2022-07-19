from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..analysis_plugin import (AnalysisPluginAbc, AnalysisResult,
                               TemplateInfo, analysis)
from .. import vendor

if TYPE_CHECKING:
    from ..domain import AnalysisResult


class AnalysisPluginWithPowerStatus(AnalysisPluginAbc):
    """
    要求设备所有在位电源模块运行在正常状态。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_power.textfsm', ['MODE', 'ID', 'PRESENT', 'STATE'])
    def huawei_vrp(template: TemplateInfo, result: AnalysisResult):
        """模块状态在线，并且状态不为Normal或者Supply时告警"""
        power = template['display power']
        for row in power:
            # 当没有电源插入的时候，不关注
            if not re.match(r'Yes|Present', row['present']):
                continue
            if not re.match(r'Normal|Supply', row['state']):
                result.add_warning(
                    f'设备 {row["id"]} 电源状态异常')

    @analysis.vendor(vendor.Cisco)
    @analysis.template_key('cisco_ios_show_power_status.textfsm', ['ps', 'model', 'status', 'fan_sensor'])
    def cisco_ios(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为good时，报警"""
        for row in template['show power status']:
            if row['status'] != 'good':
                result.add_warning(
                    f'{row["ps"]}: {row["model"]} 电源状态异常')

    @analysis.vendor(vendor.Maipu)
    @analysis.template_key('maipu_mypower_show_system_power.textfsm', ['power_id', 'status', 'work_status', 'power_in'])
    def maipu_mypower(template: TemplateInfo, result: AnalysisResult):
        """
        迈普的show system power 分为两种:
        一种为长的信息，``status``的信息为online， ``work_status`` 和 ``power_in`` 均为Normal为正常，
        另外一种是短信息，只有 ``status``, 判断模块是否正常
        """
        for row in template['show system power']:
            if row['status'] == 'Online':
                if row['work_status'] != 'Normal' or row['power_in'] != 'Normal':
                    result.add_warning(
                        f'电源 {row["power_id"]}状态异常')
            else:
                if row['status'] != 'Normal':
                    result.add_warning(
                        f'电源{row["power_id"]}状态异常')
