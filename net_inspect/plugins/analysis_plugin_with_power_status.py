from __future__ import annotations

from typing import TYPE_CHECKING
import re

from ..analysis_plugin import AnalysisPluginAbc
from ..vendor import Cisco, Huawei

if TYPE_CHECKING:
    from ..domain import AnalysisResult


class AnalysisPluginWithPowerStatus(AnalysisPluginAbc):
    """检查电源状态是否正常"""

    def __init__(self):
        ntc_templates = {
            Huawei: {'huawei_vrp_display_power.textfsm': [
                'MODE', 'ID', 'PRESENT', 'STATE']},
            Cisco: {'cisco_ios_show_power_status.textfsm': [
                'model', 'status', 'fan_sensor', 'input_status']}
        }
        super().__init__(ntc_templates)

    def main(self, vendor, template, result) -> AnalysisResult:
        if vendor is Huawei:
            power = template['display power']
            for row in power:
                # 当没有电源插入的时候，不关注
                if not re.match(r'Yes|Present', row['present']):
                    continue
                if not re.match(r'Normal|Supply', row['state']):
                    result.add_warning(
                        f'设备 {row["id"]} 电源状态异常')

        if vendor is Cisco:
            for row in template['show power status']:
                if row['status'] != 'good' or row['input_status'] != 'good':
                    result.add_warning(
                        f'设备 {row["model"]} 电源状态异常')

        return result
