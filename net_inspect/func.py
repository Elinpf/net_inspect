import re


def reg_extend(reg: str) -> str:
    """扩展正则表达式写法，支持简单的逐字匹配
    e.g
    r'sh[[ow]] ver[[sion]]'
    将变成
    'sh(o(w)?)? ver(s(i(o(n)?)?)?)?'
    """
    def _completion(match):
        word = str(match.group())[2:-2]
        return '(' + ('(').join(word) + ')?' * len(word)

    return re.sub(r'(\[\[.+?\]\])', _completion, reg)


def get_command_from_textfsm(vendor_platform: str, template: str) -> str:
    """从模板文件名中获得命令
    :param vendor_platform: 平台名称
    :param template: 模板文件名

    :return: 命令

    >>> self.get_command('huawei_os', 'huawei_os_display_interface_status.textfsm')
    'display interface status'
    """

    template = template.replace(vendor_platform + '_', '')
    template = template.replace('.textfsm', '')
    return template.replace('_', ' ')


def pascal_case_to_snake_case(camel_case: str):
    """大驼峰（帕斯卡）转蛇形

    >>> pascal_case_to_snake_case('HuaweiVrpDisplayVersion')
    'huawei_vrp_display_version'
    """
    snake_case = re.sub(r"(?P<key>[A-Z])", r"_\g<key>", camel_case)
    return snake_case.lower().strip('_')


def snake_case_to_pascal_case(snake_case: str):
    """蛇形转大驼峰（帕斯卡）

    >>> snake_case_to_pascal_case('huawei_vrp_display_version')
    'HuaweiVrpDisplayVersion'
    """
    words = snake_case.split('_')
    return ''.join(word.title() for word in words)
