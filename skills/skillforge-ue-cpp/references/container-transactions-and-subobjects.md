# Container Transaction、FastArray 与 Replicated Subobject 生产合同

> 用于复杂 Inventory / Equipment / Stash / Hotbar / World Container 的网络审查。重点不是某个插件 API，而是把复制、Authority transaction、对象生命周期、线程和存档拆成可验证合同。

## 1. 先把四种身份分开

复杂容器里经常同时存在以下标识，它们不能互相替代：

| 身份 | 用途 | 生命周期 |
|---|---|---|
| `ItemId` / `ContainerId` | 业务、存档、跨容器引用 | 跨会话稳定 |
| runtime handle：index + generation | 当前运行时快速查找、防 stale slot | 当前会话 |
| FastArray `ReplicationID` / dirty state | 网络 delta 内部 bookkeeping | 复制实现 |
| UObject pointer / Outer / subobject registration | GC、RPC、网络宿主 | 当前对象图 |

规则：

- Hotbar、Quest link、Equipment intent、Save 引用 stable ID，不保存 UObject pointer 作为长期身份。
- Cell index 只是位置，不是物品身份。
- Cell version/generation 能拒绝 stale request，但不等于 persistent ItemId。
- Outer 可以帮助 lifetime/RPC routing，但不能成为业务 ownership 的唯一证据。

## 2. FastArray 与 replicated UObject 是两条网络合同

当 FastArray entry 指向 replicated UObject Item 时：

1. FastArray 负责“这个 entry 现在引用谁、stack/slot/version 是什么”。
2. registered subobject 负责 Item UObject 及其 descendants 的 replicated properties/RPC 生命周期。
3. 两者可能不同帧到达，UI/业务不能假设 entry callback 时 Item 所有字段已经 ready。
4. JIP 必须能从完整 snapshot 重建本地索引，并在 UObject 尚未 ready 时延期表现刷新或按 stable ID 二次 resolve。

### 2.1 对称 subobject transfer

跨容器移动复杂 UObject Item 时，至少要有等价于下面的显式流程：

`validate old host -> unregister old item descendants -> commit business transfer/reparent -> register new item descendants -> publish projection`

可根据引擎/宿主实现调整顺序，但必须证明以下不变量：

- 同一 Item 不会同时长期注册在两个网络 host；
- 旧 host 在 eject/replace/destroy 后不保留 stale registration；
- nested subobjects 与 item root 同步撤销/注册；
- relevancy/condition 改变后没有越权泄露；
- Listen Host 本地表现不依赖自己的 OnRep。

不能只看到 `bReplicateUsingRegisteredSubObjectList=true` 与 `AddReplicatedSubObject()` 就宣称生命周期完整。必须搜索 active `RemoveReplicatedSubObject()` 调用路径，并验证 move/eject/replace/destroy/JIP/reconnect。

## 3. “项目很新”不等于“某机制已经 active”

技术时效性审查除了 commit/date，还要区分：

1. **Declared**：README、注释、模块依赖、header include 宣称存在。
2. **Compiled**：代码能进入目标 build，而不是 `#if 0`、未启用宏、Editor-only 或未引用文件。
3. **Runtime-active**：真实执行路径会调用它。
4. **Verified**：目标 UE 版本运行测试证明语义成立。

只有第 3 层才能写“当前实现使用 X”，第 4 层才能写“目标项目可依赖 X”。

典型反例：

- include `IrisFastArraySerializer.h`，但真正继承仍在 `#if 0` 后面；
- README 写 rollback，但 rollback 函数被注释；
- 声称 thread-safe，但只有 writer 加锁、reader 全部无锁；
- 声称 Save/Load，却只序列化 DTO，没有完整 reconstruction path。

## 4. Canonical mutation 与 presentation delta 分开

容器 canonical state 的提交要立即完成并标记 FastArray dirty。UI/音效/日志等 projection 可以为了降低 churn，在同一帧或 next tick 合并通知。

### 4.1 允许合并的东西

- 同一 Cell 多次 `Change` 合成最终一次 Changed；
- 一批相邻 cell mutation 合成一次 UI refresh message；
- 多个 FastArray callback 转成一个 view-model patch。

### 4.2 必须定义的 folding 语义

同一 index 在一个 coalescing window 中可能出现：

- Add -> Change；
- Add -> Remove；
- Remove -> Add（replacement）；
- Change -> Change；
- Move 涉及两个 index。

不能只把三个 index 数组分别 `AddUnique()`。要定义最终语义和事件顺序，例如：

- Add -> Remove：如果从未对外可见，可以折叠成 no-op；
- Remove -> Add：通常是 Replace，至少要保留 old/new identity；
- Change -> Change：只发布最终 revision；
- JIP：initial snapshot 不伪装成“玩家刚捡到物品”的 Add event。

### 4.3 next-tick 生命周期

延迟到下一帧的 lambda/timer 仍然属于异步 re-entry：

