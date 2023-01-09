简介
=====

``net_inspect`` 是一个Python的库，用于将获取到的网络设备信息进行解析，统一数据调度的框架。

使用 ``net_inspect`` 可以很方便的做到处理批量设备信息，多厂商型号设备数据统一调度和输出。

特性：

* 离线处理设备命令回显
* 命令回显准确分割
* 智能识别设备名称，厂商，型号，版本，序列号等信息。
* 智能分析设备的运行状态
* 多厂商都采用统一的数据结构模型
* 采用框架设计，方便自定义扩展


安装
-----

``net_inspect`` 可以在Linux和Windows平台下使用, 需要 Python 3.7 及其以上版本。


你可以使用 PyPi 去安装 ``net_inspect``:
::

    pip install net_inspect


使用 ``-U`` 执行更新操作。


``net_inspect`` 依赖 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_, 
所以如果你已经安装了 ``ntc-templates``, 那么需要先将 ``ntc-templates`` 删除掉。
::

    pip uninstall ntc-templates

请放心 ``ntc-templates-elinpf`` 完全兼容 ``ntc-templates``，并且支持更多国产设备的命令。


快速上手
---------

``net_inspect`` 的使用非常简单，对于常规查看操作，可以使用命令行模式。
::

    net_inspect -i logs

``net_inspect`` 会自动识别 ``logs`` 目录下的所有设备信息，然后进行解析，最后将结果输出到屏幕上。

隐藏了一个默认的选项 ``-I console``, 也就是默认的输入格式是 **console** 的格式。
这里的 ``logs`` 目录下的文件是通过CLI获取到的设备信息，比如 ``show version`` 的输出结果。 
文件后缀可以是 ``.txt`` 也可以是 ``.log``。

:doc:`/others/console_input` 查看log文件样式。


代码示例
--------

作为一个框架， ``net_inspect`` 可以很方便的集成到你的代码中，比如下面的代码示例。

logs 目录下包含了三台设备的console信息，分别是一台华为交换机和两台华三交换机。


.. code-block:: python
    :emphasize-lines: 1

    from net_inspect import NetInspect

    net = NetInspect()
    net.set_plugins(input_plugin='console')
    net.run(input_path='logs')

    print('total devices:', len(net.cluster.devices))

    for device in net.cluster.devices:
        info = device.info
        print(' | '.join([info.hostname, info.ip, info.vendor,
            info.version, info.model, info.cpu_usage]))


上面的代码展示了如何使用 ``net_inspect`` 的 :obj:`~net_inspect.NetInspect` 进行批量设备信息的解析，然后不同厂商的信息内容通过统一的接口调用，
将指定内容输出到屏幕上。

输出内容如下::

    total devices: 3
    Switch_A | 24.44.1.248 | Huawei | 5.170 | S12704 Terabit Routing Switch | 6%
    Switch_B | 24.45.1.240 | H3C | 5.20 Release: 3342 | SR8800 | 5%
    Switch_C | 24.45.254.254 | H3C | 5.20 Release: 1238P08 | S9508E-V | 1%