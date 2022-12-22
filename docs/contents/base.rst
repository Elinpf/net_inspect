基础教程
=========


NetInspect
-----------


通常情况下，需要构造一个 :class:`~net_inspect.NetInspect` 实例进行后续的操作，实例的方式如下::

    from net_inspect import NetInspect
    net = NetInspect()


设置插件
----------

插件是 net_inspect 的核心， ``input_plugin`` 和 ``output_plugin`` 需要通过 :meth:`~net_inspect.NetInspect.set_plugins` 方法设置插件。

而 ``analysis_plugin`` 不需要设置，net_inspect 会自动识别。

net_inspect 自带了部分插件，可以在命令行模式下用以下命令查看::

    net_inspect -l


.. note::

    ``input_plugins`` 中有个 ``InputPluginWithConsole`` 插件，其简写是 ``console`` 表示只要是从控制台输入的命令，都可以被这个插件处理。 
    :doc:`/others/console_input` 提供参考


要将输入插件设置为 ``console`` 可以这样做::

    net.set_plugins(input_plugin='console')

.. note::

    设置插件时，可以使用插件名称的简写字符串直接设置，也可以使用插件类设置。 ``Type[InputPluginAbstract] | str``


使用外部模板库
--------------

net_inspect 默认使用 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_, 虽然其中包含了大部分的设备模板，
但是有时候还是希望使用自己定义的模板库进行解析，这个时候需要做的工作如下：

#. 创建一个模板库文件夹，例如 ``local_templates``
#. 将模板文件放入 ``local_templates`` 文件夹中
#. 创建 ``index`` 文件
#. 在 :meth:`~net_inspect.NetInspect.set_external_templates` 方法中指定模板库文件夹路径

创建模板库文件夹
^^^^^^^^^^^^^^^^

模板库中的 ``textfsm`` 文件命名规则是 ``<vendor_platform>_<command>.textfsm``，例如 ``cisco_ios_show_version.textfsm``

``index`` 文件是一个字典文件，包含了模板库中模板的查找规则， 例如 ntc-templates-elinpf 中的 `index <https://github.com/Elinpf/ntc-templates/blob/master/ntc_templates/templates/index>`_ 文件。

index 文件编写 `规则 <https://github.com/Elinpf/ntc-templates#index-file>`_ 如下:

#. 文件开始必须包含 ``Template, Hostname, Platform, Command`` 字段
#. 按字母顺序排列操作系统
#. 按照模板名称长度排序（最长到最短）
#. 当长度相同时，使用字母顺序排列名称
#. 操作系统之间使用空行分隔

假设我们需要添加三个厂商的 ``clock`` 模板, 文件夹结构如下::

    ├── local_templates
    │   ├── huawei_vrp_display_clock.textfsm
    │   ├── hp_comware_display_clock.textfsm
    │   ├── cisco_ios_show_clock.textfsm
    │   ├── index

index 文件如下::

    Template, Hostname, Platform, Command

    huawei_vrp_display_clock.textfsm, .*, huawei_vrp, dis[[play]] clo[[ck]]

    hp_comware_display_clock.textfsm, .*, hp_comware, di[[splay]] clo[[ck]]

    cisco_ios_show_clock.textfsm, .*, cisco_ios, sh[[ow]] clo[[ck]]

设置模板库路径
^^^^^^^^^^^^^^

当创建好模板库，接下来只需要设置模板库路径即可, 
在 :meth:`~net_inspect.NetInspect.set_external_templates` 方法中指定模板库文件夹路径::

    net.set_external_templates('local_templates')

.. note::

    如果模板库中有重复的模板，会优先使用外部模板库中的模板

启用日志
--------

net_inspect 默认不会输出任何日志，如果需要启用日志，可以使用 :meth:`~net_inspect.NetInspect.enable_console_log` 方法::

    net.enbale_console_log(level='DEBUG')