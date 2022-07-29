from __future__ import annotations

from typing import TYPE_CHECKING

from .. import vendor
from ..analysis_plugin import AnalysisPluginAbc, analysis

if TYPE_CHECKING:
    from ..analysis_plugin import TemplateInfo
    from ..domain import AnalysisResult


class AnalysisPluginWithCpuStatus(AnalysisPluginAbc):
    """
    检查CPU利用率不能过高。
    """

    @analysis.vendor(vendor.Huawei)
    @analysis.template_key('huawei_vrp_display_cpu-usage.textfsm', ['cpu_5_min'])
    def huawei_vrp(template_info: TemplateInfo, result: AnalysisResult):
        """
        CPU利用率高于80%，则告警。
        """
        for row in template_info['display cpu-usage']:
            check_cpu_usage(float(row['cpu_5_min']), result)

    @analysis.vendor(vendor.Cisco)
    @analysis.template_key('cisco_ios_show_processes_cpu.textfsm', ['cpu_5_min'])
    def cisco_ios(template_info: TemplateInfo, result: AnalysisResult):
        """
        CPU利用率高于80%，则告警。
        """
        for row in template_info['show processes cpu']:
            check_cpu_usage(float(row['cpu_5_min']), result)

    @analysis.vendor(vendor.Ruijie)
    @analysis.template_key('ruijie_os_show_cpu.textfsm', ['cpu_5_min'])
    def ruijie_os(template_info: TemplateInfo, result: AnalysisResult):
        """
        CPU利用率高于80%，则告警。
        """
        for row in template_info['show cpu']:
            check_cpu_usage(float(row['cpu_5_min']), result)

    @analysis.vendor(vendor.Maipu)
    @analysis.template_key('maipu_mypower_show_cpu_monitor.textfsm', ['cpu_5_min'])
    def maipu_mypower(template_info: TemplateInfo, result: AnalysisResult):
        """
        CPU利用率高于80%，则告警。
        """
        for row in template_info['show cpu monitor']:
            check_cpu_usage(float(row['cpu_5_min']), result)

    @analysis.vendor(vendor.H3C)
    @analysis.template_key('hp_comware_display_cpu-usage.textfsm', ['cpu_5_min'])
    def hp_comware(template_info: TemplateInfo, result: AnalysisResult):
        """
        CPU利用率高于80%，则告警。
        """
        for row in template_info['display cpu-usage']:
            check_cpu_usage(float(row['cpu_5_min']), result)


def check_cpu_usage(cpu_usage: float, result: AnalysisResult):
    if cpu_usage > 80:
        result.add_warning(f'CPU利用率达到{cpu_usage}%')
