# LGF GAS 战斗预测、TargetData 与多来源能力合同

适用于 LGameplayFramework 消费工程中的 LocalPredicted 战斗、连续 Montage Section、双持/多刀刃、TargetData、装备 Ability grant、Avatar 切换和多表现层预测回滚。

本参考建立在 LGF 当前既有规则之上：

- Authority 拥有伤害、库存和装备真值；
- Request/owned Agent 承载客户端意图；
- Pawn + Mover 是运动路径；
- GASP/Linked Layer/武器 Mesh 是 presentation；
- Inventory ItemId 是持久身份；
- Codex 本轮实际项目补充的多刀刃 HitWindow/Sequence 规则继续有效。

外部 GASDocumentation/GASShooter 只提供机制证据。它们分别基于 UE5.3 社区文档和更旧 UE4 shooter 实现，不覆盖 LGF 当前 UE5.7/后续目标 API。

## 1. LGF 的 GAS identity 分层

一次战斗请求不要只用 AbilityClass 描述。

```text
Persistent Player / ASC Owner
  + AvatarGeneration
  + Equipment ItemId / EntryId
  + Runtime Grant Source
  + Ability SpecHandle
  + Activation / Prediction identity
  + Combo Sequence
  + Section
  + HitWindow generation
  + PartId / TraceSourceBinding
```

这些身份解决不同问题。

| 身份 | 用途 |
|---|---|
| ItemId | 存档、Inventory、跨重建业务身份 |
| Grant Source / SourceObject | 本次运行时能力来自哪件装备 |
| SpecHandle | 精确撤销/激活具体 AbilitySpec |
| Activation identity | 区分同一个 Spec 的不同激活 |
| AvatarGeneration | 拒绝旧 Pawn/形态迟到回调 |
| Combo Sequence | 续招请求防旧序列 |
| HitWindow generation | 命中窗口隔离与去重 |
| PartId / Trace binding | 左右刀/附加部件命中隔离 |

不要让其中一个 ID 同时承担所有职责。

## 2. 双持同 AbilityClass：来源必须隔离

左右手都可能授予 `GA_MeleeCombo` 或同一通用 AbilityClass。

Authority grant 时记录：

```text
ItemId / EquipmentEntry
Runtime SourceObject or source context
FGameplayAbilitySpecHandle
other GrantedHandles
```

卸右手：

```text
Right ItemId
→ right grant registry
→ exact SpecHandle(s)
→ revoke
```

不要：

```text
Find AbilityClass == GA_MeleeCombo
→ Clear all
```

也不要仅靠 GameplayTag / InputTag 猜 source。

`SourceObject` 是 runtime source context，不是永久 ItemId。Load/respawn/transform 后从 persistent Equipment/Inventory truth 重建 grant mapping。

### 验收

- 左右同类 GA；
- 只卸一把；
- 左右换槽；
- Drop 右手；
- death/respawn；
- NPC transform；
- JIP；
- old source callback late arrival。

另一把武器的能力不能被误删。

## 3. 五段连招不是一个永不失效的 PredictionKey

当前多刀刃参考已经要求跟踪 Section、Sequence、HitWindow。现在再加 GAS prediction boundary。

### 3.1 每个异步边界都重新审计

例如：

```text
Activate Section 1
→ Montage event
→ input buffer wait
→ Section 2
→ hit window notify
→ async trace / damage request
→ Section 3 ...
```

首段 Activation PredictionKey 不能自动跨越所有 latent callback。

每个边界记录：

```text
Client/Server
SpecHandle
ActivationKey
Current ScopedKey validity
Combo Sequence
Section
HitWindow generation
Timestamp
```

### 3.2 后续段的两种合法策略

**A. 真预测**

目标 UE 版本的 GAS 正式机制建立新 Scoped Prediction Window / sync point，然后预测允许的副作用。

**B. Authority continuation**

服务器继续伤害/Cost/窗口业务，客户端只预测 Montage、trail、camera、轻量 movement presentation。

不能复用 stale PredictionKey 假装仍在第一段 prediction scope。

## 4. 客户端结束不等于服务器结束

高延迟下：

```text
client montage section ended
server still processing accepted sequence/window
```

这是正常可能性。

服务器业务生命周期不能默认由 client natural end/cancel 强制终止。

