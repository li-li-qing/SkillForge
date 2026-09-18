# GAS 预测、TargetData 与能力生命周期生产模式

适用于 UE C++ 中的 Gameplay Ability System 联网能力，尤其是 LocalPredicted 技能、多段连招、TargetData、自定义 AbilityTask、装备授予、预测 Montage、GameplayCue 和高延迟取消问题。

本文只保留跨项目可迁移的合同。具体 API、宏和内部容器名称必须以消费工程实际 Unreal Engine 版本为准。外部依据主要来自：

- `tranek/GASDocumentation@8f76c5780bdea69e0ea2cc161ab2f435f04182eb`：社区 GAS 经验文档，标注 UE 5.3；
- `tranek/GASShooter@26295c548a19f221917e4a7232c12e763db64cb1`：UE4 时代高级多人样例，用来观察复杂武器、TargetData、AbilityTask、RPC batching 和多 Mesh Montage 的工程形态。

不要把 2021/2024 的具体类名或内部函数签名直接当作 UE5.7/5.8 API。迁移的是所有权、预测、数据归属、清理和验证语义。

## 1. 先区分四种身份

复杂 GAS 问题至少同时存在四种身份，不能只看 AbilityClass：

1. **OwnerActor**：ASC 的长期拥有者；
2. **AvatarActor**：当前物理表现和执行载体；
3. **Grant Source**：谁把这份 AbilitySpec 授给 ASC；
4. **Activation Identity**：这一次具体激活，包括 SpecHandle、Activation/Prediction identity 和项目自己的 generation/sequence。

典型玩家结构：

```text
PlayerState / Stable Player Agent
  └─ ASC (persistent OwnerActor)
        ├─ AbilitySpec from Sword A
        ├─ AbilitySpec from Sword B
        └─ active/persistent effects

Current Pawn / Form / Mount Avatar
  ├─ Mover
  ├─ Mesh / AnimInstance
  ├─ Physics / Camera
  └─ AvatarActor
```

同一个 AbilityClass 可以由不同装备来源分别授予。此时 `AbilityClass`、AbilityTag、InputTag 都不能单独充当 grant identity；最终仍需保存并关联对应的 spec handle。

### 1.1 OwnerActor 与 AvatarActor

如果玩家死亡、变形、骑乘或重新生成后需要保留 Attributes、GameplayEffects、长期技能/背包关联，则稳定 Owner 与可替换 Avatar 分离是自然模型。

Avatar 更换时需要显式重新建立 ASC ActorInfo，并对旧 Avatar 的 transient state 做 teardown：

- AbilityTask 外部 delegate；
- TargetData 等待者；
- Montage / Linked Layer preview；
- MotionWarp / Mover movement operation；
- old Avatar camera / physics / presentation binding；
- 任何捕获旧 Pawn、Mesh、AnimInstance 的 async callback。

不要因为 ASC 还活着，就假设旧 Avatar 的弱引用、SourceObject、Montage instance、TargetActor 仍然有效。

### 1.2 SourceObject 是运行时来源上下文，不是永久 ItemId

`FGameplayAbilitySpec::SourceObject` 很适合表达“这份 Spec 是由哪把武器、装备实例或授予源创建的”。它可以解决：

- 两把武器授予同一个 AbilityClass；
- Ability 内需要访问实际武器 runtime state；
- 卸下其中一个 source 时只撤销它自己的 grant。

但 SourceObject 应当视为**运行时引用/上下文**，而不是 SaveGame 的永久业务身份。现代 GAS 中它可以是弱引用语义；持久装备身份仍使用稳定 ItemId / EquipmentEntryId / DefinitionId。

推荐层次：

```text
Persistent ItemId
   ↓ runtime rebuild
Equipment Entry / Grant Source Object
   ↓
FGameplayAbilitySpec.SourceObject
   + exact SpecHandle / GrantedHandles
```

