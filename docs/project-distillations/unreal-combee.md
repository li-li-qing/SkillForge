# nulla-sutra/unreal-combee 源码蒸馏

> 第十轮外部 UE 项目研究。目标不是迁入 Combee 插件，而是验证现代 UE 容器系统在 FastArray、replicated UObject、transaction、link/reference item、threading 与 snapshot 上的真实生产边界。

## 0. 结论摘要

固定源码：

- Repository：`nulla-sutra/unreal-combee`
- Commit：`971fa227179a99d308956b7031d5422634cefbfd`
- Commit date：2026-06-30
- License：MPL-2.0
- Descriptor：`Combee.uplugin`
- Descriptor status：`IsExperimentalVersion = true`
- Descriptor 没有固定 `EngineVersion`

本轮 freshness 分类：

**Current source / Experimental adoption**

含义：

- 仓库本身不是旧项目；
- 2026 年仍维护；
- 使用 Push Model、registered subobject list、`FInstancedStruct`、UE_WITH_IRIS 等现代 API；
- 但 descriptor 明确 Experimental；
- 多个 README 宣称与 active source 不一致；
- 没有在本轮执行目标 UE5.7/5.8 UBT、PIE、Dedicated Server、JIP、disconnect/reconnect 或性能测试；
- 所以只能选择性吸收机制，不能写“可直接作为 LGF Production Inventory”。

最值得吸收：

1. canonical Cell FastArray 与复杂 UObject subobject 是两条独立复制合同；
2. Unique / Shared / Link 三类 Item 语义；
3. Link item 的 source accessibility 与 event-driven re-resolve；
4. canonical mutation 立即提交、UI mutation next-tick coalesce；
5. Push Model exact dirty；
6. per-controller owner-only Bridge + TransactionId；
7. child transaction / typed `FInstancedStruct` payload；
8. Item Outer 可以与 network host/lifetime 协作，但不能代替业务 stable ID。

最重要的拒绝项：

1. README 写 Iris FastArray，但 active Hive inheritance 被 `#if 0` 关闭；
2. README 写 rollback/atomic，active rollback 代码被注释；
3. Swap 多步 mutation，没有真正 rollback；
4. Assign 没有把底层 `AssignCell()` failure 纳入 transaction failure；
5. Eject 不检查 child clear success 就继续 reparent；
6. Bridge 允许客户端选择 `TSubclassOf<Transaction>`；
7. Bridge 还有 client-selected `RemoteClass + FuncName -> ProcessEvent` 的 generic server route；
8. FRWLock 只有 writer 证据，没有 reader lock；
9. AddReplicatedSubObject 有 active path，但 Remove helper 没找到 active caller；
10. Snapshot README 描述完整 restore，但 active Apply 并没有重建 item graph；
11. Snapshot 缺 stable ItemId/ContainerId/SchemaVersion；
12. `UCombeeItem::GetWorld()` 返回 global current play world，不适合多 PIE/DS 生产默认。

---

## 1. 为什么研究 Combee

前几轮已经覆盖：

- Obsidian：Item Definition / Instance / Fragment、GAS Equipment grant、Stash/Save；
- RockInventory：Struct-first、Index+Generation、typed ItemState、ItemData/SlotData、Transaction skeleton；
- AyaDog/Lyra：长期 Inventory 与 Applied Equipment 生命周期；
- GASDocumentation/GASShooter：SourceObject、SpecHandle、Prediction/TargetData；
- XistCommonGame：UI 是 projection，不拥有业务 truth。

Combee 的差异点是：

- 它把容器本身做成 replicated ActorComponent；
- Cell 是 FastArray；
- Item/Fragment 是 replicated UObject；
- Item transfer 会 reparent Outer；
- transaction 独立成模块；
- Link item 是一等类型；
- 还提供 Snapshot 模块。

因此它很适合用来验证：

> 当“值型容器 + UObject graph + transaction + save”同时出现时，哪些生命周期必须显式化。

---

## 2. 模块地图

`Combee.uplugin` 暴露：

- `Combee` Runtime
- `CombeeEditor` Editor
- `CombeeUse` Runtime
- `CombeePresets` Runtime
- `CombeeUI` Runtime
- `CombeeTransaction` Runtime
- `CombeeSnapshot` Runtime

Optional/Enabled dependency 包含：

- UE5Coro
- Paper2D

注意：

**模块存在不等于本轮所有模块都被生产审查通过。**