检查：

- NetExecutionPolicy；
- current UE NetSecurity/termination policy；
- 项目自定义 cancel request；
- AbilityTask cancel path；
- Montage stop path。

客户端可以立即停止自己的 preview，但 Authority 是否终止由服务器规则决定。

### 4.1 对 LGF-26 的补充

`SubmittedToServer` 仍然不等于 Accepted。

现在日志进一步加：

```text
ActivationKey
ScopedKey
ServerAbilityActive
TerminationReason
AuthorityWindowGeneration
```

这样可以区分：

- 请求晚到；
- sequence 过期；
- prediction window 已失效；
- client 提前结束触发 remote termination；
- server 自己因 ActionLock/Target invalid 拒绝。

## 5. TargetData 适合“与这次激活绑定的数据”

对于 lock-on、Traversal、近战 trace，可选：

```text
GameplayEvent / TargetData / LGF current request payload
```

只要它们能与本次 activation identity 绑定。

不推荐：

```text
Client set replicated CurrentTarget
Client immediately ActivateAbility
```

服务器可能先收到 Ability 请求，再看到旧 `CurrentTarget`。

### 5.1 TargetData 不等于可信 Hit

客户端可以算：

- target candidate；
- aim sample；
- ledge；
- HitResult；
- preferred montage/action。

Authority 仍检查：

```text
request owner
Item / source
Avatar generation
Ability/Sequence/Window
range / LOS / facing
collision / trace
team / alive / invulnerable
traversal geometry
warp envelope
moving primitive
```

对于高风险动作，可以让客户端只发 confirm/seed/candidate，服务器重新 trace。

## 6. TargetData race 与 consume-once

多人环境存在：

```text
TargetData arrived before AbilityTask registered listener
```

不能因此丢一枪/丢一段。

LGF 适配时确保当前 GAS/request layer 有：

- activation-keyed listener；
- register 后检查 already-arrived payload；
- consume-once；
- cancel/end cleanup；
- duplicate/replay rejection；
- stale Avatar/Sequence rejection。

如果 LGF 当前没有抽象，不为“复刻 GASShooter”新增 Actor 型 targeter；优先做与现有 Request/GAS 风格一致的轻量 task/service。

## 7. 多刀刃命中与 GAS TargetData 的边界

HitWindow/TraceSourceBinding 仍是 LGF authoritative trace contract。

TargetData 可以表示：

- client-local target suggestion；
- aim / lock candidate；
- confirmed input timing；
- sampled visual hit 用于 correction。

不要用客户端 TargetData 取代现有 Authority blade trace，除非玩法明确改为 client-shot model 且服务器有完整 envelope validation。

左右刀独立伤害仍使用：

```text
TraceConfig identity
+ HitWindow generation
+ Target identity
```

PredictionKey 不能替代 HitWindow identity。

## 8. Reusable Targeter 与 LGF Trace Service

GASShooter 复用 TargetActor 的价值是减少自动武器每枪 spawn/GC。但 LGF 不需要复制 TargetActor 类层级。

如果要复用 LGF trace worker/query：

必须 reset：

- Avatar / Item / PartId；
- Ability activation；
- Sequence / HitWindow；
- sockets / collision profile；
- previous hit set；
- target filter；
- generation；
- callbacks。

Damage callback 可同步 cancel/switch section，因此回调后重新检查 run generation，和现有多刀刃参考一致。

## 9. Ability RPC batching：只在证据证明值得时

如果 LGF 存在同一帧：

```text
Activate
→ immediate TargetData
→ End
```

可以研究当前 UE GAS 的 RPC batching。

但：

- 不改变 Authority revalidation；
- 不改变 Sequence/HitWindow；
- 不改变 idempotency；
- 不改变 damage transaction；
- 不为了 batching 把五段 combo 挤进一帧。

先用 Unreal Insights / network profile 证明 RPC 数量是瓶颈，再实现目标版本的 API。

## 10. 装备数值：什么进 GAS，什么留 Inventory

LGF 已有 Inventory/Equipment runtime data，不要每把武器都挂独立 ASC。

### 角色/共享 GAS Attribute

- Health；
- Stamina/Mana；
- 共享资源；
- 需要 GE/MMC/ExecCalc/capture 的战斗属性。

