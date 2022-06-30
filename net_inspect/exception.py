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
    ...


class NtcTemplateNotDefined(AnalysisPluginError):
    ...