本轮重点：

- Core Container/FastArray
- Core Item/Fragment
- Preset Unique/Shared/Link
- Transaction/Bridge
- Preset Move/Swap/Assign/Eject
- Snapshot

`CombeeUse`、UI、Editor 只在与核心合同相关时参考，没有将其全部蒸馏。

---

# Part A — Container / FastArray

## 3. FCombeeCell

Cell 是 `FFastArraySerializerItem`。

核心字段：

- Item interface reference
- StackCount
- Container
- Index
- Version

### 3.1 好的方向

Cell 明确把：

- item identity/reference；
- stack；
- slot position；
- local change revision；

放在同一个 mutation entry 周围。

这适合用 FastArray 做细粒度 delta。

### 3.2 LGF 需要继续拆 identity

`Cell.Version` 不是 stable ItemId。

`Cell.Index` 不是 stable ItemId。

FastArray ReplicationID 也不是 stable ItemId。

LGF 继续需要：

- persistent ItemId；
- persistent ContainerId；
- runtime slot/generation；
- replication bookkeeping。

分别存在。

---

## 4. FCombeeHive 与 Iris 证据

源码 include：

`Iris/ReplicationSystem/FastArray/IrisFastArraySerializer.h`

但实际 inheritance：

```text
#if 0
FIrisFastArraySerializer
#else
FFastArraySerializer
#endif
```

所以固定提交的正确结论是：

**Hive active runtime path 使用传统 `FFastArraySerializer`。**

不能写：

> Combee 已经采用 FIrisFastArraySerializer。

### 4.1 本轮新增时效性规则

以后外部项目每个机制都区分：

- Declared；
- Compiled；
- Runtime-active；
- Verified。

“include 了新 API”只到 Declared。

---

## 5. FastArray callback 语义

Combee callback 会把：

- PreRemove -> Remove；
- PostAdd -> Add；
- PostChange -> Change；

投影到容器 mutation 通知。

PostAdd 还会对包含 Item 的新 Cell 合成一次 Change。

### 5.1 值得吸收

这说明作者在尝试把：

`network delta callback`

标准化为：

`container semantic change`

这与之前 RockInventory 的 semantic delta classification 是同一方向。

### 5.2 必须继续收紧

FastArray callback 是本地 projection，不是业务 transaction 起点。

UI：

- 可以消费 Add/Remove/Change；
- 不能通过 callback 再执行 authoritative inventory operation；
- JIP snapshot 与“玩家刚获得 Item”必须分开。

---

## 6. UCombeeContainer

Container 是 `UActorComponent`：

- Tick disabled；
- replicated by default；
- registered subobject list enabled；
- Hive 使用 Push Model。

这是现代方向。

### 6.1 Central mutation point

`AssignCell()` 是 central mutation path。

它执行：

- index validation；
- current/upcoming state comparison；
- stack validation；
- compatibility；
- before context；
- write；
- item registration/reparent；
- dirty；
- mutation delegates；
- ForceNetUpdate。

“所有写入收敛到一个函数”本身很有价值。

### 6.2 但 mutation context 不是安全边界

`AssignCell()` 被标成 Authority-only Blueprint 函数，并不意味着上层 request 已经授权。

Authority 仍需知道：

- 谁请求；
- 是否能访问此 Container；
- Item 当前是不是请求里那一件；
- slot revision 是否仍匹配；
- 是否存在 trade/chest/loot session。

---

## 7. next-tick mutation coalescing

MarkIndexDirty 一类路径会：

- 立即改 canonical state；
- 立即 FastArray dirty；
- 把 Add/Change/Remove index 放进集合；
- `SetTimerForNextTick` 后统一广播。

### 7.1 可吸收机制

这适合 UI：

- 一个 transaction 改 20 个 Cell；
- 不需要刷新 UI 20 次；
- canonical state 仍然已经完成。

### 7.2 R10 补的 contract

必须定义：

- Add -> Remove；
- Remove -> Add；
- Change -> Change；
- Replace；
- Move 两 slot；

一帧内如何 folding。

否则三个 `TArray<int32>` 去重不等于正确 semantic delta。

### 7.3 lifetime risk

next-tick lambda 捕获 `this`。

如果 Container 在 callback 前销毁/Travel，需要：

- weak binding；
- timer cancellation；
- owner generation；
- 或可证明 TimerManager lifetime safety。

