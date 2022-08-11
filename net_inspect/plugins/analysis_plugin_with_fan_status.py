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
            if row['present']:  # NE serial and S5700 serial
                if not match_lower(row['present'], r'yes|present'):
                    result.add_focus(f"Slot {row['slot_id']} 风扇不在位")

                elif row['registered'] and not match_lower(row['registered'], 'yes'):
                    result.add_focus(f"Slot {row['slot_id']} 风扇未注册")

                elif not match_lower(row['status'], r'auto|namual|normal'):
                    result.add_warning(f"Slot {row['slot_id']} 风扇状态不正常")
            else:  # 其他系列进行简单的判断
                if not match_lower(row['status'], 'normal'):
                    result.add_warning(f"Slot {row['slot_id']} 风扇状态不正常")

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_fan.textfsm', ['slot', 'id', 'status'])
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """模块状态不为Normal的时候告警"""
        for row in template['display fan']:
            if not match_lower(row['status'], 'normal'):
                result.add_warning(
                    f'Slot {row["slot"]} Fan {row["id"]} 状态异常' if row['slot'] else f'Fan {row["id"]} 状态异常')

    @analysis.vendor(vendor.Maipu)
    @analysis.template_key('maipu_mypower_show_system_fan.textfsm', ['fan_id', 'status', 'work_status', 'statistics_ierr', 'statistics_oerr'])
    def maipu_mypower(template: TemplateInfo, result: AnalysisResult):
        """模块Status状态为Online的时候，检查WorkStatus不为Normal的时候告警, 否则Status不为Normal时警告，
        并且检查模块的错误统计"""
        for row in template['show system fan']:
            if match_lower(row['status'], 'online'):
                if not match_lower(row['work_status'], 'normal'):
                    result.add_warning(f'Fan {row["fan_id"]} 状态异常')
            elif not match_lower(row['status'], 'normal'):
                result.add_warning(f'Fan {row["fan_id"]} 状态异常')

            elif int(row['statistics_ierr']) + int(row['statistics_oerr']) > 0:
                result.add_warning(f'Fan {row["fan_id"]} 状态异常')
