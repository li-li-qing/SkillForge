# UE 复制、接口与构建审查补充

从旧 LGF 审计技能提炼；通用 UE 检查不意味着所有项目都采用 LGF API 或相同网络策略。

## 复制闭环

属性声明 → OnRep 实现 → GetLifetimeReplicatedProps/Super → 实际注册及条件 → Authority 修改 → 各消费者刷新。Push Model 还要核对实际脏标记与启用条件。Host 本地表现可能需要共享刷新函数，不能假定 OnRep 自动覆盖所有服务器本地路径。

FastArray 检查条目/容器继承、NetDeltaSerialize/Traits、新增修改 MarkItemDirty、删除结构变化 MarkArrayDirty、回调与消费身份。数组下标和内部 ReplicationID 不是稳定业务/存档 ID。重排不应靠下标定义业务顺序，需要显式排序字段和消费端验证。小型低频数组不机械迁移 FastArray。

Server RPC 核对拥有权；世界 NPC/仓库等不属于客户端时通过它拥有的 Actor/Agent 请求。Authority 解析稳定身份，校验权限、距离、成本、数量、状态、频率与陈旧上下文。Multicast 不替代需要 JIP/相关性恢复的复制状态。

## 生命周期与蓝图接口

异步加载、委托、Timer、输入绑定与授予 Handle 成对清理；弱引用使用前重新核验对象及当前 Avatar/操作代次。热路径不要同步加载、全局 Actor 扫描或每帧重建大 UI 快照；缓存必须说明失效条件。优化结论需要前后采样，不以代码更短证明更快。

按真实反射元数据说明 Callable/Pure/Event/RPC，不凭名称画蓝图节点。请求提交、服务器完成、失败/取消分别反馈；UIData 是显示快照，不暴露可变复制容器或 Dirty 接口。删除旧接口前查源码、配置、可检查资产、存档与序列化兼容；不要把旧文档“无情删除”当成不看引用就删的授权。

## 构建与文档

从当前 .uproject、Target.cs、引擎关联和 Build.cs 找实际目标；不固定用户盘符、模块数量或 DebugGame。公共头只引必要依赖；模块图不能下层依赖项目/表现上层。

日志定位 first-include 诊断由哪个工具发出；UE 5.7 案例是 UBT include-order 检查，不写成 UHT。反射失败、C++ 编译失败和链接缺模块/符号分别处理。不要为测试方便随意公开生产 API 或扩大所有模块依赖。

Target is up to date 仅表示增量目标没有重编。要证明改动进入二进制，保存实际 Compile/Link 与对应文件版本；Live Coding 成功也不自动证明下一次干净启动加载同一内容。

教程按先创建依赖再引用接线的顺序组织；签名变更查 API，装配变更查 Tutorial，模块定位查 README。正文说明真实原因、网络上下文、失败分支与 Blueprint Impact，不用大段 API 全文替代最小可执行路径。