卸装时优先按授予时保存的最终 handle 精确撤销，而不是重新扫描 AbilityClass 或 GameplayTag 猜来源。

如果必须遍历 ActivatableAbilities：

- 使用目标引擎当前推荐的 ability-list lock / safe iteration 机制；
- 先收集需要删除的 handle；
- 离开不允许 mutation 的迭代范围后再删除；
- 不在遍历中让同步回调重入修改同一容器。

## 2. PredictionKey 不是“整个 Ability 生命周期通票”

### 2.1 Activation PredictionKey 的有效范围

LocalPredicted Ability 激活会产生 activation PredictionKey。它用于把客户端预测副作用和服务器确认结果关联起来。

关键规则：**PredictionKey 只在明确的 prediction window 中有效。**

可用的心智模型：

```text
Activate Ability
└─ Activation Prediction Window
   ├─ predicted GE
   ├─ predicted Cue
   ├─ immediate TargetData / request
   └─ window ends

later latent callback
└─ NOT automatically the same prediction window
```

进入 `WaitDelay`、Montage notify、异步 trace、定时器、网络回调、外部 delegate、下一帧 combo section 后，不得假设激活时那把 PredictionKey 仍可继续预测。

### 2.2 Scoped Prediction Window

如果 latent continuation 确实需要新的预测副作用，必须用**目标 UE 版本正式支持的 Scoped Prediction Window / sync-point 机制**建立新的预测范围。

旧文档中的 `WaitNetSync`、`FScopedPredictionWindow` 等名称只能作为历史线索；在 UE5.7/5.8 项目中先查当前引擎源码和已有项目封装。

每个异步边界都回答：

| 问题 | 必须回答 |
|---|---|
| 谁继续？ | owning client、Authority、两端还是仅 presentation |
| 当前 prediction identity 是什么？ | activation key、新 scoped key、项目 sequence/generation |
| 可预测什么？ | GE、Cue、Montage、HitWindow、movement preview |
| 服务器拒绝怎么办？ | rollback / correction / stop preview |
| callback 迟到怎么办？ | generation / Avatar / SpecHandle revalidate |

### 2.3 不要复用 stale PredictionKey

错误做法：

```text
Ability Activate 得到 PredictionKey K1
→ 等 400 ms Montage Section
→ 继续拿 K1 预测 Cost / Damage / Movement
```

如果 K1 已离开 prediction scope，继续使用它会制造“看起来带 key、实际没有合法预测窗口”的假一致性。

正确选择通常只有两类：

1. 新的合法 scoped prediction；
2. 后续业务改为 Authority continuation，客户端只保持 cosmetic preview。

## 3. Client Ability End 与 Authority End 分开

高延迟下，客户端 Montage 比服务器更早自然结束很常见。不能因此让客户端直接决定服务器业务 Ability 已结束。

历史 GAS 有 `Server Respects Remote Ability Cancellation` / termination security 等设置。核心迁移原则：

- **execution policy** 决定能力在哪里运行；
- **security/termination policy** 决定客户端是否有权要求服务器启动/结束；
- 两者不是同一件事。

对于伤害、交易、Traversal、库存 mutation 等不可逆业务：

- Authority 拥有最终结束条件；
- owning client 可以请求 cancel，但服务器重验；
- prediction reject 要撤销本地 preview；
- 客户端自然 Montage 完成不自动等价 Authority 的 HitWindow / Cost / Damage 完成。

多 Section combo 应记录：

```text
SpecHandle
Activation identity
Combo Sequence
Section index
HitWindow generation
Client presentation end
Server gameplay end
```

## 4. TargetData 是请求载荷，不是授权

`FGameplayAbilityTargetData` / Handle 适合传递与一次 Ability activation 绑定的网络数据，例如：

- Actor / component candidate；
- hit result；
- aim origin/direction；
- traversal ledge samples；
- custom compact request data。

### 4.1 为什么比“先复制变量再激活”可靠

错误模式：

