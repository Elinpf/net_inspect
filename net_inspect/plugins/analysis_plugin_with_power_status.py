from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..analysis_plugin import (AnalysisPluginAbc, AnalysisResult,
                               TemplateValue, analysis)
from ..vendor import Cisco, Huawei

if TYPE_CHECKING:
    from ..domain import AnalysisResult


class AnalysisPluginWithPowerStatus(AnalysisPluginAbc):
    """检查电源状态是否正常"""

    @analysis.vendor(Huawei)
    @analysis.template_value('huawei_vrp_display_power.textfsm', ['MODE', 'ID', 'PRESENT', 'STATE'])
    def huawei(self, template: TemplateValue, result: AnalysisResult):
        power = template['display power']
        for row in power:
            # 当没有电源插入的时候，不关注
            if not re.match(r'Yes|Present', row['present']):
                continue
            if not re.match(r'Normal|Supply', row['state']):
                result.add_warning(
                    f'设备 {row["id"]} 电源状态异常')

    @analysis.vendor(Cisco)
    @analysis.template_value('cisco_ios_show_power_status.textfsm', ['ps', 'model', 'status', 'fan_sensor'])
    def cisco(self, template: TemplateValue, result: AnalysisResult):
        for row in template['show power status']:
            if row['status'] != 'good':
                result.add_warning(
                    f'{row["ps"]}: {row["model"]} 电源状态异常')
