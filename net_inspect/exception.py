class Error(Exception):
    ...


class Continue(Exception):
    """用于控制循环"""


class TemplateError(Error):
    """ntc-template 错误"""


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
