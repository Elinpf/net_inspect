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
    def huawei(template: TemplateInfo, result: AnalysisResult):
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
    def cisco(template: TemplateInfo, result: AnalysisResult):
        for row in template['show power status']:
            if row['status'] != 'good':
                result.add_warning(
                    f'{row["ps"]}: {row["model"]} 电源状态异常')