不能只因为“只有下一帧”就忽略异步生命周期。

---

# Part B — Threading

## 8. FRWLock 审查

Container 声明 `FRWLock`。

搜索固定提交：

- 有 `FWriteScopeLock`；
- 没找到对应 `FReadScopeLock` 读路径。

README 将其描述为 read-write lock/thread-safe 机制。

### 8.1 正确结论

只能说：

> 当前存在 writer-side lock。

不能说：

> Container thread-safe。

### 8.2 为什么

writer 加锁但 reader 无锁：

- data race 仍可能存在；
- lock 没有形成 happens-before reader contract。

另外 Inventory graph 包含：

- UObject；
- Blueprint events；
- Net replication；
- registered subobject；
- Rename/Outer；

这些操作也不能靠一个数据锁自动变线程安全。

### 8.3 LGF 结论

默认 GameThread ownership。

后台线程只处理 immutable/native snapshot。

如果未来真的多线程：

- POD/native state 单独隔离；
- reader/writer 同步成套；
- callback/UObject side effects 回 GameThread；
- 用 generation/revision re-entry。

---

# Part C — Item Representation

## 9. UCombeeItem_SHARED

Shared Item 返回 Class Default Object。

语义适合：

- gold；
- wood；
- basic resource；
- identityless stack commodity。

### 9.1 值得吸收的是语义，不是实现形式

LGF 已经从 RockInventory 得到 struct-first cost ladder。

因此 LGF 不需要把所有 stackable material 变成 CDO UObject。

真正的结论是：

> identityless、immutable、只有 stack count 的对象不需要独立实例状态。

---

## 10. UCombeeItem_UNIQUE

Unique Item：

- runtime NewObject；
- per-instance fragments；
- kill lifecycle；
- Outer 可转入 Container。

语义适合：

- durability weapon；
- generated gear；
- enchantment；
- instance-bound state。

### 10.1 与 RockInventory 对照

RockInventory：

`Stack -> typed ItemState -> optional UObject ItemInstance`

Combee：

`Item UObject -> Fragment UObject -> FInstancedStruct Rna`

对于大量普通装备，RockInventory 更省 object count。

对于：

- fragment 独立 RPC；
- Blueprint polymorphism；
- fragment 独立 replicated state；

Combee 更灵活。

所以 R10 形成四级成本阶梯，而不是选一个项目的模型覆盖另一个。

---

## 11. UObject Fragment + Rna

每个 Fragment：

- 是 UObject；
- supported networking；
- Rna 是 replicated `FInstancedStruct`；
- Push Model dirty；
- 可注册 Iris replication fragments；
- 可拥有 RPC callspace。

### 11.1 优势

行为和 mutable state 分开：

- UObject 提供 behavior shell；
- Rna 提供 typed state。

### 11.2 成本

每 Item 多 Fragment 会增加：

- UObject count；
- GC traversal；
- registered subobject bookkeeping；
- replication descriptors；
- delegate lifetime；
- Save serialization paths。

### 11.3 LGF 默认

1. static definition fragment；
2. typed struct state；
3. optional behavior UObject fragment；
4. Actor。

按需求升级。

---

# Part D — Link Item

## 12. UCombeeItem_LINK

这是本轮最有新意的部分。

Link 保存：

- SourceItem；
- SourceContainer；
- SearchCache；
- accessibility。

它监听 Source Container mutation。

Source 变化后不会每次立即重新搜，而是 next tick throttle。

### 12.1 可映射场景

LGF：

- Hotbar；
- Favorite；
- quick-use；
- equipment intent；
- quest item reference；
- pet summon item reference。

### 12.2 LGF 要改成 stable identity

不能保存：

`UObject* + Container* + Index`

作为永久 link identity。

应保存：

- ItemId；
- optional ContainerId；
- semantic slot/intent。

runtime pointer/index 只是 cache。

### 12.3 为什么重要

Item 从 Backpack 移到 Equipment：

- Hotbar 不应复制 Item；
- 不应因为 slot 变了就失效；
- 应按 ItemId 找到同一业务对象。

Item 真正删除：

- Link 变 Missing；
- 同 Definition 新 Item 不能冒充旧 ItemId。

---

# Part E — Replicated Subobject

## 13. Add 路径

Combee 在 Item 进入 Container 时会：

- AddReplicatedSubObject(item)；
- collect nested subobjects；
- add descendants。

方向正确。

## 14. Remove 路径证据不足

