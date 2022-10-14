from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis
from ..func import safe_str2float

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithMemoryStatus(AnalysisPluginAbc):
    """
    检查内存利用率不能过高。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.base_info('memory_usage')
    def huawei_vrp(template: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        check_memory_usage(template.base_info['memory_usage'], result)

    @analysis.vendor(vendor.Cisco)
    @analysis.base_info('memory_usage')
    def cisco_ios(template: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        check_memory_usage(template.base_info['memory_usage'], result)

    @analysis.vendor(vendor.Ruijie)
    @analysis.base_info('memory_usage')
    def ruijie_os(template: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        check_memory_usage(template.base_info['memory_usage'], result)

    @analysis.vendor(vendor.Maipu)
    @analysis.base_info('memory_usage')
    def maipu_mypower(template: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        check_memory_usage(template.base_info['memory_usage'], result)

    @analysis.vendor(vendor.H3C)
    @analysis.base_info('memory_usage')
    def hp_comware(template: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        check_memory_usage(template.base_info['memory_usage'], result)


def check_memory_usage(memory_usage: str, result: AnalysisResult):
    if memory_usage == '':
        return

    # 去除百分号，转换为float
    memory_usage = safe_str2float(memory_usage[:-1])

    if memory_usage > 80:
        result.add_warning(f"内存利用率达到{round(memory_usage,1)}%")