```text
Client sets replicated CurrentTarget
Client immediately activates Ability
Server assumes CurrentTarget already arrived
```

属性复制和 Ability RPC/GameplayEvent 不承诺按业务需要的顺序同时到达。

如果数据必须与某次 activation 原子关联，优先把它放进 GameplayEvent/TargetData/当前项目正式 request payload，携带同一 activation identity。

### 4.2 Authority validation envelope

TargetData `NetSerialize` 成功只说明“能传输”，不说明“可信”。

服务器按动作类型重验：

- source Ability / Item / Equipment 仍存在且属于请求者；
- 当前 Avatar / stance / action lock / cooldown 合法；
- target 仍有效、可见、可伤害/可交互；
- distance / LOS / facing；
- trace geometry / collision channel；
- HitWindow / combo sequence；
- traversal obstacle height/depth/slope/clearance；
- target primitive velocity / moving-base identity；
- montage / action candidate 是否在 server-approved set；
- request generation 未过期。

客户端数据可以是：

1. **候选**：服务器重 trace 后决定；
2. **压缩证据**：服务器验证范围后接受；
3. **confirm only**：客户端只说“现在确认”，服务器自己生成 TargetData。

### 4.3 Consume once 与数据早到 race

服务器端 TargetData 等待逻辑必须处理两种顺序：

```text
listener first -> data later
data first -> listener later
```

生产合同：

- key by SpecHandle + ActivationPredictionKey 或当前引擎等价 activation identity；
- 注册 delegate 后检查 data 是否已经存在；
- 收到后 `consume once`；
- cancel/end 后清理 listener；
- duplicate / replay / late packet 不重新结算；
- 同一 AbilityClass 的两把武器不能串数据。

GASShooter 历史实现使用 `ConsumeClientReplicatedTargetData()` 和“注册后调用 already-set delegate”的模式。不要照抄 API 名称，但保留 race contract。

## 5. 自定义 TargetData 设计

只发送完成请求需要的字段。

推荐：

```text
Request identity
Source identity
Target candidate / compact hit sample
quantized origin/direction
action-specific small enum/tag/flags
```

谨慎：

- 整个 inventory snapshot；
- 大型 GameplayTagContainer；
- 重复的静态 Definition 文本；
- 客户端计算的最终 damage；
- 可由服务器按 seed/definition 重建的大量 cosmetic sample。

自定义 TargetData 需要按目标引擎要求实现 ScriptStruct/NetSerialize/traits，并验证对象引用、量化精度、Iris/legacy replication（若相关）和版本演进。

## 6. AbilityTask 是有生命周期的异步对象

AbilityTask 不只是“Blueprint latent node”。它通常同时拥有：

- Ability / ASC weak context；
- SpecHandle / Activation identity；
- delegate subscription；
- replicated event/TargetData waiting state；
- TargetActor / async query；
- completion/cancel callbacks。

### 6.1 清理顺序

在 `OnDestroy()` / EndTask 路径里：

1. 先停止外部 targeting / timer / async source；
2. 解绑外部 delegate；
3. 解除 confirm/cancel input 绑定；
4. 清理 waiting TargetData listener；
5. invalidate task generation；
6. 最后调用会清空 Ability/ASC context 的父类 cleanup。

不要先 `Super::OnDestroy()` 再访问已经被父类置空的 Ability/ASC。

### 6.2 Reusable TargetActor / Targeter

复用 TargetActor 可以减少高频 spawn/GC 和初始化成本，但必须有 reset contract：

```text
Owner / Avatar
Ability / ASC
SpecHandle / Prediction identity
Trace config
filter / collision
previous hit cache
confirm / cancel binding
debug state
request generation
active task owner
```

每次 Begin 都覆盖全部本次状态，每次 Stop 都回到可验证 idle。

“对象没有 Destroy”不等于“可安全复用”。

### 6.3 何时不要 TargetActor

