# GASDocumentation + GASShooter 源码蒸馏

> 第七轮外部 UE 项目研究。目的不是复制旧 GAS 样例，而是把 Prediction、TargetData、AbilityTask、Owner/Avatar、装备 Ability grant、RPC batching、多 Mesh Montage 和高延迟取消语义提炼到 SkillForge，并映射到当前 LGameplayFramework（LGF）生产路线。

## 0. 快照、许可与证据等级

### GASDocumentation

- 仓库：`tranek/GASDocumentation`
- 固定内容快照：`8f76c5780bdea69e0ea2cc161ab2f435f04182eb`
- 许可：MIT
- 文档定位：社区 GAS 经验文档 + 示例工程，不是 Epic 官方规范
- 文档时代：README 自述示例已更新到 UE 5.3
- 当前研究日期：2026-09-14

### GASShooter

- 仓库：`tranek/GASShooter`
- 固定内容快照：`26295c548a19f221917e4a7232c12e763db64cb1`
- 许可：MIT
- 定位：Advanced FPS/TPS GameplayAbilitySystem sample
- 代码时代：主要实现来自 UE4-era；固定快照远早于当前 UE5.7/5.8

### 证据原则

本轮将来源分为三层：

1. **机制证据**：GASDocumentation 对 PredictionKey、TargetData、AbilityTask、ASC Owner/Avatar 等概念的解释；
2. **工程实现证据**：GASShooter 对武器、TargetActor、RPC batching、多 Mesh Montage 的具体实现；
3. **当前项目决策**：只在与 LGF UE5.7/实际工程源码一致或可重新验证时写成正式 Skill。

旧类名、内部函数、RPC、InputID、TargetActor API 不能因为在 GASShooter 出现就写成 2026 的 GAS 标准答案。

---

# 1. 为什么这一轮要成对研究

只读 GASDocumentation 会得到机制说明，但看不到大型武器系统如何把这些机制组合起来；只读 GASShooter 则容易把 2021 的 UE4 API 误当现行最佳实践。

本轮分工：

```text
GASDocumentation
  ├─ GAS 概念/限制
  ├─ PredictionKey / window
  ├─ TargetData
  ├─ NetSecurityPolicy
  ├─ AbilityTask
  └─ AttributeSet / Cue / EffectContext

GASShooter
  ├─ PlayerState ASC
  ├─ Weapon SourceObject / SpecHandle
  ├─ reusable TargetActor
  ├─ TargetData consume / race handling
  ├─ Ability RPC batching
  ├─ 1P/3P multi-mesh montage
  └─ predicted weapon ammo / presentation
```

最终进入 LGF 的不是这两个项目的类结构，而是它们共同证明的生产合同。

---

# 2. ASC OwnerActor / AvatarActor：长期身份与临时身体

## 2.1 文档模型

GASDocumentation 区分：

- `OwnerActor`：ASC 的拥有者；
- `AvatarActor`：ASC 当前代表的物理 Actor。

玩家可以使用：

```text
PlayerState = OwnerActor
Character/Pawn = AvatarActor
```

这样角色死亡/重生后，ASC、Attributes、持续 GameplayEffects 可以继续留在稳定 PlayerState。

## 2.2 GASShooter 实证

`GSPlayerState.cpp`：

- 创建 replicated `UGSAbilitySystemComponent`；
- Mixed replication mode；
- 创建角色 AttributeSet 和 Ammo AttributeSet；
- PlayerState 作为长期 ASC 宿主。

`GSHeroCharacter.cpp` 的 `PossessedBy()`：

```text
AbilitySystemComponent = PlayerState.ASC
InitAbilityActorInfo(PlayerState, HeroCharacter)
```

客户端则通过 PlayerState replication 对应路径初始化。

## 2.3 对 LGF 的意义

这与前面 AyaDog 轮次得出的 stable player truth / replaceable Avatar 一致，并且进一步补强 GAS 本身的理由。

对用户未来功能：

- 吸收任意 NPC；
- 变成场景 Prop；
- 骑乘不同宠物/NPC；
- death/respawn；

都不需要为每个形态创建独立长期 ASC。

推荐：

```text
Stable player identity / PlayerState-side domain
  └─ persistent ASC state
        ↓ InitAbilityActorInfo
Current Avatar generation
  ├─ Pawn + Mover
  ├─ Mesh / AnimInstance
  ├─ PhysicsControl
  ├─ GameplayCamera
  └─ equipment presentation
```

