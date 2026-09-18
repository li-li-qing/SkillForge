# LGF Container Transaction、Link 与 Replicated Item 合同

> 用于把外部 Inventory/Container 思想迁入 LGameplayFramework，而不建立第二套真值或绕过现有 Authority/Request/Foundation。

## 1. LGF 先保留现有业务 Authority

外部容器库的 Bridge、Transaction、Container Component 只能提供参考机制。LGF 的业务真值仍由现有 Inventory/Equipment/Stash/Request/Authority 体系拥有。

迁入任何外部 transaction 前，先回答：

- 现在谁拥有 `ItemId` 真值？
- 谁能授权访问该 Container？
- 当前是否已有 ActionLock / Request / result path？
- Equipment/GAS side effects 从哪里提交？
- Save schema 是否已经依赖现有 ItemId/ContainerId？

没有这些答案，不创建平行 Bridge/Inventory truth。

## 2. Container Capability：owner RPC 不是库存授权

玩家有权调用自己的 Server RPC，不代表他有权修改 payload 指向的任意 Container。

Authority 请求应重新解析：

```text
Player/Controller
 + OperationId
 + SourceContainerId
 + TargetContainerId
 + ItemId
 + expected generation/revision
 + bounded slot/amount
 -> Resolve capability/access
 -> Re-resolve current state
 -> Validate
 -> Commit
```

### 2.1 capability 来源

按容器类型可来自：

- 自己的 Inventory/Equipment/Stash 固定 owner；
- 打开的 World Chest interaction session；
- 当前 Trade session；
- Party/Shared storage ACL；
- Crafting station interaction；
- Loot reservation；
- server-issued short-lived access token/session generation。

关闭箱子、离开距离、trade cancel、死亡、Avatar 替换后，旧 capability 失效。

## 3. Server-owned Operation Registry

LGF 不允许客户端把任意 `TSubclassOf<Transaction>` 或 `RemoteClass + FuncName` 送给 Server 决定执行路径。

优先使用：

```text
EInventoryOperation / GameplayTag OperationId
  -> server-owned registry
  -> typed validator
  -> typed executor
```

unknown operation 默认拒绝。

即使为了扩展性使用 class registry，也由服务器配置 `OperationId -> Class`，客户端只发 OperationId。

## 4. Cross-container atomic transaction

Inventory -> Equipment -> Stash -> Hotbar 的跨域操作使用一笔 transaction identity。

### 4.1 推荐 phases

1. Resolve stable IDs。
2. Authorize all container capabilities。
3. Validate source ItemId/generation/revision。
4. Validate target capacity/compatibility。
5. Reserve participating slots/items in deterministic order。
6. Build before-image + write-set。
7. Revalidate after any async/reservation boundary。
8. Commit canonical container state。
9. Transfer registered subobjects / runtime host。
10. Apply Equipment/GAS grant/revoke。
11. Publish GameplayMessage/UI projection。
12. Return typed result and cache TransactionId outcome。

### 4.2 failure

父 transaction `Failed` 不是 rollback。

如果 commit phase 可能失败：

- before-image 能恢复每个 participant；
- rollback 也验证 ItemId/generation，不能覆盖后来合法修改；
- rollback failure 是高等级诊断事件；
- 最终可用 authoritative snapshot/reconcile 兜底。

如果能预构建不可失败 write-set，优先减少 rollback 复杂度。

## 5. Link Slot：Hotbar 不复制 Item truth

Hotbar、收藏、快捷使用、装备 intent 保存：

- stable `ItemId`；
- 可选 semantic slot / desired ContainerId；
- runtime cache：pointer/index/generation；
- resolution state：Resolved / Missing / Inaccessible / Pending。

Source Item move 后：

- Link 不跟着复制一个新 Item；
- cache 失效后按 ItemId 重解；
- 如果 Item 被销毁，Link 变 Missing；
- 同 Definition 新物品不会自动冒充原 ItemId。

这对“背包物品 -> Hotbar -> 装备 -> 仓库”尤其重要。

## 6. Replicated Item UObject transfer

LGF 只有复杂唯一物品才升级成 replicated UObject。

跨容器时区分：

- **business owner**：ContainerId/ItemId；
- **network host**：哪个 Actor/Component 注册 subobject；
- **Outer**：GC/RPC/world context；
- **presentation owner**：当前 Equipment Actor / mesh / UI。

它们可能一致，但不能用一个指针隐式代表全部。

### 6.1 对称流程

需要记录并诊断：

- old host registered? descendants count?
- unregister old root + descendants；
- reparent/Outer change；
- register new root + descendants；
- FastArray/entry update；
- Host local projection；
- JIP/reconnect rebuild。