如果目标只是一次轻量 line/sphere query，现代项目可以优先考虑：

- AbilityTask + value request state；
- subsystem/service query；
- Mover/GAS 专门 request data；
- 无 Actor 的函数化 targeter。

不要为复用而引入全局共享可变 TargetActor。

## 7. Ability RPC Batching 是 transport optimization

历史 GAS ability batching 可以把同一原子 scope 中的：

```text
TryActivate
TargetData
EndAbility
```

合并为较少 RPC。

核心规则：**Ability RPC batching 只是 transport optimization，不是 business transaction。**

它不提供：

- Authority permission；
- idempotency；
- rollback；
- anti-replay；
- TargetData correctness；
- guaranteed gameplay commit。

### 7.1 适合场景

- 同一帧 activation + immediate trace + end；
- profile 已证明 RPC 数量是瓶颈；
- payload 小且可一次验证。

### 7.2 不适合为了“凑 batch”改生命周期

持续自动攻击、多段 melee combo、长时间 channel ability、多个 HitWindow 不应被强制压成同一个 batch。

Batch 内每一项业务语义仍按普通路径校验。Batch reject/ability reject 也必须触发相同 rollback。

旧 `FScopedServerAbilityRPCBatcher` 等具体 API 在目标 UE5.7/5.8 必须重新查当前 GAS 源码。

## 8. Item-local state 不等于 Attribute

不要因为项目用了 GAS，就把所有数值都塞进 AttributeSet。

### 8.1 适合 AttributeSet

- Health / Mana / Stamina；
- shared reserve resource；
- 需要 GE aggregator/capture/stack/MMC/ExecCalc 的数值；
- 需要由 GameplayEffect 统一修改的长期角色属性。

### 8.2 适合 Item runtime state

- clip ammo；
- durability；
- heat；
- random roll / affix runtime values；
- item-local charges。

这些值通常更适合 compact item entry / UObject item instance / replicated value field，由 Ability 通过 ItemId / SourceObject / Equipment context 获取。

### 8.3 Dynamic AttributeSet removal race

`dynamic AttributeSet` 可以运行时加入 ASC，但 `remove` 有 replication race：

```text
client removes set
↓
late server attribute delta arrives
↓
receiver cannot resolve expected AttributeSet
```

如果生产项目必须动态移除：

- Authority 是 removal owner；
- 定义网络 fence/ack、grace period 或安全 teardown；
- 先停止所有引用该 Set 的 Ability/Effect；
- 处理 JIP/reconnect；
- 不让客户端随 UI 卸装立即销毁 replicated set。

无必要时，item-local state 比“每把武器一个 AttributeSet/ASC”简单得多。

### 8.4 手工 item prediction 要有 correction contract

历史 Shooter 会在 firing tag 活跃时临时抑制 clip ammo replication，避免 Authority snapshot 覆盖本地连射预测。

不要把“开火时停复制”写成通用规则。生产实现必须同时定义：

- 谁预测；
- 谁 authoritative；
- 何时重新开始复制；
- correction 如何应用；
- weapon swap/drop 时怎么 flush；
- generation 如何避免旧武器 correction 写入新武器。

## 9. GameplayEffectContext：执行上下文，不是业务仓库

自定义 EffectContext 适合携带一次执行所需 provenance：

- instigator/source；
- compact TargetData；
- hit metadata；
- damage source context；
- cue 需要的少量表现参数。

不适合：

- 完整 Inventory；
- SaveGame；
- 永久 Item ownership；
- 大型世界状态 snapshot。

自定义 Context 要验证目标引擎的：

```text
GetScriptStruct
Duplicate
NetSerialize
StructOps traits
AbilitySystemGlobals allocation path
```

## 10. GameplayCue 与 Authority truth 分离

GameplayCue 是表现通道。即使某些 Cue 经网络发送，也不能承担：

- 扣血；
- 资源消耗；
- Inventory mutation；
- 掉落/奖励真值。

