# 网络请求、状态与复制

## 先分调用者、所有者和真值

Remote Owner 经拥有的网络对象/Agent 发 Request，再到 Server RPC；Authority 重新解析稳定身份、权限、资源、距离和当前状态后修改真值。SimulatedProxy 消费复制状态与本地表现，不提交 owner-only 请求。

Listen Host 同时具有 Authority 和本地玩家上下文。可在同一个 Request 门面内直接走 Authority 内核，无需强制给自己发 RPC；但仍需核对与 Remote 路径的业务校验、预算、结果和本地刷新是否一致。Dedicated Server 不依赖本地 Widget/Camera，但权威 Trace Mesh 可以是判伤所需数据。

函数名不是网络合同。核对 UFUNCTION 元数据和实现，例如当前 `ServerGiveAbilitySet` 是 Authority 调用入口，不是客户端 RPC。`BlueprintAuthorityOnly` 也不会自动跨网传输。

## 请求返回值不能统一猜测

| 当前入口类型 | 返回/结果边界 |
|---|---|
| 多数 Gameplay Request | 提交结果，不直接代表 Authority 业务成功 |
| Quest | `FLQuestRequestHandle`，读取其 SubmitResult，并关联最终操作结果 |
| UINavigation | 同步 Receipt，Presenter 的最终成功/失败另经结果事件 |
| ActionLock Request | bool；远端 true 表示发起请求，Authority 分支返回执行结果，仍应核对具体函数 |

不要为让文档看起来统一而修改生产 API。UI 的 Pending、Rejected、成功状态从实际结果协议驱动；超时不能直接等同没执行，重试要遵循业务幂等合同。

## ActionLock：带版本范围的接入提醒

以下来自取材版本的 `LGameplayActionLockComponent.cpp`，不是对所有 LGF 版本和组件的断言。任务开始时复核：

| 观察到的实现 | 应检查什么 |
|---|---|
| Start/Cancel 共用 RequestBudget | 高频 Start 后是否影响 Cancel；不能预设已经有独立终止预算 |
| RPC 的预算分支检查玩家 Pawn owner | Host 直接 Authority、PlayerState owner 与 Pawn owner 的覆盖差异 |
| Authority 自然完成广播 StateChanged 与 CompletedAuthority | 不假设与 Cancel/Ended 是相同语义 |
| Proxy OnRep 在序号改变且 active→inactive 时广播 Ended | 自然完成也可能满足该条件，不能用 Proxy Ended 结算奖励 |
| 替换旧锁时 Authority 广播旧锁 Ended | Proxy active→active 不走同一 Ended 条件，事件次数不是业务完成次数 |
| 状态/移动输入比例存在 | 不代表已自动接线 CMC、Mover 或 GAS，也不构成奖励/交易授权 |

接入先明确消费方和完成判据。解释任务只记录差异及影响；修复任务再按明确语义处理预算、终止和事件，并验证 Host/Remote/不同 owner、自然完成/取消/替换、限频后终止、JIP、死亡与销毁。不能以 UI 不再报错替代业务确认。

## FastArray、保存与可见性

核对 Item/Serializer 继承、NetDeltaSerialize/Traits、增改删 Dirty、OwnerComponent、复制回调和清理。回调用于呈现或派生缓存，不在客户端二次提交库存变更。

FastArray 已有条目/容器回调，不机械给每个 Item 加 OnRep。普通重要复制属性再核对 OnRep、GetLifetimeReplicatedProps、注册与条件、Host 本地通知和 JIP 恢复。

运行期 ReplicationID/Key 不能当作存档的稳定业务 ID。保存现有业务字段与身份，恢复走模块规定的重建流程；UIData/ViewData 不代替真实保存结构。

当前 Inventory 使用动态复制条件。先确认容器所有权、共享策略、消费者与相关性，再判断 OwnerOnly 是否合理；不能把个人背包、玩家查看的世界容器和公会仓库统一改成一个条件。

## Quest / Dialogue 的陈旧与重复请求

当前 Quest 按 RequestId 查结果缓存，同时比较 QuestId、OperationType 和 PayloadId。换奖励选项或业务操作不能冒用同一个 RequestId。限频与已经执行的业务结果须分开，按当前实现核对重试时机和缓存规则，不把任意失败都当永久结果或全部自动重试。

当前 Dialogue 选项协议关联 SessionId、ExpectedNodeId 和 OptionId；不能仅凭 OptionId 把迟到点击应用到新节点。节点指纹由当前 Agent 路径处理，项目 UI 应使用公开 Request 门面，不直接拼内部 RPC。

对所有这些操作，分别验证 Authority 修改次数、结果关联、UI 呈现次数和持久化结果。有效重复应幂等，参数改变、会话过期、权限变化应按契约拒绝。

## 表现层驱动源：队列条目事件与 UIData 事件的可见范围不同

`ULCraftingStationComponent` 同时暴露 `OnCraftingQueueEntryChanged` / `OnCraftingQueueEntryRemoved` 和 `OnCraftingStationUIDataChanged`。三者可见范围**不等价**：

- 队列条目事件的唯一广播链在**复制接收侧**：`HandleReplicatedQueueEntryChanged/Removed` → `QueueDeferredReplicatedQueueEntry*` → `Schedule/FlushDeferredQueueRepBroadcast`。Listen Host 或单机本地推进队列时不走这条链，因此这些事件**不广播**。
- `OnCraftingStationUIDataChanged` 在服务器每次推进完成后由 `BroadcastStationUIChanged()` 直接广播，客户端 OnRep 也广播。

结论：给制作台一类 Actor 挂表现层（动画、特效、进度显示）时驱动源用 UIData 事件；用队列条目事件会在 Host/单机上完全不动，而远端客户端看似正常，最容易误判为“资产或特效没配好”。

审计方法：判断一个委托的可见范围时，读**广播点的调用者链**，不要只读广播语句本身；“存在 Broadcast”不等于“本机会收到”。真值仍从复制队列的 view data 读取，事件只当“变化了”的信号。