## 2.4 不直接照搬的旧建议

GASShooter 把 PlayerState `NetUpdateFrequency` 设置为 100，用来解决旧版本 PlayerState 默认更新率低导致的 GAS 延迟。

这只能作为历史症状证据，不能写成 UE5.7/5.8 的固定配置：

- 当前 Replication Graph / Iris / Adaptive update 策略可能不同；
- 项目实际 PlayerState 数据量不同；
- 100 Hz 可能浪费带宽。

当前 Skill 只保留：**如果 ASC 放 PlayerState，要实际测 Attribute/Tag/Ability state latency，并针对当前 replication architecture 调优。**

---

# 3. AbilitySpec SourceObject：能力来源身份

## 3.1 GASShooter 的武器授予

`GSWeapon::AddAbilities()`：

- 仅 Authority grant；
- `GiveAbility()` 创建 spec；
- SourceObject 是实际 `this` 武器实例；
- 保存返回的 `AbilitySpecHandle`。

`RemoveAbilities()`：

- Authority only；
- 遍历保存的 handle；
- `ClearAbility(handle)`。

这是一个非常清晰的来源级生命周期：

```text
Weapon instance
  ├─ SourceObject
  └─ exact SpecHandles
```

## 3.2 同 AbilityClass 多来源

这正好对应用户 Codex 刚新增的双刀项目现实：

```text
Left Sword  -> GA_MeleeCombo
Right Sword -> GA_MeleeCombo
```

AbilityClass 一样，不代表是同一 grant。

如果卸右刀时做：

```text
Clear all GA_MeleeCombo
```

左刀也会被误删。

应当：

```text
Right ItemId
→ right runtime grant source
→ right SpecHandle
→ clear right only
```

## 3.3 SourceObject 不是永久身份

GASDocumentation 的更新记录还说明 `FGameplayAbilitySpec::SourceObject` 被改成了弱引用语义。

因此不能把 SourceObject 当：

- SaveGame ItemId；
- 跨服务器业务 ID；
- 可靠永久指针。

应该分层：

```text
Persistent ItemId
↓ runtime rebuild
Equipment Entry / Weapon runtime object
↓
Spec.SourceObject + SpecHandle
```

## 3.4 Character ability removal 的额外证据

`GSCharacterBase::RemoveCharacterAbilities()` 使用：

- `Spec.SourceObject == this`；
- AbilityClass 在 startup list；
- 先收集 handle；
- 第二遍清除。

这里可以吸收“**来源过滤 + 不在迭代中直接 mutation**”原则。

但 LGF 已有 GrantedHandles 体系时，精确保存 handle 优于运行时再扫描 class/list。

---

# 4. PredictionKey：不是整个 Ability 生命周期的许可证

## 4.1 Activation Prediction Window

GASDocumentation 描述 LocalPredicted ability 的基本顺序：

```text
Client TryActivateAbility
→ generate PredictionKey
→ send server activation request
→ client predicts ability
→ server accepts/rejects
→ replicated key/effects reconcile
```

PredictionKey 的核心用途是把：

- 客户端预测 GameplayEffect；
- GameplayCue；
- 其他预测 side effect；

与服务器确认结果对应起来。

## 4.2 Prediction window 是有限范围

文档明确指出：Activation PredictionKey 只在一个原子 grouping/window 内有效。

最常见误解：

```text
Ability 是 LocalPredicted
=> 整个 Ability 从开始到结束都在同一个合法 prediction window
```

错误。

例如：

```text
Activate
→ WaitDelay
→ Montage notify
→ Section transition
→ input buffer
→ async trace callback
```

进入这些 latent 边界后，原 activation key 通常已不再是“valid for more prediction”。

## 4.3 新 Scoped Prediction Window

旧文档描述 `WaitNetSync` / `FScopedPredictionWindow` 等机制来创建新的 prediction scope。

本轮不把旧 API 名称直接升级为 LGF 生产规定。

保留的是语义：

> 每个 latent/asynchronous continuation 如果要继续预测，必须证明当前引擎提供了新的合法 prediction/sync identity；否则后续业务由 Authority 执行，客户端只预测 presentation。

## 4.4 对双刀五段连招的直接影响

