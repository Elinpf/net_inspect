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

在 :class:`~net_inspect.BaseInfo` 中，我们定义了一些基本的信息，必须 ``hostname``, ``ip``, ``cpu_usage`` 等等，
但是有时候我们还需要增加一些自定义的字段，方便后续调用。