### Item runtime state

- durability；
- blade condition；
- clip ammo；
- heat；
- charges；
- affix rolled value。

Ability 通过 SourceObject/ItemId/Equipment context 访问。

如果未来确实动态增删 AttributeSet，必须把 replicated teardown race 写进设计；不能在 owner UI 一卸装就让客户端提前删除 Set。

## 11. 多 Mesh / Linked Layer prediction reject

LGF 当前不是 GASShooter 的 1P/3P fork，但同样有：

- main character Mesh；
- source/hidden skeleton；
- VisibleMesh / retarget；
- weapon parts；
- Linked Anim Layer；
- future transform avatar / mount presentation。

预测播放 identity 使用：

```text
Activation identity
+ AvatarGeneration
+ Mesh 与 Layer identity
+ MontageInstance identity
```

### Reject / Cancel

服务器拒绝本次 Ability 时：

- stop 这次 activation 的 main montage preview；
- unlink/rollback 这次 overlay/layer；
- stop weapon/part cosmetic action；
- close local HitWindow preview；
- cancel Mover movement preview/warp；
- clear notify/task delegates；
- leave later/new Avatar same-name montage untouched。

不能只 `Montage_Stop(Asset)`。

## 12. EffectContext 与伤害 provenance

LGF damage execution 可以使用 EffectContext 保存一次伤害的来源信息，但保持短小：

```text
Source Item/Part identity (runtime/stable id as appropriate)
Hit/TargetData summary
Damage action id
surface / impact metadata
```

不要把 Inventory entry、整套 Equipment snapshot 或长期状态塞进去。

EffectContext 是 execution provenance，不是第二份装备数据库。

## 13. GameplayCue：丢了可以难看，不能少扣/多扣血

多刀刃同时产生大量：

- trail；
- sparks；
- hit impact；
- sound；
- camera/UI feedback。

这些 cosmetic event 与 Authority DamageId 分离。

如果带宽高：

- 同一 action 批 cosmetic event；
- 用 seed / compact positions；
- 远端只重建必要表现；
- owner 可以更丰富。

不把每个 trace sample 都做一个网络 Cue。

## 14. Avatar 变身/骑乘与 ASC

LGF 的长期 ASC/Inventory truth 不跟形态走。

切 Avatar：

```text
Old avatar generation invalid
→ cancel/unbind old AbilityTasks / TargetData listeners
→ rollback old predicted montage/layers/movement
→ detach presentation
→ InitAbilityActorInfo(stable owner, new avatar)
→ bind new avatar gameplay/presentation
→ rebuild equipment grant/presentation mapping
```

旧 Avatar 的 TargetData、reject 与 Montage end 回调晚到时直接丢弃。

## 15. 不照搬 GASShooter 的内容

明确拒绝直接迁移：

- UE4 InputID 为核心的输入系统；
- 每把枪的老 TargetActor Actor hierarchy；
- 整套自定义 multi-mesh ASC montage fork；
- 构造函数 `StaticLoadClass` 资产路径；
- hardcoded `RequestGameplayTag()` 热路径；
- firing tag 下简单关闭 replication 但无 correction generation；
- 老 `Role` 与 RPC validation 写法；
- 认为 README/demo 跑通即代表 UE5.7 GAS 兼容。

## 16. LGF 网络验收矩阵

### Ability

- Accepted / Rejected；
- local cancel / server cancel；
- cost fail；
- cooldown fail；
- client natural montage end first；
- server ability end first。

### Combo

- 1～N sections；
- high RTT；
- input at open/middle/close edge；
- duplicate input；
- stale sequence；
- dual blade same target；
- one blade miss / other hit。

### Avatar / Equipment

- swap weapon during predicted ability；
- remove only one same-class grant source；
- death/respawn；
- transform NPC；
- mount/unmount；
- JIP。

### Diagnostics

每条 request 至少可关联：

```text
Player/ASC owner
AvatarGeneration
ItemId / PartId
SpecHandle / Source
ActivationKey / ScopedKey
Sequence / Section / HitWindow
TargetData id
Authority result / reject reason
Montage mesh/layer instance
```

这样才能把“动画看着错”“技能只打一段”“右刀误伤”追到同一数据链上。