仓库有 `ContainerTryRemoveReplicateSubobjectItem()` helper。

但固定提交 code search：

- 找到声明；
- 找到定义；
- 没找到 active caller。

`AssignCell()` replace/clear path 可见地注册 upcoming item，但没有可见对称 unregister previous item。

### 14.1 为什么这是 blocker

跨容器 move 如果：

- old host 仍注册；
- new host 又注册；

可能导致：

- stale replication；
- duplicate host；
- relevancy 泄漏；
- destroy/reconnect cleanup 异常。

### 14.2 LGF 合同

每次 complex Item transfer 都显式记录：

- old host；
- old registration count；
- descendants；
- remove result；
- new host；
- add result。

并纳入 diagnostics。

---

## 15. Outer as ownership

Combee 会 Rename Item 到 Container 作为 Outer。

### 15.1 好处

Outer 链可以帮助：

- GC；
- GetTypedOuter Actor；
- RPC routing；
- fragment host resolution。

### 15.2 不能外推

Outer 不是：

- persistent ItemId；
- Save ContainerId；
- permission ACL；
- stable business ownership。

LGF 要显式分开。

---

## 16. UCombeeItem::GetWorld 风险

Base Item 的 `GetWorld()` 返回 global current play world。

这在简单 PIE 可能工作。

但生产风险：

- multi-process PIE；
- single-process multi-world PIE；
- listen server + client world；
- Dedicated Server；
- Editor preview；
- commandlet。

更安全：

从 stable Outer/host Actor 获取 World。

如果没有 world，返回 null/拒绝需要 world 的操作。

---

# Part F — Transaction

## 17. Base Transaction

Base Transaction 有：

- FGuid TransactionId；
- FInstancedStruct Payload；
- Started / Executing / Success / Failed；
- Parent/Root；
- child transaction；
- failure bubble。

这是一个不错的 command skeleton。

### 17.1 但 rollback 不存在于 active path

源码有 rollback 相关代码，但整段被注释。

所以：

- failure bubble 是 active；
- rollback 不是 active。

README “rollback support” 不能晋级为当前实现事实。

---

## 18. ACombeeBridge

Bridge：

- owner-only；
- per-controller；
- no movement；
- RPC request/response；
- TransactionId；
- server child execution。

### 18.1 可吸收

owner-scoped command route 比：

- GameState Server RPC；
- arbitrary world actor RPC；

更合理。

### 18.2 关键安全问题：client-selected transaction class

Server RPC 接收：

- TransactionClass；
- Payload；
- TransactionId。

Bridge 自身没有可见 allowlist。

所以客户端可以选择“服务器要 instantiate 哪个 Transaction class”。

LGF 不采用。

### 18.3 更强风险：ConventionalRemoteCall

Server RPC 还允许：

- RemoteClass；
- FuncName；
- Instigator；
- Payload。

服务器：

- 找 CDO；
- `FindFunctionChecked(FuncName)`；
- `ProcessEvent()`。

即使目标函数内部可以验证，这种入口仍扩大攻击面。

生产默认应改成：

`OperationId -> server registry -> typed validator/executor`

客户端不能决定 arbitrary class/function。

---

# Part G — Authority Access

## 19. Owner RPC 不等于 Container capability

客户端拥有自己的 Bridge。

但 payload 可以引用：

- FromContainer；
- TargetContainer；
- slot index。

Move/Swap 的 visible validation 主要是：

- IsValid；
- index；
- compatibility。

没有证明：

- container 属于该玩家；
- chest 正打开；
- trade session 仍有效；
- 玩家仍在 range；
- loot reservation 属于该玩家。

### 19.1 LGF 新增 container capability

访问权由 Authority 根据 domain 解析。

例如：

- personal inventory：PlayerId owner；
- world chest：InteractionSessionId；
- trade：TradeSession generation；
- party stash：ACL；
- loot：Reservation token。

Request 中 raw pointer 不是 authority proof。

---

# Part H — Atomicity

## 20. Move

Move 根据目标状态分发到：

- Merge；
- Swap；
- Resize + Swap。

结构清晰。

但 child transaction 的组合本身不提供 atomicity。

---

## 21. Swap active code

顺序：

1. Eject target；
2. Assign source -> target；
3. Assign old target -> source。

如果步骤 2/3 失败：

- parent 可以 Failed；
- 但之前的 mutation 已经发生；
- active rollback 不存在。

