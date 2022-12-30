进阶教程
==========


自定义厂商
----------

目前 net_inspect 支持以下厂商的识别：

#. :class:`~net_inspect.vendor.Cisco` ``cisco_ios``
#. :class:`~net_inspect.vendor.Huawei` ``huawei_vrp``
#. :class:`~net_inspect.vendor.H3C` ``hp_comware``
#. :class:`~net_inspect.vendor.Maipu` ``maipu_mypower``
#. :class:`~net_inspect.vendor.Ruijie` ``ruijie_os``

但是在 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_ 中包含的的远远不止这5家厂商，
当有需要时，可以自定义厂商，只需要继承 :class:`~net_inspect.vendor.DefaultVendor` 类即可。

例如，我们需要识别一台 ``Juniper`` 的设备，我们可以这样做：

.. code-block:: python

    from net_inspect.vendor import DefaultVendor

    class Juniper(DefaultVendor):
        PLATFORM = 'juniper_junos'
        VERSION_COMMAND = 'sh[[ow]] ver[[sion]]'
        KEYWORD_REG = r'JUNOS'
        INVALID_STR = r'Invalid input detected at'


* ``PLATFORM`` 表示在 ``ntc-templates-elinpf`` 中的厂商名称前缀
* ``VERSION_COMMAND`` 表示获取设备版本的命令， ``[[`` 和 ``]]`` 包裹的内容是可以简写的，例如 ``sh ver`` 和 ``sh[[ow]] ver[[sion]]`` 是等价的
* ``KEYWORD_REG`` 表示设备厂商信息的关键字，可以使用正则匹配，匹配到关键字后识别为对应厂商设备
* ``INVALID_STR`` 表示命令回显是无效回显的关键字，必须命令错误时的回显等。

只需要这样定义一下， net_inspect 在执行的时候会自动识别出来。并将对应的 ``juniper_junos`` 模板调用执行解析。



增加base_info条目
-----------------

在 :class:`~net_inspect.BaseInfo` 中，net_inspect 定义了一些基本的信息，比如 ``hostname``, ``ip``, ``cpu_usage`` 等等， 实现跨设备类型的统一调用。
但是有时候还需要增加一些自定义的字段，方便后续统一调用。


例如，我们需要增加一个 ``clock`` 字段，用于获取设备的时钟信息，我们可以这样做:

.. code-block:: python
    :emphasize-lines: 5,10,27

    from net_inspect import NetInspect, EachVendorDeviceInfo, BaseInfo, Device


    class AppendClock(BaseInfo):
        clock: str = ''  # 时钟信息


    class EachVendorWithClock(EachVendorDeviceInfo):

        base_info_class = AppendClock  # 设置base_info的类

        def do_huawei_vrp_baseinfo_2(self, device: Device, info: AppendClock):
            # 添加do_<vendor_platform>_baseinfo_<something>方法，可以自动运行
            for row in device.parse_result('display clock'):
                info.clock = f'{row["year"]}-{row["month"]}-{row["day"]} {row["time"]}'

        def do_hp_comware_baseinfo_2(self, device: Device, info: AppendClock):
            for row in device.parse_result('display clock'):
                info.clock = f'{row["year"]}-{row["month"]}-{row["day"]} {row["time"]}'

        # ... 可自行其他厂商的do_<vendor_platform>_baseinfo_<something>方法


    if __name__ == '__main__':
        net = NetInspect()
        net.set_plugins(input_plugin='console')
        net.set_base_info_handler(EachVendorWithClock)  # 设置获取设备基本信息的处理类
        net.run(input_path='log')

        print('total devices:', len(net.cluster.devices))

        for device in net.cluster.devices:
            info = device.info  # type: AppendClock
            print(' | '.join([info.hostname, info.clock]))

执行的输出结果如下::

    total devices: 3
    Switch_A | 2021-03-19 10:23:08
    Switch_B | 2021-03-19 10:24:17
    Switch_C | 2021-03-19 10:32:17

可以看到，我们增加 ``huawei_vrp`` 和 ``hp_comware`` 平台的 ``clock`` 信息，使用 ``device.info.clock`` 进行统一调用。

.. note::
    
    没有实现 ``clock`` 的平台，将会以空字符串作为默认值