- 用 weak/lifetime-safe owner；
- teardown 时取消 timer/registration；
- callback 重新检查对象/host/generation；
- 不捕获短生命周期引用；
- canonical transaction 不能等待这个 projection callback 才算完成。

## 5. FRWLock 不是 UObject thread-safe 证明

先决定线程所有权，再决定是否需要锁。

### 5.1 默认建议

Inventory canonical UObject graph、Blueprint delegates、replication、subobject registration 由 GameThread 拥有。

如果只在 GameThread 读写，那么一个“看起来高级”的 `FRWLock` 往往只是装饰性复杂度。

### 5.2 真正跨线程时

若确实有 POD/native snapshot 数据跨线程：

- writer 和 reader 必须参与同一个同步合同；
- `FWriteScopeLock` + 所有 reader 无锁，不叫 thread-safe；
- 锁区内不要调用 Blueprint、UObject delegate、RPC、Asset load 或可重入业务；
- 锁区只保护可明确枚举的数据；
- 将必要数据复制成 immutable snapshot 后，再在其他线程计算；
- 结果回 GameThread 后重新验证 generation/revision 再 commit。

要记录 thread-affinity assertion、压力测试或 sanitizer/TSAN 证据。没有这些证据时只能写“有 writer lock”，不能写“线程安全”。

## 6. Client request 不能选择任意服务器实现类/函数

Owner-only RPC route 只证明“这个连接能调用此 Actor/Component”，不证明客户端能选择任意业务操作。

生产入口优先：

```text
Client
  -> OperationId / GameplayTag / typed request DTO
Server
  -> server-owned registry / allowlist
  -> operation-specific validator
  -> Authority resolve current state
  -> execute
```

禁止把下面设计当默认：

- client 传任意 `TSubclassOf<UTransaction>`，server 直接 `NewObject` + execute；
- client 传 `RemoteClass + FuncName`，server 对 CDO `ProcessEvent()`；
- client 提交裸 Container UObject pointer 就被视为已授权。

### 6.1 Authority 必查

每笔容器请求至少按需要验证：

- requesting Player/Controller/connection；
- operation allowlist；
- source/target `ContainerId` 是否对该请求者可访问；
- world chest/trade/session 是否仍有效；
- `ItemId`、expected generation/revision；
- source slot 当前仍指向该 Item；
- target capacity/compatibility/reservation；
- action lock / death / stun / trade state；
- rate limit / replay / duplicate TransactionId。

Raw UObject pointer、slot index、client-selected class 都只是候选。

## 7. Transaction state machine 不等于原子性

`Started -> Executing -> Failed` 只能说明状态机失败；它不证明前面已经写入的 mutation 被撤销。

### 7.1 推荐事务结构

```text
Request
 -> resolve stable IDs
 -> authorize capability
 -> preflight every participant
 -> reserve/lock logical resources
 -> build before-image + write-set
 -> revalidate
 -> single commit point
 -> mark dirty / replicate
 -> publish side effects
 -> response
```

### 7.2 两种可接受原子策略

**A. Commit phase 不可失败**

先把全部条件、对象、容量、资产依赖验证完，再构造完整 write-set。真正 commit 只做确定成功的内存写入。

**B. 有测试过的 rollback / compensation**

保存 before-image，每一步有逆操作；任何一步失败后恢复所有已修改 participant，然后再发布 Failure。

不能把“child transaction 失败会 bubble parent”写成 rollback。

### 7.3 Child result 必须 gate 下一步

错误模式：

```text
Eject target
Assign source to target
Assign target to source
parent later sees Failed
```

如果第二或第三步失败，前面的 mutation 已经提交。

每个 child operation 必须有明确 result：

- object returned != success；
- delegate fired != success；
- parent final Failed != rollback；
- mutation context `State` / typed result 必须检查。

失败后禁止继续：

- rename/reparent；
- register/unregister subobject；
- grant/revoke GAS；
- destroy item；
- publish gameplay/UI event。

## 8. Idempotency 与 stale request

可靠 RPC 也不能替代业务 idempotency。

请求建议包含：

- `RequestId/TransactionId`；
- operation type；
- stable source/target ContainerId；
- ItemId；
- expected source generation/revision；
- bounded target slot/amount/options。

服务器可缓存最近完成请求结果，重复 RequestId 返回同一结果而不再执行 mutation。断线重连、UI 重发、timeout retry 都要测试。

## 9. Reference/Link item：引用 canonical truth，不复制 truth

Hotbar、收藏、装备快捷位、Quest tracker 常常不需要另一份完整 Item。

推荐：

```text
LinkSlot
  Stable ItemId
  Optional desired ContainerId / semantic slot
  Runtime resolution cache (pointer/index/generation)
  Accessible / Missing reason
```

源 Item move/eject/load/reconnect 后：