因此 README “Atomic operation” 与 active code 不一致。

### 21.1 LGF 迁移

跨容器 move/swap：

- preflight all participants；
- before-image/write-set；
- commit phase 尽量不可失败；
- 或真正 rollback/compensation。

---

## 22. Assign failure propagation bug pattern

Assign 调用 Container::AssignCell。

源码原本显然计划检查：

`ResultContext.State != Success`

但该检查当前被注释。

于是：

- 底层 AssignCell 可以返回 Failed；
- Transaction 自身仍可能自动落到 Success。

这是非常重要的 anti-pattern。

> “调用过 mutation API”不等于“mutation succeeded”。

---

## 23. Eject failure propagation

Eject：

1. child Assign clear；
2. 不检查 child result；
3. 如果原 Item 存在，Rename 到 transient package。

极端失败：

- cell 没真正 clear；
- item 却 reparent 了；
- container still references item；
- network host/Outer/business ownership 不一致。

### 23.1 新规则

任何 teardown/reparent/grant/revoke 都必须在 canonical mutation success 后执行。

---

# Part I — Idempotency / Concurrency

## 24. TransactionId 是好基础，但不是完整 idempotency

TransactionId 存在。

但生产还需要：

- duplicate request result cache；
- stale request detection；
- ItemId/generation；
- deterministic reservation；
- retry/reconnect semantics。

Reliable RPC 不会自动替你做业务去重。

---

## 25. 并发访问

两个 client 同时从 shared chest 取同一 Item：

必须决定：

- 谁先 reserve；
- 第二笔如何失败；
- slot revision 是否变化；
- TransactionId replay 如何处理。

FRWLock 不解决业务竞争。

业务竞争靠 Authority transaction + revision/reservation。

---

# Part J — Snapshot / Save

## 26. Snapshot DTO active source

实际 snapshot type 保存：

- FragmentClassPath；
- Fragment JSON；
- ItemClassPath；
- fragments；
- Cell Index；
- StackCount；
- Container Capacity。

没有：

- SchemaVersion；
- ItemId；
- ContainerId；
- DefinitionId；
- link graph IDs。

README 展示的 ItemGuid / ContainerClass 等字段与当前 active types 不一致。

---

## 27. CreateSnapshot

Create Container Snapshot：

- 遍历非空 Cell；
- 保存 Item class path；
- 保存 Fragment data。

作为 debug DTO 有用。

作为长期 Save：不足。

---

## 28. ApplyContainerSnapshot

active source：

1. `ClearContainer(Container)`；
2. 遍历 snapshot cells；
3. 获取 current Cell；
4. 如果 current Cell.Item 存在，则 ApplyItemSnapshot；
5. 用 current Cell.Item + snapshot stack 调 AssignCell。

问题：

**clear 之后 current Cell 通常没有 Item。**

代码没有：

- 根据 ItemClassPath instantiate；
- stable identity map；
- nested/link second pass；
- before-image rollback；
- schema migration。

所以不能称完整 restore。

---

## 29. LoadClass 同步路径

ApplyItemSnapshot / ApplyFragmentSnapshot 会 `LoadClass`。

Save/load loading phase 可以接受显式 blocking 策略，但：

- online inventory transaction 不应这么做；
- 大量 Item restore 可能有 hitch；
- packaged missing class 需要 migration/reject。

LGF 继续用 DefinitionId + registry/asset preload/migration。

---

## 30. 正确 Save graph

生产 load：

1. parse；
2. schema migrate；
3. validate class/definition IDs；
4. instantiate all ContainerId / ItemId；
5. apply scalar state；
6. second pass resolve Link/Nested edges；
7. detect duplicate/cycle；
8. build complete new graph；
9. atomic replace live graph；
10. register runtime subobjects；
11. rebuild runtime handles/index；
12. publish UI。

不能先 clear live inventory 再边读边失败。

---

# Part K — 与前面项目的综合决策

## 31. Obsidian vs RockInventory vs Combee

