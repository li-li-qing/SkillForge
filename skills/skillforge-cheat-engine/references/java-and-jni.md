# CE Java collector 与 JNI 排障

## 先核对运行的代码

检查 CE 自带 java.lua、collector 源码/二进制、JDK、位宽和 GC 参数。Lua 函数存在不证明当前原生服务实现了对应命令；核对客户端命令编号、载荷格式、原生分发分支、响应和未知命令行为。

本次观察的 CE 7.7 包中，旧字段包装对应命令 25/26，但原生分发未实现；未知命令使服务退出。改用已核对的批量字段读写路径（该包中为 36/42）。这些编号是快照证据，不是其他版本的协议承诺；不在真实游戏里轮流尝试未知编号。

同一 Lua 快照还存在参数计数取错作用域、解引用包装的 type 判断错误、字段写入类型来源错误。包装修复必须对照实际源码和响应格式；不要把“函数没报错”当服务仍在线。进程切换和 collector 重连后重新核对状态，并使旧类/对象缓存失效。

## 引用配对是原生正确性问题

需要在调用之外保留的对象可提升为 JNI global 引用；原 local 引用与新 global 引用分别管理。字符串字符缓冲应按对应字符串 API 释放，global 引用再用 DeleteGlobalRef 释放；DeleteLocalRef 不能用于替代。

本次 collector 在方法对象返回分支中把结果提升成 global 引用，字符串返回收尾却 DeleteLocalRef，违反引用配对。仅把错误解释成“Java 地址不固定”会漏掉真实的原生内存破坏。

JNI 契约依据：[Global and Local References](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/functions.html#global-and-local-references)。具体故障和测试条件见 [案例记录](minecraft-case.md)。不要假设所有发行版仍带该错误，也不要对未来修复版本机械替换文本。

## 崩溃的最小复现

保留 hs_err 日志，读取故障线程与本地栈、JVM 参数、加载组件和时间。GC worker 崩溃可能是之前错误释放破坏引用表；仅切换 GC 或提高权限不能证明根因已解决。

在独立自有 Java fixture 复现字符串返回、全局引用分配/释放/复用和垃圾回收，再比较修复前后；只循环调用但不复用引用槽，可能没有触发同一错误。记录失效引用数、调用/GC 次数、进程退出码和读写读回，不以“运行几秒没崩”替代。

补丁只影响安装文件不一定影响已注入的 collector；确认目标内实际加载版本。无法验证当前加载组件时，停止进一步原生调用，按必要程度重启目标后重新附加；不要把重载 Lua 当成自动卸载旧原生代理。

## 对象访问器

以当前业务根重新解析对象，分别维护会话级元数据与操作级对象引用。异常退出也要释放本次临时 global 引用；重复加载不能遗留长寿命对象或复用已释放引用。类列表刷新/卸载时对应 class/method/field 缓存也需重新核对。

加载只读，读取与写入入口分开；写前检查当前对象身份及实际最大值，写后通过运行时字段读回。通过语义字段完成写入，不把依赖 GenZGC 位布局的裸地址解码作为通用写法。获取到的地址只作带条件的诊断快照。

## 线程归属与异常状态
JNIEnv只属于取得它的当前线程，不能把CE主线程缓存的JNIEnv交给worker/timer线程。原生工作线程核实自身VM附加状态并取得自己的环境；只清理自己建立的附加关系，不替其他线程detach。local引用也不能跨线程转交；跨线程对象需要正确管理global引用，其存在不保证对象裸地址固定。
调用Java方法后检查pending exception，不能只凭返回值非空或非零继续GetObjectField/写字段。异常存在时中止正常读写，只进行规范允许的异常检查和资源释放；保留原异常证据并明确传播或处理，不无条件ExceptionClear后重试。引用配对修复不能替代线程和异常检查。
依据：[Oracle JNI设计：线程与异常](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/design.html)、[Invocation API线程附加](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/invocation.html#attaching-to-the-vm)。这是Java SE 21规范归纳，不是本轮collector/JVM实测；历史Minecraft试验的标签与限制保持不变。