Codex 新增 LGF-26 已经发现：高延迟 Submit 后只打一段。

本轮增加一个新排查维度：

```text
Section 1 ActivationKey
Section 2 current ScopedKey
Section 3 current ScopedKey
...
```

不能只记录：

```text
Ability Activate success
RPC Submitted
```

需要进一步区分：

- client current key valid？
- server current ability still active？
- client natural end 是否影响 server？
- target/hit request 属于哪个 window？

---

# 5. Remote cancel / termination：高延迟能力的隐藏坑

GASDocumentation 对 `Server Respects Remote Ability Cancellation` 的评价非常明确：它可能让客户端提前结束服务器版本的能力，尤其是高延迟 LocalPredicted ability。

这对长 combo 很重要。

场景：

```text
Client montage section finished
Client considers local ability complete
↓ latency
Server still owns accepted HitWindow / sequence
```

如果设置/策略允许 client end 直接 force server end，服务器可能提前丢掉后续 section。

## 5.1 两个独立维度

- **NetExecutionPolicy**：能力在哪里执行；
- **NetSecurity/Termination policy**：客户端是否有权让服务器执行/终止。

ServerOnly execution 也不自动等于 ServerOnly termination。

## 5.2 LGF 应用

不可逆业务：

- damage；
- inventory mutation；
- traversal movement commit；
- equip transaction；

都必须让 Authority 自己决定最终 end。

客户端 natural montage end 可以：

- 停本地 preview；
- 发 cancel request；

但不能默认直接结束 Authority truth。

---

# 6. TargetData：原子请求载荷

## 6.1 TargetData 适合什么

GASDocumentation 把 `FGameplayAbilityTargetData` 定义成跨网络传递 targeting data 的多态结构。

适合：

- Actor/Object refs；
- HitResults；
- aim origin/direction；
- location；
- custom compact data。

## 6.2 为什么优于“set replicated field then activate”

文档明确提醒：

```text
set replicated variable
immediately activate ability
```

不能保证接收端先看到变量，再看到 ability activation。

所以如果某数据必须属于某次 Ability activation，最好与这次 request/Event/TargetData 一起发送，而不是依赖两条独立 replication path 的到达顺序。

## 6.3 对 LGF 的用途

可以用于：

- lock-on candidate；
- traversal sample；
- aim sample；
- melee client suggestion；
- action input timing。

但 LGF 的 Authority trace/damage contract 不因为 TargetData 存在就消失。

---

# 7. TargetData 是网络数据，不是服务器授权

## 7.1 GASShooter 的重要实现

`UGSAT_WaitTargetDataUsingActor::OnTargetDataReplicatedCallback()`：

- Consume client replicated data；
- 调 TargetActor 的 `OnReplicatedTargetDataReceived()`；
- 该函数可以 sanitize/verify；
- 返回 false 就 reject / cancel；
- 注释明确说服务器甚至可以重新 trace，只把客户端包当 confirm。

这是本轮最重要的生产机制之一。

## 7.2 Authority envelope

LGF 应按动作重验：

### melee

- source Item / Part；
- current HitWindow；
- combo Sequence；
- target alive/team；
- socket/trace geometry；
- distance / LOS；
- dedup generation。

### traversal

- ledge still exists；
- range/facing；
- slope；
- clearance；
- target primitive velocity；
- accepted action/montage set；
- moving base identity。

### lock-on

- target valid；
- LOS/range；
- target not stale；
- current lock policy。

## 7.3 客户端可以少发

GASShooter 注释还提供了一个带宽思路：客户端不一定发送完整 trace result，可以只发 confirm，由 server TargetActor 自己算。

现代 LGF 可以改成：

```text
client candidate/seed/confirm
→ Authority service re-query
→ accepted compact result
```

不需要复刻 Actor TargetActor。

---

# 8. TargetData race：数据可能比 listener 先到

GASShooter remote server 侧：

1. 注册 `AbilityTargetDataSetDelegate`；
2. 注册 cancelled delegate；
3. 调“如果 data 已经到了就立即触发”的检查；
4. 标记 waiting remote data。

这是典型 network race 处理：

```text
Data first, listener later
Listener first, data later
```

两种都必须工作。

## 8.1 Consume once

数据处理后必须从 ASC 的 replicated TargetData cache 消费掉。

否则：