1. cache 可失效；
2. Link 按 ItemId re-resolve；
3. accessibility 根据当前 Authority/view permission 更新；
4. 删除 Item 后 link 显示 Missing，不绑定到同类新物品。

不要把 `(Source UObject*, SourceContainer*, SourceIndex)` 当跨会话 link identity。

## 10. Snapshot / Save：先重建身份图，再发布 live state

一个“能把 struct 转 JSON”的 Snapshot DTO 不等于 Save/Load 系统。

生产 snapshot 至少考虑：

- `SchemaVersion`；
- `ContainerId`；
- `ItemId`；
- `DefinitionId` 或迁移稳定 class/asset identity；
- stack / slot / generated state；
- nested/link/reference edges；
- optional tombstone/version；
- game/domain version migration。

### 10.1 两阶段/多阶段 load

推荐：

```text
parse
 -> migrate schema
 -> validate all IDs/classes/assets
 -> instantiate canonical containers/items
 -> first pass: scalar state
 -> second pass: resolve ItemId/ContainerId links
 -> validate graph/cycles/duplicates
 -> atomic replace live state
 -> register subobjects
 -> mark replicated state dirty
 -> publish UI/messages
```

禁止：

```text
clear live inventory
 -> load first cell
 -> fail on missing class
 -> leave player with half inventory
```

### 10.2 Class load

- Save/load UI 可以显式进入 loading phase；
- 高速 online transaction 里禁止 `LoadClass/LoadSynchronous`；
- missing/renamed class 走 migration table、fallback 或明确 reject；
- DefinitionId 比直接保存裸 class path 更容易做内容迁移。

## 11. UObject world context

Replicated Item/Fragment UObject 若需要 `GetWorld()`：

- 优先从 stable Outer/host Actor/world-context owner 获取；
- 没有合法 world 时返回 null/拒绝操作；
- 不把 `GEngine->GetCurrentPlayWorld()` 作为生产默认。

原因：PIE 可以存在多个 World；Dedicated Server、client、editor preview、commandlet 的 current play world 语义不同。

Outer 转移同时会影响：

- `GetWorld()`；
- RPC callspace；
- NetDriver；
- GC lifetime；
- registered subobject host。

所以 reparent 是 transaction 生命周期的一部分，不是 cosmetic rename。

## 12. Fragment 成本阶梯

“Fragment composition”是好思想，但实现形态按成本升级：

1. **Static Definition / DataAsset fragment**：静态配置，无 per-item runtime object。
2. **`FInstancedStruct` typed state**：耐久、roll、socket 等值型实例状态。
3. **optional UObject behavior fragment**：需要 Blueprint polymorphism、独立 delegate/RPC/replication lifecycle 时才创建。
4. **Actor**：需要 world transform/collision/tick/relevancy 时才升级。

大量材料/货币/普通堆叠物，不要“一件物品多个 replicated UObject fragment”。

## 13. Combee 固定快照的选择性结论

针对 `nulla-sutra/unreal-combee@971fa227179a99d308956b7031d5422634cefbfd`：

可吸收：

- cell FastArray + registered UObject subobject 的双合同意识；
- unique/shared/link 三种语义的区分；
- link/source accessibility 的事件驱动刷新；
- canonical commit 后合并 next-tick presentation callback；
- per-controller Bridge + TransactionId + child command 结构；
- `FInstancedStruct` typed payload；
- push-based dirty。

不直接采用：

- 将 experimental plugin 视为 production-ready；
- 声称 active Iris FastArray（固定源码仍走传统 FastArray branch）；
- 只有 writer lock 就写 thread-safe；
- generic client-selected transaction class / remote function dispatch；
- 把 failure bubbling 当 rollback；
- README 的 atomic/rollback 声明替代 active source；
- 先 clear live container 再进行不完整 snapshot restore；
- UObject `GetWorld()` 使用 global current play world；
- add subobject 有路径、remove 生命周期没有 active 对称调用仍称完整。

## 14. 最低验收矩阵

1. 两客户端同时 move 同一 Item，只有一笔 commit。
2. stale index + wrong ItemId/generation 被拒绝。
3. 伪造另一个玩家 ContainerId 被拒绝。
4. 伪造 operation/class/function 无法选择服务器实现。
5. child 1/2/3 每个边界注入失败，无半交换/丢失/复制。
6. duplicate TransactionId 幂等。
7. JIP 能重建 FastArray + subobject graph。
8. move/eject/replace 后旧 host registration 归零。
9. disconnect/reconnect 后 link 按 ItemId 重解。
10. snapshot 缺 class/旧 schema/重复 ID 时 live inventory 不被半清空。
11. Listen Host 与 Remote 收到等价、单次 presentation delta。
12. multi-PIE/DS 获取正确 World/NetDriver。
13. 1k/10k/50k items 下统计 entry size、rep bandwidth、callback churn、GC UObject 数量。
14. 如宣称线程安全，reader/writer 压力验证与 thread-affinity assertion 有证据。
