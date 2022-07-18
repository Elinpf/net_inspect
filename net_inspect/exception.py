class Error(Exception):
    ...


class TemplateError(Error):
    ...


class PluginError(Error):
    ...


class NotPluginError(Error):
    ...


class AnalysisPluginError(Error):
    ...


class AnalysisLevelError(AnalysisPluginError):
    ...


class CommandNotFoundError(AnalysisPluginError):
    ...


class AnalysisTemplateNameError(AnalysisPluginError):
    """模板的名称不存在"""


class AnalysisVendorNotSupport(AnalysisPluginError):
    """分析模块暂不支持该厂商"""


class NtcTemplateNotDefined(AnalysisPluginError):
    """模板名称不存在"""