- 下一 activation 可能读旧数据；
- retry 可能重复伤害；
- reused TargetActor 可能串请求。

## 8.2 identity

至少按：

```text
SpecHandle
+ ActivationPredictionKey / current activation identity
```

当前 LGF 还需要叠加：

```text
AvatarGeneration
Combo Sequence
HitWindow generation
Item/Part source
```

---

# 9. AbilityTask：真正的异步资源所有者

GASDocumentation 的 Custom AbilityTask 模式和 GASShooter TargetData task 都说明：AbilityTask 不只是 latent UI node。

它通常管理：

- Ability/ASC context；
- delegate；
- replicated event listener；
- target object；
- prediction scope；
- completion/cancel lifecycle。

## 9.1 cleanup order

GAS changelog 特别提到：`Super::OnDestroy` 可能会把 Ability pointer 清空，所以 task 自己需要访问的东西要先清理。

推荐：

```text
stop external source
→ unbind target/delegates
→ consume/clear waiting network data
→ invalidate task generation
→ Super::OnDestroy
```

## 9.2 late callback

即使 delegate 已解除，已经排队的 callback/async result 仍可能晚到。

回调入口重新验证：

- task still active；
- Ability still same activation；
- Avatar generation；
- source Item；
- current Sequence/Window。

---

# 10. Reusable TargetActor：优化的本质是 reset contract

GASShooter 每把 Weapon 缓存 LineTrace / SphereTrace TargetActor，并在 EndPlay Destroy。

好处：

- 自动枪不每发 Spawn Actor；
- 减少 GC；
- 可以复用 trace config。

风险：

- previous hit/filter 泄漏；
- old delegates；
- old Ability/ASC；
- old PredictionKey；
- old confirm/cancel binding。

因此可迁移规则不是：

> 所有 LGF trace 都做 TargetActor pool。

而是：

> 若复用昂贵 targeting object，必须定义完整 reset contract。

对于 LGF 的服务器 melee trace，现有 component/service 体系如果已经轻量，就没有理由新增 Actor hierarchy。

---

# 11. Ability RPC batching：网络优化，不是业务事务

GASDocumentation/GASShooter 展示：同一帧内可以把：

```text
Activate
TargetData
End
```

合并成更少的 client->server RPC。

## 11.1 最适合 hitscan instant ability

Semi-auto 一枪：

```text
activate
trace
send target
end
```

最容易形成原子 batch。

Full-auto 只有第一发能明显节省更多，因为后续 TargetData 仍是独立事件。

## 11.2 不要混成 business transaction

Batching 不提供：

- permission；
- validation；
- anti-replay；
- rollback；
- transaction commit；
- idempotency。

TargetData 在 batch 内仍然是不可信客户端数据。

## 11.3 对 melee combo

五段连招如果横跨数百毫秒甚至数秒，不能为了 batching 强改成一个“一帧能力”。

只对真正同一 prediction scope 的短操作考虑 batching。

---

# 12. Weapon local state：不必 AttributeSet-per-item

GASDocumentation 给出三个 item attribute 方案：

1. plain values on item；
2. AttributeSet on item；
3. ASC on item。

它明确推荐 gun ammo 这类 item-local 值放 item 本身。

## 12.1 GASShooter 实现

Weapon：

- PrimaryClipAmmo；
- Max clip；
- Secondary clip；
- owner-only replication。

Shared reserve ammo 则放玩家 Ammo AttributeSet。

这符合语义：

```text
weapon instance local clip state
vs
player shared combat resource
```

## 12.2 对 LGF

延续 RockInventory/Obsidian 成本阶梯：

```text
Item Definition
→ compact runtime state
→ optional typed state/UObject
→ GAS only where GE aggregation semantics are needed
```

耐久、heat、charge、clip ammo 通常没有必要成为独立 AttributeSet。

---

# 13. Dynamic AttributeSet removal race

GASDocumentation 特别警告 runtime remove AttributeSet：

```text
client removes set first
server replicated attribute delta arrives later
client cannot find set
→ crash / invalid state
```

这是一个重要的生命周期反例。

## 13.1 生产要求

如果必须 dynamic set：

- Authority owns removal；
- 停止引用该 set 的 Ability/Effect；
- 定义 replication fence / grace period / ack；
- JIP 明确 final membership；
- client UI 隐藏不等于立即销毁 replicated set。

