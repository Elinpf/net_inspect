框架结构
========



net_inspect 由以下几个部分组成：


================ ==========
input_plugin     输入插件
output_plugin    输出插件
analysis_plugin  分析插件
base_info        基本信息组件
================ ==========


input_plugin
-------------

net_inspect 在执行 :meth:`~net_inspect.NetInspect.run_input` 方法时，会将路径下的所有 ``.txt`` 和 ``.log`` 文件作为输入，
然后将文件内容作为参数传递给 input_plugin。

input_plugin 的作用是将设备名称提取出来，并且将对应的 ``cmd - contents`` 内容写入到
:class:`~net_inspect.InputPluginResult` 返回。

完成这一步，就可以得到 :class:`~net_inspect.Device` 对象了。


parse
------

解析模块是固定的，不需要用户自己实现或者改变，他的作用是将每个 :class:`~net_inspect.Device` 对象中的
:class:`~net_inspect.Cmd` 对象命令内容进行解析，
使用的是 ``textfsm`` 方式的 `ntc-templates-elinpf <https://github.com/Elinpf/ntc-templates>`_ 库包。


analysis_plugin
----------------

analysis_plguin 是分析插件，已经有一部分进行了实现，主要目的是实现对设备问题的分析，形成告警信息。

例如： ``show power`` 中的信息如果是 ``Fail``，则会形成一条告警信息。


output_plugin
--------------

output_plugin 的作用是来将已经处理好的信息通过统一的方法输出出来。 例如：输出到文件，输出到数据库等等。

通过重载抽象方法 :meth:`~net_inspect.domain.OutputPluginAbstract.main` 来实现


base_info
----------

:doc:`/reference/base_info` 的作用是将不同厂商的信息保存为统一格式样式，方便后续的调用。
