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