## 13.2 更简单的方案

对于不需要 GAS aggregate 的 item-local state，根本不要动态 AttributeSet。

---

# 14. Weapon ammo prediction 的历史技巧与限制

GASShooter 在 firing tag 活跃时，用 `PreReplication()` 临时禁止 clip ammo replication，避免 server 旧 snapshot 覆盖 client predicted ammo。

这证明：

> 单独 replicated property 与 prediction 有时需要主动避免回写 clobber。

但不能把它提升成通用方案。

缺失的生产问题包括：

- 何时重新开启 replication；
- server correction；
- 丢包；
- 切枪；
- drop；
- reload；
- generation；
- reject prediction。

所以 Skill 只记录“manual item-state prediction must define correction contract”。

---

# 15. EffectContext：一次执行的 provenance

GASDocumentation 说明可 subclass `FGameplayEffectContext` 并加入 TargetData。

需要：

- GetScriptStruct；
- Duplicate；
- NetSerialize；
- StructOps traits；
- AbilitySystemGlobals allocator。

GASShooter shotgun 用它传 multiple target data 给 GameplayCue。

## 15.1 适合内容

- instigator；
- source Item/Part；
- hit sample；
- surface；
- Damage action id；
- compact TargetData。

## 15.2 不适合

- Inventory snapshot；
- Equipment database；
- Save data；
- 大型永久 runtime state。

EffectContext 是 execution context，不是第二个背包系统。

---

# 16. GameplayCue：业务与表现分离

GASDocumentation 描述：大量 GameplayCue 可以 batching/自定义 compact RPC。

Shotgun 8 pellet 如果每个 impact 各发一套 cue，带宽很快放大。

## 16.1 对双刀/ARPG

可能出现：

- left trail；
- right trail；
- hit spark；
- surface effect；
- damage number；
- hit sound。

Authority 只需要保证：

```text
DamageId / accepted hits / state
```

表现可以：

- compact impact array；
- random seed；
- local reconstruction；
- owner rich / remote reduced detail。

丢一个 cosmetic cue 不能造成少扣血或多扣血。

---

# 17. 多 Mesh Montage：identity 不是 Montage asset

GASShooter 的 ASC 为 1P/3P skeletal meshes 扩展了 Montage replication。

本轮不迁移它的 fork，但吸收一个非常重要的 identity：

```text
Ability activation/prediction
+ Mesh
+ Montage instance
```

LGF/GASP 再加：

```text
AvatarGeneration
+ Linked Layer / Part
```

## 17.1 predicted reject

GASShooter 对 predicted montage 注册 rejection delegate。

这证明：

> client predicted montage 必须有 server reject rollback。

LGF 多层表现不能只停主 Mesh：

- main avatar montage；
- Linked layer；
- weapon layer；
- first-person/alternate mesh（若未来增加）；
- movement preview；
- trail/cue。

但 rollback 必须精确属于旧 activation，不能停掉新 Avatar 后来播放的同名 montage。

---

# 18. SimulatedProxy 不运行完整业务 Ability

GASDocumentation 强调 GameplayAbilities 通常不在 SimulatedProxy 上作为业务逻辑运行。

SimProxy 看到的是：

- replicated state；
- tags；
- cues；
- montage/presentation。

这对 LGF 很重要：

不要为了“所有端表现一致”让 SimProxy 自己执行 damage/trace truth。

表现一致性通过 presentation replication 解决，不是通过复制 Authority logic。

---

# 19. Mixed replication mode：可见性，不是 Authority

GASShooter PlayerState 使用 Mixed mode：

- owning client 获得完整 active GE；
- simulated clients 主要看到 tags/cues 等。

这是一种带宽/隐私/需求策略。

它不改变：

- server Authority；
- damage ownership；
- request validation。

LGF 不应为了 UI 要看一个 buff 信息就轻易改成 Full replication。

---

# 20. 旧 API / 现代 UE 迁移边界

## 20.1 明确属于历史实现的内容

- InputID-centric GAS input；
- UE4 Role 写法；
- TargetActor-heavy targeting；
- old RPC validation style；
- old multi-mesh ASC fork；
- `FScopedServerAbilityRPCBatcher` 的具体签名；
- UE5.3 `InitGlobalData()` 说明已注明 5.3 开始自动调用。

## 20.2 现代 LGF 应重新验证

