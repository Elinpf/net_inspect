from __future__ import annotations

from typing import TYPE_CHECKING
import re

from ..analysis_plugin import AnalysisPluginAbc
from ..vendor import Cisco, Huawei
from ..exception import AnalysisVendorNotSupport

if TYPE_CHECKING:
    from ..domain import AnalysisResult


class AnalysisPluginWithPowerStatus(AnalysisPluginAbc):
    """检查电源状态是否正常"""

    def __init__(self):
        ntc_templates = {
            Huawei: {'huawei_vrp_display_power.textfsm': [
                'MODE', 'ID', 'PRESENT', 'STATE']}
        }
        super().__init__(ntc_templates)

    def main(self, vendor, template, result) -> AnalysisResult:
        if vendor == Huawei:
            power = template['display power']
            for row in power:
                # 当没有电源插入的时候，不关注
                if not re.match(r'Yes|Present', row['present']):
                    continue
                if not re.match(r'Normal|Supply', row['state']):
                    result.add_warning(
                        f'设备 {row["id"]} 电源状态异常')

        else:
            raise AnalysisVendorNotSupport(vendor)

        return result