多 pellet、多刀刃、多 impact 场景先做带宽预算。

可能策略：

```text
Authority damage results
  └─ compact presentation event
       ├─ seed
       ├─ a few impact positions
       └─ action id / surface summary
             ↓
clients reconstruct cosmetic detail
```

不要求每个 blade sample / pellet 都单独 NetMulticast Cue。

丢失不可靠 cosmetic cue 时，业务状态仍必须正确。

## 11. Predicted Montage 与多 Mesh / Linked Layer

GASShooter 历史项目为了 1P/3P Mesh 自定义了多 Mesh Montage replication。LGF/GASP 不应复制这套 ASC，但可以吸收 identity：

```text
Ability activation / prediction
+ Avatar generation
+ mesh / layer
+ montage instance
```

不是：

```text
Montage Asset == playback identity
```

### 11.1 Prediction reject rollback

客户端预测播放后若服务器拒绝：

- 只撤销属于该 activation 的 montage instance；
- 清理该 activation 的 notify delegate；
- 停该 activation 的 linked overlay / weapon layer；
- 清 movement preview / warp；
- 不误停新 Avatar 或后来播放的同名 montage。

### 11.2 SimulatedProxy

GameplayAbility 通常不在 SimulatedProxy 上作为业务逻辑执行；远端视觉通过复制状态、GameplayCue、Montage/animation presentation 等投影。

不要为了“所有端跑相同 Ability”破坏 Authority/Prediction 分工。

## 12. Replication mode 是状态可见性策略，不是权限

Full / Mixed / Minimal 等 ASC replication mode 决定哪些 GE/Tag/Cue 信息复制给谁，不改变 Authority 所有权。

设计时分别回答：

- 谁有权修改；
- owning client 需要看到什么；
- SimulatedProxy 需要什么表现状态；
- Debug/UI 是否依赖完整 GE；
- AI 是否需要 Full GE replication。

不要为了 UI 想看到一个数，就把整个 ASC replication mode 放大。

## 13. 生产验证矩阵

### 13.1 网络角色

- Standalone；
- Listen Host local；
- Listen remote AutonomousProxy；
- remote SimulatedProxy；
- Dedicated server；
- JIP / reconnect。

### 13.2 网络条件

- 0 / medium / high RTT；
- loss；
- jitter；
- duplicate / late request；
- correction；
- Avatar switch during ability。

### 13.3 Ability 生命周期

- accepted；
- rejected；
- local cancel；
- server cancel；
- natural client montage end before server；
- cost fail；
- TargetData invalid；
- SourceObject removed；
- equipment swap；
- death / transform。

### 13.4 记录字段

推荐诊断至少记录：

```text
Owner / Avatar
SpecHandle
SourceId / SourceObject name
Activation identity
PredictionKey / ScopedKey state
Ability sequence
TargetData sequence
Task generation
Montage mesh/layer/instance
Authority accept/reject reason
```

只记录“RPC submitted”或“Ability activated”不足以证明最终业务收敛。

## 14. 迁移旧 GAS 样例的门禁

GASDocumentation/GASShooter 的重要价值是解释机制和暴露历史踩坑，不是提供 2026 API 模板。

每条旧实现迁移前：

1. 固定外部源码 commit；
2. 标记外部目标 UE 版本；
3. 在当前项目引擎源码查同一语义的现行 API；
4. 检查 deprecated / Iris / registered subobject / prediction 变化；
5. 写当前项目行为测试；
6. 再实现最小迁移。

特别禁止直接照搬：

- UE4 TargetActor 体系的全部类层级；
- 老 input ID 绑定架构；
- 硬编码 `RequestGameplayTag()` 到热点；
- weapon `StaticLoadClass` 路径；
- “firing 时关 replication”但无 correction 的预测；
- 为 1P/3P Mesh 整体复制旧 ASC montage fork；
- 用 batching 替代 Authority transaction。