- Enhanced Input + InputTag routing；
- GAS current replicated events；
- ScopedPredictionKey APIs；
- AbilityTask teardown internals；
- registered subobject / Iris；
- current Montage replication behavior；
- Mover + GAS movement ability bridge；
- GameplayCamera / GASP presentation。

---

# 21. 与已有 SkillForge 轮次的合并关系

## ActionRoguelike

已有规则：client candidate != Authority authorization。

GAS 本轮把它具体化到 TargetData：serialized target != trusted target。

## Obsidian / AyaDog

已有规则：equipment grants 保存 GrantedHandles。

GASShooter SourceObject + SpecHandle 提供另一条独立证据，强化“同 AbilityClass 多 source 精确撤销”。

## RockInventory

已有规则：item-local runtime state 分层，避免 UObject/复杂系统滥用。

GASDocumentation 的 weapon ammo plain fields 再次证明“不需要每个 item 一个 AttributeSet/ASC”。

## GASP-ALS-R / ALS-Refactored

已有规则：animation/movement truth 分域，预测 presentation 有 rollback identity。

GASShooter multi-mesh montage reject 把 GAS prediction rollback 补到 Mesh/Layer 维度。

## Codex 最新 LGF 双刀

Codex 已加入：

- PartId；
- TraceSourceBinding；
- HitWindow identity；
- Sequence；
- server/client timing logs；
- real GAS damage fixtures。

本轮不替换这些规则，只补：

- Prediction window；
- SourceObject/SpecHandle；
- TargetData consume/revalidate；
- remote cancel；
- multi-layer reject rollback。

---

# 22. 对用户实际多刀项目的建议模型

```text
Inventory ItemId
   ↓
Equipment Entry
   ├─ PartId: Primary
   ├─ PartId: OffHand
   └─ Grant Source Context
          ↓ Authority grant
      SpecHandle(s)
          ↓ activation
   Activation Identity / PredictionKey
          ↓
   Combo Sequence / Section
          ↓
   HitWindow Generation
          ↓
   TraceSourceBinding
          ↓
   Authority accepted Hit / DamageId
          ↓
   Cosmetic Cue / Montage / Layer
```

每一层都有自己的 identity，不用一个 GameplayTag 或 MontageName 全部代替。

---

# 23. 多段 Combo 的推荐时序

## Client

```text
input
→ local CanActivate
→ predict presentation
→ send activation/request identity
→ buffer next input
→ if latent boundary needs prediction: establish valid scoped window
→ submit sequence/target candidate
→ await accept/reject
```

## Authority

```text
activation request
→ validate ability/source/avatar
→ accept activation
→ own combo sequence
→ own hit-window generation
→ receive target/input request
→ validate identity + timing + target envelope
→ apply damage/effect
→ replicate accepted state/result
```

## Client correction

```text
server accept
→ reconcile predicted presentation

server reject
→ rollback exact activation generation
→ stop old montage/layer/movement preview
→ never stop later/new activation
```

---

# 24. TargetData for melee：三种设计强度

### A. Server trace authoritative

client 只提交：

```text
input timing / candidate id
```

server trace。

安全最强，延迟感更明显。

### B. Client sample + server envelope

client 提交 compact trace sample；server 检查范围/geometry/target/sequence。

适合动作游戏折中。

### C. Client hit authoritative

不推荐默认用于 PvP/经济真值，除非项目明确接受作弊面并有 server analytics/anti-cheat。

LGF 默认应使用 A/B，而不是 C。

---

# 25. AbilityTask generation pattern

建议项目自己的 task/request 都带 generation：

```cpp
struct FCombatActivationIdentity
{
    ItemId;
    AvatarGeneration;
    SpecHandle;
    ActivationKey;
    ComboSequence;
    HitWindowGeneration;
};
```

实际类型按项目现有结构设计，不必创建这个具体 struct。

任何 callback：

1. resolve current owner；
2. compare identity；
3. if stale -> return；
4. perform mutation；
5. callback 后若可能重入，再验证一次。

---

# 26. 服务器拒绝原因要结构化

不要只输出：

```text
Ability failed
Target invalid
```

至少区分：

- stale avatar；
- stale spec/source；
- sequence mismatch；
- hit-window closed；
- target range；
- LOS；
- team/friendly；
- action locked；
- cost/cooldown；
- prediction/termination mismatch；
- replay/duplicate TargetData。

