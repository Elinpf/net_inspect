from net_inspect import func


def test_reg_extend():
    """测试正则表达式扩展"""
    res = func.reg_extend('sh[[ow]] ver[[sion]]')
    assert res == r'sh(o(w)?)? ver(s(i(o(n)?)?)?)?'


def test_get_command_from_textfsm():
    """从模板文件名中获得命令"""
    cmd = func.get_command_from_textfsm(
        'huawei_os', 'huawei_os_display_interface_status.textfsm'
    )
    assert cmd == 'display interface status'


def test_pascal_case_to_snake_case():
    """测试大驼峰（帕斯卡）转蛇形"""
    res = func.pascal_case_to_snake_case('HuaweiVrpDisplayVersion')
    assert res == 'huawei_vrp_display_version'


def test_snake_case_to_pascal_case():
    """测试蛇形转大驼峰（帕斯卡）"""
    res = func.snake_case_to_pascal_case('huawei_vrp_display_version')
    assert res == 'HuaweiVrpDisplayVersion'


def test_clamp_num_min():
    """测试小于最小值"""
    res = func.clamp_number(1, 3, 6)
    assert res == 3


def test_clamp_num_max():
    """测试大于最大值"""
    res = func.clamp_number(7, 3, 6)
    assert res == 6


def test_clamp_num_normal():
    """测试正常值"""
    res = func.clamp_number(5, 3, 6)
    assert res == 5


def test_mach():
    string = 'Normal'
    assert True == func.match(string, 'Normal')
    assert False == func.match(string, 'normal')


def test_match_lower():
    string = 'Normal'
    assert False == func.match_lower(string, 'Normal')
    assert True == func.match_lower(string, 'normal')


def test_safe_float2str():
    test_list = [
        (0.0, '0.0'),
        (1, '1.0'),
        (1.0, '1.0'),
        (3.9999992, '4.0'),
    ]

    for test in test_list:
        assert func.safe_float2str(test[0]) == test[1]


def test_safe_str2float():
    test_list = [
        ('0.0', 0.0),
        ('1', 1.0),
        ('1.0', 1.0),
        ('3.9999992', 3.9999992),
        ('err', 0.0),
    ]

    for test in test_list:
        assert func.safe_str2float(test[0]) == test[1]


def test_case_insensitive_dict():
    """测试忽略大小写的字典"""
    t = func.CaseInsensitiveDict()
    t['VERSION'] = '1.0'
    t['uptime'] = '1 day'

    assert t['VERSION'] == '1.0'
    assert t['version'] == '1.0'

    assert t['uptime'] == '1 day'

    del t['uptime']
    assert 'uptime' not in t

    del t['VERSION']
    assert 'VERSION' not in t
    assert 'version' not in t


def test_case_insensitive_dict_2():
    """测试忽略大小写的字典的update方法"""
    t = {'VERSION': '1.0', 'uptime': '1 day'}

    t2 = func.CaseInsensitiveDict()
    t2.update(t)

    del t

    assert t2['VERSION'] == '1.0'
    assert t2['version'] == '1.0'
    assert t2['UPTIME'] == '1 day'
    assert t2['uptime'] == '1 day'


def test_case_insensitive_dict_3():
    """测试忽略大小写的字典的__init__方法"""
    t = {'VERSION': '1.0', 'uptime': '1 day'}

    t2 = func.CaseInsensitiveDict(t)
    del t

    assert t2['VERSION'] == '1.0'
    assert t2['version'] == '1.0'
    assert t2['UPTIME'] == '1 day'
    assert t2['uptime'] == '1 day'
