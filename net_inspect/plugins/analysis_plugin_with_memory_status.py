from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithMemoryStatus(AnalysisPluginAbc):
    """
    检查内存利用率不能过高。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_memory-usage.textfsm', ['MEMORY_USING_PERCENT'])
    def huawei_vrp(template_info: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        for row in template_info['display memory-usage']:
            check_memory_usage(float(row['MEMORY_USING_PERCENT']), result)

    @analysis.vendor(vendor.Cisco)
    @analysis.template_key('cisco_ios_show_processes_memory_sorted.textfsm', ['memory_total', 'memory_used'])
    @analysis.template_key('cisco_ios_show_processes_memory.textfsm', ['memory_total', 'memory_used'])
    def cisco_ios(template_info: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        for row in template_info['show processes memory sorted']:
            check_memory_usage(
                float(row['memory_used']) / float(row['memory_total']) * 100, result)

        for row in template_info['show processes memory']:
            check_memory_usage(
                float(row['memory_used']) / float(row['memory_total']) * 100, result)

    @analysis.vendor(vendor.Ruijie)
    @analysis.template_key('ruijie_os_show_memory.textfsm', ['system_memory_used_rate_precent'])
    def ruijie_os(template_info: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        for row in template_info['show memory']:
            check_memory_usage(
                float(row['system_memory_used_rate_precent']), result)

    @analysis.vendor(vendor.Maipu)
    @analysis.template_key('maipu_mypower_show_memory.textfsm', ['used_percent'])
    def maipu_mypower(template_info: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        for row in template_info['show memory']:
            check_memory_usage(float(row['used_percent']), result)

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_memory.textfsm', ['used_rate'])
    def hp_comware(template_info: TemplateInfo, result: AnalysisResult):
        """
        内存利用率高于80%，则告警。
        """
        for row in template_info['display memory']:
            check_memory_usage(float(row['used_rate']), result)


def check_memory_usage(memory_usage: float, result: AnalysisResult):
    if memory_usage > 80:
        result.add_warning(f"内存利用率达到{round(memory_usage,1)}%")