这样才能把 Codex 的高延迟“只打一段”问题从日志变成可验证状态机。

---

# 27. 性能方向

## 27.1 可优化

- reusable expensive targeting object；
- RPC batching for truly atomic hit-scan-style ability；
- compact TargetData；
- GameplayCue batching/local reconstruction；
- tag/spec lookup index；
- item local compact value state。

## 27.2 不要提前优化

- 每个 melee sample 都建复杂 pool；
- 为 batch 改 Ability 生命周期；
- 为避免 AttributeSet race 建第二 ASC；
- 为多 Mesh presentation fork 整个 ASC；
- 每 Tick构造 GameplayTag/TargetData heavy container。

所有优化先 profile。

---

# 28. 安全方向

NetSecurityPolicy 是 GAS 提供的一层保护，但不能代替业务 validation。

即使 Ability 本身只能服务器执行，也仍要验证：

- request actor ownership；
- target；
- item；
- cost；
- rate；
- replay；
- sequence。

反过来，即使 LocalPredicted 能力允许 client execution，也不能让它决定 server damage truth。

---

# 29. 最终迁移决策表

| 外部机制 | SkillForge 决策 |
|---|---|
| PlayerState ASC Owner | 保留稳定 Owner / replaceable Avatar 语义 |
| PlayerState 100 Hz | 不保留固定值；当前网络实测 |
| SourceObject weapon | 保留 runtime source identity |
| exact SpecHandle revoke | 强保留 |
| PredictionKey window | 强保留 |
| old WaitNetSync exact recipe | 只保留语义，当前版本重查 |
| TargetData | 保留为 activation-bound compact request |
| client TargetData trusted | 拒绝 |
| reusable TargetActor | 保留 reset contract，不迁 Actor 架构 |
| Ability RPC batching | 保留 profile-based transport optimization |
| per-item plain state | 保留，与现有 item-state ladder 合并 |
| dynamic AttributeSet removal | 标为高风险 replication lifecycle |
| EffectContext custom data | 保留 minimal provenance |
| every pellet independent Cue | 拒绝，先做 bandwidth design |
| custom 1P/3P ASC montage fork | 不迁；吸收 prediction rollback identity |
| firing 时停 ammo replication | 不作为通用方案；要求 correction contract |

---

# 30. 新增 SkillForge 行为样本

UE C++：

- `CPP-36` GAS Owner/Avatar/Source lifecycle；
- `CPP-37` Prediction window across latent continuation；
- `CPP-38` TargetData consume/validate/race；
- `CPP-39` AbilityTask reusable targeter cleanup；
- `CPP-40` RPC batching != business transaction；
- `CPP-41` item-local state vs dynamic AttributeSet；
- `CPP-42` EffectContext/Cue bandwidth separation。

LGF：

- `LGF-28` multi-section prediction window + server end authority；
- `LGF-29` dual weapon SourceObject/SpecHandle isolation；
- `LGF-30` client TargetData authority retrace + ordering；
- `LGF-31` predicted montage multi-layer rejection rollback。

这些新用例与 Codex 新增 `LGF-25..27` 共存。

---

# 31. 本轮没有验证什么

没有声称：

- GASShooter 可在 UE5.7/5.8 编译；
- 旧 TargetActor API 是现代最佳实践；
- old RPC batching API 当前签名仍一致；
- LGF 当前项目已经实现这些新合同；
- UE PIE/Dedicated/high-latency 已跑；
- GASShooter 的手动 ammo prediction 是无误的生产模板。

本轮结果是：**固定源码研究 + Skill 行为合同 + 文本/结构验证**。

---

# 32. 后续可继续研究的 GAS 来源

如果继续 GAS 方向，优先级：

1. 当前 UE5.7/5.8 `GameplayAbilities` engine source：确认 Prediction/AbilityTask/TargetData 现行 API；
2. Lyra：AbilitySet、InputTag、HeroComponent、Experience/GameFeature 与现代 GAS；
3. Epic ActionRPG 历史样例：GameplayEffectContainer 思路，只取机制；
4. modern GAS sample / engine tests：Iris、registered subobject、prediction regression。

但下一轮不应继续堆旧 GAS 文档，应该换到现代 UE 项目或直接用用户实际 LGF 工程验证这些合同。
