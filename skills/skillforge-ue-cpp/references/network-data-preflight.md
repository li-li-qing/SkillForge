# UE网络与大量数据的前置合同

适用：当前UE项目的联机Gameplay、背包/容器/装备等批量状态；普通C++、Qt或已明确单机的纯本地列表不套用。

## 先确定事实

读取当前引擎小版本、复制体系、拥有者和实际消费入口。用户的P2P需求必须澄清具体会话与权威拓扑；不能把P2P直接解释为每个节点均可权威写入。明确Authority、AutonomousProxy、SimulatedProxy及本地UI职责，客户端请求不直接变更权威物品真值。

## 大规模同步主动评估

用户希望大量同步优先使用FFastArraySerializer。先给出数量/变化频率/接收范围的依据与方案，不默认复制整份普通数组。确认实际引擎版本对应的数组包装、条目身份、NetDeltaSerialize与traits、增改MarkItemDirty、删除MarkArrayDirty、相关接收回调及生命周期；不要依赖数组索引充当长期业务身份。

按当前工程复制体系登记属性与子对象，重要状态实现相应OnRep并配置GetLifetimeReplicatedProps。FastArray的增删改回调与普通属性OnRep是不同通知机制；不能假定给外层数组加一个OnRep就替代条目通知。Listen Server的本地展示路径也要按实际代码验证，不假定主机必然经历与远端完全相同的通知。

结构体内说明哪些字段参与序列化、稳定身份、Authority写入、dirty标记、接收端消费与本地派生/缓存字段；不写与实际编码不符的模板注释。网络引用不等于对象内容已复制，按需核对子对象合同。

## 性能与内存约束

遵循Unreal Coding Standard；UObject成员引用优先按所有权选择UPROPERTY下TObjectPtr，观察/异步生命周期另核对，不将其视为万能安全保证。不得在Tick或循环中调用StaticLoadObject、FObjectFinder或做复杂Tag匹配；资源准备/索引预计算移出热路径，明确缓存失效。

检查真实结构布局、热冷字段与频繁写共享字段造成的缓存问题；不盲目给所有结构alignas(64)或压缩对齐。改变布局或序列化先评估兼容，性能收益以测量而非名字证明。

## 定向验证

按项目实际需求覆盖Authority/Proxy、增删改、重复请求、初始同步、迟加入/重连、容量上界、相关网络条件与UI投影。未有UE/多人运行环境写not_run，不能仅以头文件静态检查宣称联机正确。

## 来源与范围

2026-10-15核对：[Epic FFastArraySerializer](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/NetCore/FFastArraySerializer)、[类型示例](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/NetCore/TFastArrayTypeHelper)、[UObject复制](https://dev.epicgames.com/documentation/unreal-engine/replicating-uobjects-in-unreal-engine)。网页默认版本不等于项目版本，具体API须回当前引擎源码核对。

既有详细合同继续按需读取 [复制审查](replication-review.md)、[容器与子对象](container-transactions-and-subobjects.md)。本页是前置检查与用户工程约束，不宣称已在用户工程完成联机性能测试。
