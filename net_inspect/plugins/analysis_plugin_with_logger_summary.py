from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithLoggerSummary(AnalysisPluginAbc):
    """
    检查日志中的告警信息。
    """

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_logbuffer_summary.textfsm',
                           ['slot', 'emerg', 'alert', 'crit', 'error', 'warn'])
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """日志摘要中大于WARN级别的告警信息进行提示"""
        for row in template['display logbuffer summary']:
            if int(row['emerg']) > 0:
                result.add_warning(f"Slot {row['slot']} 有{row['emerg']}条紧急告警")
            if int(row['alert']) > 0:
                result.add_warning(f"Slot {row['slot']} 有{row['alert']}条警告告警")
            if int(row['crit']) > 0:
                result.add_warning(f"Slot {row['slot']} 有{row['crit']}条严重告警")
            if int(row['error']) > 0:
                result.add_warning(f"Slot {row['slot']} 有{row['error']}条错误告警")
            if int(row['warn']) > 0:
                result.add_warning(f"Slot {row['slot']} 有{row['warn']}条告警")