| 问题 | Obsidian | RockInventory | Combee | LGF 默认 |
|---|---|---|---|---|
| Static Definition | strong | strong | class/CDO-oriented | DataAsset/Definition |
| Mutable state | UObject ItemInstance | typed ItemState | UObject Fragment + Rna | typed state first |
| Large materials | heavier | compact | Shared CDO semantics | compact struct |
| Stable runtime handle | basic | Index+Generation | Cell index/version | Index+Generation |
| Persistent ItemId | yes direction | explicitly separate | snapshot lacks | required |
| FastArray | yes | yes | yes | scale/churn based |
| Item/Slot split | limited | explicit dual arrays | Cell combined | use domain need |
| UObject replication | yes | optional | central | optional escape hatch |
| Link item | limited | can model state | explicit LINK | stable ItemId link |
| Transaction | implicit/domain | explicit but WIP | explicit hierarchy but no rollback | server-owned atomic write-set |
| Registered subobject | yes | yes | yes but remove evidence incomplete | symmetric lifecycle |
| Snapshot | save domains | stable-ID guidance | incomplete active restore | versioned graph rebuild |

---

## 32. 技术时效性最终评级

### Current

- FastArray delta replication；
- registered subobject list；
- Push Model dirty；
- FInstancedStruct typed payload/state；
- server Authority transaction concept；
- owner-scoped RPC bridge；
- event-driven link refresh。

### Current but incomplete / experimental in this snapshot

- Combee整体 Production adoption；
- Iris FastArray；
- subobject unregister transfer；
- thread-safety claim；
- rollback/atomic transaction；
- snapshot full restore。

### Reject for LGF production default

- arbitrary client-selected TransactionClass；
- RemoteClass + FuncName generic server ProcessEvent；
- global current play world；
- failure bubble == rollback；
- reader 无锁但称 thread-safe；
- class path + JSON == stable Save identity。

---

# Part L — SkillForge 写回

## 33. UE C++

新增：

`references/container-transactions-and-subobjects.md`

重点：

- active-code evidence；
- subobject symmetric transfer；
- frame-coalesced projection；
- threading ownership；
- operation allowlist；
- transaction atomicity；
- link stable identity；
- snapshot graph；
- UObject world context；
- fragment cost ladder。

新增 behavior：

- CPP-52 external active-code evidence；
- CPP-53 symmetric subobject transfer；
- CPP-54 frame-coalesced projection；
- CPP-55 FRWLock/thread ownership；
- CPP-56 server-owned operation registry；
- CPP-57 failure != atomicity；
- CPP-58 snapshot stable identity graph；
- CPP-59 UObject world context。

---

## 34. LGF

新增：

`references/container-transaction-contracts.md`

新增 behavior：

- LGF-37 link by ItemId；
- LGF-38 container capability；
- LGF-39 cross-container atomic write-set；
- LGF-40 replicated item subobject transfer/reconnect。

不会：

- 引入 Combee runtime 依赖；
- 替换 LGF Inventory Foundation；
- 用 Combee transaction bridge 覆盖现有 Request/Authority；
- 用 UObject Fragment 覆盖所有 typed state。

---

# Part M — 建议 LGF 后续真实验证

## 35. Network

如果未来吸收这些合同，至少测试：

- Listen Host；
- Remote Client；
- Dedicated Server；
- JIP；
- disconnect/reconnect；
- packet latency/loss；
- shared chest contention。

## 36. Subobject

- move complex Item 100 次；
- old host registration count 归零；
- new host 只有一份；
- nested descendants 同步；
- destroy host 无 stale item。

## 37. Transaction failure injection

在：

- preflight；
- reservation；
- source clear；
- target assign；
- reparent；
- GAS grant；
- UI publish；

每个边界人工注入失败。

业务结果只能：

- 完整旧状态；
- 或完整新状态。

不能半状态。

## 38. Save

- old schema；
- missing Definition；
- duplicate ItemId；
- missing link target；
- nested cycle；
- corrupted cell；
- interrupted load；
- load 后 reconnect/JIP。

## 39. Performance

按数据规模分别测：

- 1k material entries；
- 10k unique generated gear；
- 50k bulk items；
- number of UObject fragments；
- GC time；
- FastArray bytes；
- Net Insights；
- mutation callbacks/frame；
- UI patch time。

不能只用“FastArray”三个字推断性能足够。

---

# 40. 本轮没有验证的内容

没有执行：

- Combee UBT；
- UE5.7 build；
- UE5.8 build；
- Editor load；
- PIE；
- Dedicated Server；
- Iris runtime；
- JIP；
- reconnect；
- packet loss；
- GC benchmark；
- Net Insights；
- large inventory benchmark。

所以本报告是：

**固定源码 + 技术时效性 + Skill contract 层研究。**

不是：

**Combee Production certification。**