重复 register、remove missing、双 host 都要暴露诊断，而不是静默继续。

## 7. FastArray callback / UI notification

Canonical Inventory commit 立即完成。

如果为了 UI 性能 coalesce 一帧内 Cell changes：

- projection-only；
- 明确 Add/Remove/Replace/Change folding；
- JIP initial snapshot 不触发“获得物品”业务效果；
- Listen Host 与 Remote 最终每客户端一次表现事件；
- next-tick callback 在 Container/Avatar/Travel teardown 后不允许访问旧 provider。

LGF 可把最终 delta 转入现有 GameplayMessage/UIData，但消息不是业务真值。

## 8. Threading：Inventory UObject truth 默认 GameThread

LGF 不因为外部项目用了 `FRWLock` 就开放多线程写 Inventory UObject graph。

默认：

- UObject item/container；
- FastArray dirty；
- registered subobject；
- Blueprint delegates；
- GAS grants；

全部由 GameThread commit。

后台线程只接收 immutable POD snapshot 做：

- sorting/search scoring；
- offline serialization compression；
- expensive pure calculation。

结果回 GameThread 后按 generation/revision revalidate。

若未来确有 shared native cache，reader/writer 同锁合同单独设计。

## 9. Save / Snapshot 与 Runtime Replication 分开

LGF 继续使用稳定 Save identity，不采用 `ClassPath + slot + fragment JSON` 作为全部存档。

最低字段：

- SchemaVersion；
- ContainerId；
- ItemId；
- DefinitionId；
- stack/slot；
- generated state；
- nested/link edges；
- domain-specific state。

Load：

`parse -> migrate -> instantiate all IDs -> resolve edges second pass -> validate -> atomic replace -> rebuild runtime handles/subobjects -> publish`

禁止先 `ClearInventory()` 再逐 cell 边加载边失败。

## 10. Combee 对 LGF 的选择性映射

### 可以吸收

- Unique / Shared / Link 语义的分离；
- Link/accessibility 的事件驱动刷新思路；
- FastArray canonical mutation + frame-coalesced UI delta；
- registered subobject list 的复杂 Item escape hatch；
- transaction GUID、owner-scoped RPC route、server-only child command；
- typed `FInstancedStruct` payload；
- Push Model exact dirty。

### 只作为反例/待完成证据

- Experimental plugin 直接进入生产；
- `#if 0` 的 FIrisFastArraySerializer 被当作 active Iris；
- writer-only FRWLock 被称 thread-safe；
- client-selected transaction class / remote function；
- failure bubble 被称 rollback；
- Assign child 不检查底层 mutation result；
- Eject 在 child clear 失败后仍 reparent；
- snapshot clear-live-before-rebuild；
- snapshot 缺 stable ItemId/ContainerId/schema；
- AddReplicatedSubObject 有 active path，但 remove helper无调用证据；
- Item UObject `GetWorld()` 依赖 global current play world。

## 11. 与已有 LGF 规则的组合

- **Obsidian**：继续使用 SourceObject + exact GrantedHandles；
- **RockInventory**：继续使用 stable handle + value-state cost ladder；
- **AyaDog/Lyra**：长期 Inventory intent 与 applied Equipment 分层；
- **GAS R7**：client request/TargetData 仍是 candidate，Authority revalidate；
- **Xist R9**：UI 消费 projection，不拥有 truth；
- **Combee R10**：补 container capability、operation allowlist、subobject transfer、write-set atomicity 与 Link reference。

不是用 Combee 重写 Inventory Foundation，而是把这些缺口补到现有 LGF transaction contract。

## 12. LGF 验收场景

1. Inventory -> Equipment -> Stash 来回移动同一 ItemId。
2. Hotbar link 在 Item move 后自动重解，删除后显示 Missing。
3. 客户端伪造另一个玩家 ContainerId 请求被拒绝。
4. 客户端伪造 operation class/function 无执行路径。
5. 同一 TransactionId 重放不重复扣/加物品。
6. Swap 每个 child boundary 注入失败，无半状态。
7. complex Item move 后 old/new subobject registration 计数正确。
8. JIP / disconnect-reconnect 后 complex item 与 link 重建。
9. Listen Host 与 Remote UI delta 一次且语义一致。
10. Save load 缺 asset/旧 schema/重复 ID 时不破坏 live inventory。
11. Avatar 变身/骑乘不改变 stable inventory ItemId；applied equipment generation 正确 teardown/rebuild。
12. 50k materials 使用 struct/value path，不创建海量 replicated UObject fragments。
