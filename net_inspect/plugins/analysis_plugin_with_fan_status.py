from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis
from ..func import match_lower

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithFanStatus(AnalysisPluginAbc):
    """
    要求设备所有在位风扇模块运行在正常状态。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_fan.textfsm', ['slot_id', 'present', 'registered', 'status'])
    def huawei_vrp(template: TemplateInfo, result: AnalysisResult):
        """检查设备所有在位风扇模块运行在正常状态"""
        for row in template['display fan']:
            if not match_lower(row['present'], 'yes'):
                result.add_warning(f"Slot {row['slot_id']} 风扇不在位")

            elif not match_lower(row['registered'], 'yes'):
                result.add_warning(f"Slot {row['slot_id']} 风扇未注册")

            elif not match_lower(row['status'], r'auto|namual'):
                result.add_warning(f"Slot {row['slot_id']} 风扇状态不正常")

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_fan.textfsm', ['slot', 'id', 'status'])
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为Normal的时候告警"""
        for row in template['display fan']:
            if not match_lower(row['status'], 'normal'):
                result.add_warning(
                    f'Slot {row["slot"]} Fan {row["id"]} 状态异常' if row['slot'] else f'Fan {row["id"]} 状态异常')
