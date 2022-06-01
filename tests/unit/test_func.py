from net_inspect.func import reg_extend


def test_reg_extend():
    """测试正则表达式扩展"""
    res = reg_extend('sh[[ow]] ver[[sion]]')
    assert res == r'sh(o(w)?)? ver(s(i(o(n)?)?)?)?'
