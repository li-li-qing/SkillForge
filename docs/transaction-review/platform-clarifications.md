# 平台与编译配置限定核验

日期：2026-11-07；仅v5 Qt/Addon参考和未执行行为题变更，未改脚本，未发布。

Qt 官方当前页面标题为6.12.0：[QThread::wait](https://doc.qt.io/qt-6/qthread.html#wait)。已修正文档原“成功wait与全部后效应同步”的无条件措辞：某些OS的TLS清理可能仍运行，Linux/Windows/Apple列为OS线程完全退出后返回；未启动也可true。保留已有无反向依赖、超时及COM显式清理约定。

Lua官方5.1.5源码：[luaconf.h](https://www.lua.org/source/5.1/luaconf.h.html)、[lparser.c](https://www.lua.org/source/5.1/lparser.c.html)。直接核对LUAI_MAXVARS=200与LUA_COMPAT_VARARG定义；new_localvar使用nactvar+n+1，leaveblock调用removevars；parlist/body建立参数/self，fornum/forlist建立隐藏控制局部。引用落实在runtime-and-api，未把标准配置等同RU定制运行时。

源码推导的待运行边界：同一函数200/201局部；两个先后退出的独立块各200局部；196/197活跃局部再进入数值for；命名参数+局部、方法self、兼容arg；拆函数后另查upvalue/寄存器限制。案例用于验证源码解释，不代表这些程序已经编译。

环境发现：shutil.which('lua5.1'/'lua'/'luac5.1')均None，RS_TEST_LUA51未设置。本轮未安装Lua，未运行真实编译、Qt线程或游戏。评测题execution_status均not_run；离线检查仅能证明JSON/引用/包结构。
