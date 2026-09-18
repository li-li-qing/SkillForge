# Epic UE5.8 StateTree + Utility AI：决策、执行、打断与大规模 AI 蒸馏

> 第十二轮外部项目蒸馏。研究日期：2026-09-14。
>
> 主证据：Epic UE5.8 StateTree 当前文档/API。
>
> Utility AI 对照：`bohdon/UtilityAIPlugin@0f49e0c6d420497d3102c3975601360dc120bf15`，MIT。
>
> 辅助样本：`pittabio/StateTrees` 仅用于观察当前社区 StateTree 实验方向，不作为 Production API 权威。

---

## 1. 本轮为什么研究 StateTree + Utility AI

R11 已经解决了“大量 NPC 如何低成本存在”的问题：

- 远距离/低交互 Agent 可以留在 Mass；
- 高交互 Agent promotion 成完整 LGF Avatar；
- StableAgentId 与 Mass runtime handle 分离；
- CombatOwner 负责唯一战斗真值；
- Simulation / Representation / Replication LOD 分开。

R12 继续回答更上层的问题：

> 大量 NPC、Boss、宠物、坐骑和普通 Actor/Pawn 到底由谁做决策？

如果没有明确边界，很容易形成四套并行脑：

1. AIController/BehaviorTree 在决定动作；
2. StateTree 又决定状态；
3. Utility AI 组件又维护 CurrentAction；
4. GAS Ability 内再根据条件偷偷决定另一个动作。

这会直接产生：

- AI 抖动；
- 同一帧多个动作抢控制权；
- Move 与 Ability 互相取消；
- Boss 阶段逻辑和 Utility 评分互相覆盖；
- 玩家给宠物“停留”命令后自动 AI 下一帧又继续追人；
- Mass promotion 后忘记原本要做什么；
- 服务器和客户端对“AI 当前意图”理解不一致。

因此本轮不是选择“StateTree 还是 Utility AI”，而是建立完整的 **Decision / Execution / Authority** 分层。

---

# 2. 技术时效性门

## 2.1 Epic StateTree：Current

UE5.8 官方仍把 StateTree 定义为通用的分层状态机：

- Selector；
- State；
- Transition；
- Task；
- Evaluator；
- Context；
- Parameters；
- Event；
- linked/external tree。

StateTree 当前不只是 AI 专用系统。

它是通用 Gameplay 状态编排系统。

因此：

**StateTree core：Current。**

对 LGF 当前目标 UE5.7 仍必须重新核对具体签名，但架构方向属于当前 UE5 体系。

---

## 2.2 UE5.8 Utility Selector：Current feature，但 Consideration API 仍 Experimental

UE5.8 StateTree 当前已经提供：

- Try Select Children With Highest Utility；
- Try Select Children At Random Weighted By Utility。

每个 child state 可以有：

- Considerations；
- logical operator；
- Weight。

官方选择器文档中 Consideration 输出归一化的 0..1 score。

但是 API 层 `FStateTreeConsiderationBase` 当前仍明确标注：

> Experimental / API expected to change.

因此必须拆成两个结论：

### 可以依赖的架构

StateTree 可以承担 Utility-style sibling state selection。

### 不应固化的 API

LGF Foundation public header 不应该直接把实验性 Consideration 类型变成长期 ABI。

推荐：

```text
LGF Pure Utility Kernel
        ↓
StateTree Adapter (target UE version)
        ↓
UE5.7 / UE5.8 StateTree nodes
```

当 Epic API 改动时，主要改 Adapter。

---

## 2.3 bohdon/UtilityAIPlugin：Stable-but-old mechanism sample

固定提交：

`0f49e0c6d420497d3102c3975601360dc120bf15`

时间：2025-04-06。

优点：

- 代码体量小；
- Utility 语义清晰；
- Tag integration 清晰；
- 有 Gameplay Debugger；
- 有 hysteresis；
- 有 busy / interrupt；
- Action execution 与 scoring 有一定分层。

但不能作为 UE5.8 API 模板：

- `.uplugin` 没有固定 EngineVersion；
- Action 是 UObject instance；
- Component 固定 TickInterval 0.025 秒；
- 每次 Tick 全量评分所有 Action；
- `CalculateDataScore()` 在固定源码中仍是 TODO；
- 很多评分可以落到 Blueprint；
- 当前 StateTree 已经原生提供 Utility selector。

结论：

**吸收 Utility AI 的稳定思想，不复制它的 runtime ownership。**

---

## 2.4 pittabio/StateTrees：Fresh experimental learning sample

该仓库创建于 2025-12，2026-04 仍更新，主题是 StateTree AI / Quest 等实验。

但：

- 作者自己标 experimental learning/testing；
- license metadata 不明确；
- stars 很少；
- 不是 Epic 官方实现。

所以只适合辅助观察社区用法。

本轮不把它作为正式生产证据。

---

# 3. StateTree 的真实运行心智

## 3.1 Active Path，而不是“当前一个节点”

StateTree 的核心心智不是传统 flat FSM：

```text
Root
 └─ Combat
     └─ Melee
         └─ Attack
```

当 leaf `Attack` 被选中时，通常整个 root-to-leaf path 都是 active。

因此：

- Root Task 可能在运行；
- Combat Task 可能在运行；
- Melee Task 可能在运行；
- Attack Task 也可能在运行。

不要把它理解成：

```text
只执行 Attack，父层只是目录
```

这会直接影响：

- context ownership；
- task cleanup；
- async request lifetime；
- gameplay tag；
- movement lock；
- ability wait；
- perception evaluator。

---

## 3.2 State Tasks 不是 BehaviorTree Sequence

一个非常容易迁移错误的心智：

```text
Task A
Task B
Task C
```

不应该默认理解成：

```text
A 成功 → 才执行 B → B 成功 → 才执行 C
```

StateTree 当前提供 Task Completion policy。

需要明确：

- ANY；
- ALL。

因此设计 State 时必须写清楚：

```text
Task: FaceTarget
Task: MoveIntoRange
Task: PrepareAttack
Completion: ALL
```

或：

```text
Task: WaitForAnimation
Task: WaitForCancelSignal
Completion: ANY
```

如果业务确实要求串行：

应使用：

- 多个 State；
- explicit transitions；
- 一个拥有内部序列的 Task；
- linked subtree。

不要依赖编辑器 Task 列表视觉顺序表达序列语义。

---

## 3.3 Task Completion 与 Task Cancellation 必须成对设计

异步 StateTree Task 常见类型：

- Move；
- Play Montage；
- Activate Ability；
- Wait Gameplay Event；
- Claim SmartObject；
- Async query；
- Path request；
- animation transition。

每个任务必须明确：

```text
Enter/Start
Tick / Event
Completion
Exit
Cancel
Late callback rejection
```

推荐业务 identity：

```text
DecisionGeneration
StateGeneration
RequestId
AvatarGeneration
```

至少选一个能判断 callback 是否仍属于当前任务的 generation。

典型错误：

```text
State Attack 进入
→ 请求 Move A
→ Utility 重新选择 Dodge
→ Attack Exit
→ Move A 下一帧完成
→ callback 继续 Activate Attack Ability
```

正确：

```text
Move completion
→ compare request generation
→ state/decision 已换代
→ ignore
```

---

# 4. UE5.8 Utility Selector

## 4.1 Highest Utility 的适用范围

非常适合 sibling states：

```text
Combat
 ├─ Attack
 ├─ Defend
 ├─ Dodge
 ├─ Heal
 └─ Reposition
```

如果这五个动作共享相同决策上下文，就没有必要再建立一个平行的 UtilityAIComponent 来选择同样的五个动作。

StateTree parent 可以直接做 utility selection。

---

## 4.2 Weighted Utility 的适用范围

适合希望：

- 仍受情境影响；
- 但不完全 deterministic；
- 同分/近分动作有变化；
- 避免 AI 机械重复。

例如：

```text
Idle
 ├─ LookAround
 ├─ AdjustWeapon
 ├─ Taunt
 └─ RepositionSmall
```

不适合把关键战斗 Authority 结果随机掉。

Utility 只决定意图。

最终攻击是否合法仍走 Ability / Authority。

---

## 4.3 Consideration 必须是纯评分

推荐签名思想：

```text
Score = F(Context)
```

其中 Context 是 snapshot。

评分阶段允许：

- 读距离；
- 读 normalized health；
- 读 cooldown ready bit；
- 读 threat；
- 读 LOS cached result；
- 读 angle；
- 读 recent damage；
- 读 player command；
- 读 resource ratio。

评分阶段禁止：

- ActivateAbility；
- CommitAbility；
- ApplyGameplayEffect；
- MoveTo；
- Claim SmartObject；
- SpawnActor；
- 写 Inventory；
- 扣资源；
- 写 canonical aggro；
- 发奖励。

原因不是代码洁癖。

因为 selector 可能：

- 重新评分；
- debug 评分；
- preview；
- 多个候选同时评分；
- 因 transition 重新 selection。

如果评分有副作用，就会出现：

```text
“只是看一眼这个动作值不值得做”
却已经扣了资源
```

---

# 5. Utility score 设计

## 5.1 评分输入必须有单位和范围

坏设计：

```text
DistanceScore = 1 - Distance
```

Distance 可能是 500、5000、50000。

正确做法：

```text
DistanceMeters
→ normalize [0, DesiredRange]
→ response curve
→ 0..1 utility
```

每个 Consideration 必须说明：

- raw domain；
- normalization range；
- response curve；
- clamp；
- stale behavior；
- missing input behavior。

---

## 5.2 不要把“权重”当万能修正器

如果 score 设计不稳定，只加 Weight 会让调参越来越不可解释。

调试必须能显示：

```text
Attack = 0.72
  distance = 0.90
  health = 0.80
  line_of_sight = 1.00
  cooldown = 1.00
  weight = 1.00

Dodge = 0.68
  recent_damage = 0.85
  stamina = 0.80
```

否则看到“为什么 AI 突然闪避”时无法回答。

---

## 5.3 Utility AI Plugin 的 Combine 思想

固定源码支持：

- Multiply；
- Max；
- Min。

这个思想仍值得保留。

例如攻击：

```text
Distance * LOS * Ammo
```

其中任一为 0，就变成 0。

而逃跑：

```text
Max(LowHealth, Surrounded, HugeBurstDamage)
```

任一危险足够高都可以触发。

StateTree 当前 Consideration AND/OR 也提供类似“低值限制 / 高值取优”的组合思维。

不要机械映射实现细节，但组合语义可以复用。

---

# 6. 决策稳定性：避免 AI 抖动

## 6.1 Hysteresis

UtilityAIPlugin 的 `ScoreHysteresisThreshold` 是很好的稳定机制。

如果当前动作分数为 0.70：

新动作 0.705 不应该立刻切换。

可以要求：

```text
NewScore > CurrentScore + 0.05
```

才允许抢占。

---

## 6.2 Minimum Dwell Time

仅有 hysteresis 仍可能抖。

例如：

```text
Attack 0.8
Dodge 0.9
Attack 0.8
Dodge 0.9
```

网络延迟、目标距离边界或血量变化会让两者持续交替。

增加：

```text
MinimumDwell = 0.3s
```

除非出现 hard interrupt，否则当前意图至少保持一定时间。

---

## 6.3 Switch Penalty

候选动作刚刚执行过，可以临时减分：

```text
FinalScore = BaseScore - SwitchPenalty
```

避免：

```text
Attack A
Attack B
Attack A
Attack B
```

机械来回切。

---

## 6.4 Cooldown / Recency

UtilityAIPlugin 保存：

- ExecuteCount；
- LastExecuteTime；
- LastFinishTime。

这是值得吸收的调试和评分输入。

LGF 可以把它抽象为轻量 DecisionHistory，而不是为每个 Action 建 UObject。

---

## 6.5 FreezeScore 只是一个策略，不是万能规则

UtilityAIPlugin 支持动作激活后冻结 score。

优点：

- 避免 active action 因瞬时 input 波动被抢；
- 简单。

风险：

- 动作执行很长时上下文已经完全变化；
- 冻结可能错过紧急 Dodge / Death / PlayerCommand。

因此 LGF 不使用全局 Freeze。

改成：

```text
Interrupt Policy
 ├─ Never
 ├─ HardOnly
 ├─ HigherPriority
 ├─ UtilityThreshold
 └─ Immediate
```

并结合 GameplayTag / Ability cancellation policy。

---

# 7. 一个 high-level Decision Owner

## 7.1 默认：StateTree 是 Owner

完整 Avatar 推荐：

```text
DecisionContext
      ↓
StateTree
      ↓
DecisionIntent
      ↓
GAS / Mover / SmartObject
```

StateTree 维护：

- 当前高层行为；
- transition；
- utility sibling selection；
- task lifecycle。

---

## 7.2 Utility scorer 不是第二个 brain

独立 scorer 可以存在，但只输出：

```text
CandidateActionId
Score
Reason Breakdown
```

不要再维护：

```text
CurrentAction UObject
Executing state
Abort lifecycle
```

否则会与 StateTree 重叠。

---

## 7.3 BehaviorTree 的位置

BehaviorTree 仍可以作为 domain executor。

例如一个 legacy “Search Room” 行为已经很成熟：

```text
StateTree
→ SearchRoom State
→ Task starts small BT
→ BT completes/fails
→ Task reports StateTree result
```

StateTree 仍是 high-level owner。

不要：

```text
BT 选 Attack
StateTree 也选 Dodge
Utility 选 Heal
```

---

# 8. StateTree + GAS

## 8.1 StateTree 只提交 Ability intent

例如 Attack Task：

```text
StateTree Attack Task
→ resolve ability intent / InputTag / AbilityTag
→ ask ASC to activate
→ store activation identity
→ wait outcome
```

真正：

- Cost；
- Cooldown；
- Prediction；
- TargetData；
- Damage；
- GameplayEffect；

仍由 GAS / Authority 管。

---

## 8.2 Utility score 不等于 Ability 可激活

可以出现：

```text
Attack score = 0.95
```

但 GAS 当前：

- mana 不足；
- cooldown；
- blocked tag；
- target invalid；
- weapon missing。

因此推荐：

```text
cheap readiness bit
→ score filtering
→ selected intent
→ GAS final CanActivate
```

不在每个 utility candidate 上调用昂贵完整 Ability activation flow。

---

## 8.3 Ability ended 不一定等于 Decision ended

一个攻击决策可能：

```text
Approach
→ Face
→ Activate Ability
→ Recover
```

Ability 完成只是 Task 的一个事件。

StateTree 决定是否：

- 连招；
- 转 Dodge；
- 继续追击；
- 回 Idle。

---

# 9. Interruption 合同

## 9.1 不用单一 Busy bool

UtilityAIPlugin 的 BusyTags 是很好的教学入口，但 Production 需要更细。

推荐 interruption context：

```text
CurrentIntent
CurrentDecisionGeneration
CurrentAbilitySpec/Activation identity
CurrentMoveRequestId
CurrentSmartObjectClaim
CurrentMontage identity
CurrentAvatarGeneration
InterruptReason
```

---

## 9.2 State switch 顺序

推荐：

```text
1. Decide to switch
2. Increment DecisionGeneration
3. Request cancel current executor
4. Executor acknowledges / finishes / force-cancel policy
5. cleanup old task resources
6. enter new State
7. start new executor
```

紧急事件可以支持 force transition，但仍必须有旧 callback rejection。

---

## 9.3 GAS cancellation

不要把：

```text
State Exit
```

直接等价为：

```text
Cancel every Ability of class X
```

继续遵守前面 GAS 轮次建立的 identity：

- exact spec handle；
- source identity；
- activation/prediction identity；
- generation。

---

## 9.4 Mover cancellation

同理：

- stop montage 不等于 stop Mover LayeredMove；
- StateTree Task 必须拥有具体 movement request/cancel identity；
- Avatar change 后旧 Move completion 不得继续触发 transition。

---

# 10. DecisionContext Snapshot

## 10.1 为什么不直接在每个 scorer 里查世界

如果每个 Consideration 都做：

- GetAllActors；
- line trace；
- ASC tag query；
- inventory lookup；
- path query；

10 个候选动作 × 8 个 consideration × 1000 个 NPC 会爆炸。

应该先构建：

```text
DecisionContext
{
  TargetId,
  TargetDistance,
  TargetAngle,
  HasLOS,
  HealthRatio,
  StaminaRatio,
  RecentDamage,
  ThreatCount,
  AbilityReadyBits,
  PlayerCommand,
  LocationBucket,
  Timestamp,
  Generation
}
```

然后所有 scorer 只读这个 snapshot。

---

## 10.2 Freshness

每个输入要知道更新时间。

例如 LOS：

```text
LOS=true
MeasuredAt = 12.30
Now = 12.95
MaxAge = 0.25
```

此时必须按 stale policy：

- resample；
- degrade score；
- reject candidate。

不能永久信任旧 cache。

---

# 11. Event-driven，而不是所有 AI 40Hz 全量评分

UtilityAIPlugin 当前固定 0.025s TickInterval。

这对少量 AI 很简单。

但 5000 Agent：

```text
5000 * 40 = 200,000 decision passes/sec
```

每次再评分 10 个 Action：

```text
2,000,000 action evaluations/sec
```

还没算 consideration。

LGF 默认改成：

```text
Dirty reason / Signal / Event
→ enqueue decision
→ budget bucket
→ score affected candidates
```

加上：

- Simulation LOD；
- distance bucket；
- combat urgency；
- staggered scheduling；
- max decisions/frame。

---

# 12. Mass + StateTree

## 12.1 低保真 Agent

Mass Tier 1 Agent 不应该每个都创建：

- AIController；
- UtilityAIComponent；
- Action UObject 数组；
- full StateTree Actor brain。

使用：

```text
Mass fragments
+ shared config
+ StateTree/Mass adapter where justified
+ batched context/scoring
```

---

## 12.2 MassStateTree 仍属 Experimental stack

UE5.8 有：

- MassStateTree Schema；
- MassStateTree Trait；
- MassStateTree Subsystem。

但它位于 MassAI / MassAIBehavior 路线。

上一轮已经建立：

MassAI 是 Experimental feature gate。

因此 LGF 的 StableAgent / DecisionState 不依赖 MassStateTree internal runtime layout。

---

## 12.3 低保真 Utility

远距离 NPC 可能只需要：

```text
Wander = 0.4
Eat = 0.7
Rest = 0.3
Flee = 0.0
```

不需要：

- 精确 LOS；
- 逐帧角度；
- weapon AbilityTag；
- Montage phase。

promotion 后才切到完整 context。

---

# 13. Promotion 时决策连续性

## 13.1 不保存 StateTree 内部 frame

禁止长期持久化：

- internal active node pointer；
- task instance address；
- transient execution handle；
- editor node index；
- raw StateTree frame memory。

这些都是 runtime implementation detail。

---

## 13.2 保存业务 DecisionState

推荐：

```text
StableAgentId
HighLevelIntent = Patrol
TargetStableId
DestinationSemanticId
CombatPhase
CooldownSummary
PlayerCommand
DecisionGeneration
LastDecisionTime
```

promotion：

```text
Mass DecisionState
→ spawn Avatar
→ build StateTree parameters/context
→ select compatible starting state
→ continue behavior
```

---

## 13.3 Demotion

```text
Full Avatar StateTree
→ extract stable business intent
→ commit StableAgent state
→ cancel runtime executor
→ destroy/release Avatar
→ Mass resumes low-fidelity decision
```

---

# 14. Player commands：宠物/坐骑优先级

用户未来希望大量 NPC/宠物都可以骑。

自动 AI 不能与玩家命令同级。

推荐优先级：

```text
Hard Safety / Death
Player Direct Command
Scripted/Cinematic Override
Combat Emergency
Autonomous Utility
Idle Flavor
```

例如：

```text
Player: Stay
```

自动 scorer 即使：

```text
ChaseEnemy = 1.0
```

也不能立即抢回控制。

只有：

- 玩家解除 Stay；
- hard safety；
- 明确 policy 允许；

才切换。

---

# 15. Mount 特殊合同

Mounted 状态时至少涉及：

- Rider input；
- mount movement；
- mount autonomous survival AI；
- combat ability；
- animation；
- camera。

必须只有一个 movement owner。

推荐：

```text
Mounted
→ PlayerCommand layer owns locomotion intent
→ Mount autonomous utility limited to non-conflicting reactions
```

例如允许：

- 播放害怕表现；
- 轻量 head look；

不允许自动 AI：

- 自己转身逃跑；
- 自己 MoveTo 食物；
- 与玩家输入争抢 Mover。

---

# 16. Boss AI

Boss 不一定需要全 Utility。

建议：

```text
StateTree = phase / scripted structure
Utility = local choice within phase
GAS = authoritative attacks
```

例如：

```text
Phase 2
 ├─ Melee Utility Group
 │   ├─ HeavyAttack
 │   └─ Sweep
 ├─ Ranged Utility Group
 │   ├─ Projectile
 │   └─ GroundAOE
 └─ Emergency
     └─ BreakStagger
```

这样 Boss 的整体设计仍可控，而局部有动态感。

---

# 17. 普通敌人

普通近战敌人可以更简单：

```text
Idle
Sense
Combat
 ├─ Approach
 ├─ Attack  [utility]
 ├─ Dodge   [utility]
 └─ Recover
Dead
```

不要为了“AI 高级”塞 50 个 utility action。

候选越多：

- 调参越难；
- profiler 越难；
- 行为越不可预测。

---

# 18. SmartObject

StateTree 可以决定：

```text
Intent = UseBench
```

但执行仍走：

```text
Find candidate
→ Authority/claim validation
→ Claim
→ Move
→ Interact
→ Release
```

评分阶段只能读：

```text
BenchAvailableCached
Distance
NeedRest
```

不能在 scoring 时 Claim。

---

# 19. Perception 与 Utility

不要每个 utility scorer 自己 line trace。

推荐：

```text
Perception/Sensor layer
→ canonical sensory cache
→ DecisionContext
→ Utility/StateTree
```

比如：

```text
VisibleTargets
NearestThreat
LastKnownTargetLocation
HasRecentLOS
HeardNoise
```

统一采样。

---

# 20. GameplayTag 的角色

Tags 很适合表达：

- State.Stunned；
- State.Dead；
- AI.Command.Stay；
- AI.Intent.Attack；
- Ability.Blocked；
- Combat.InAbility。

但不要把所有 utility numeric input 变成 Tag。

距离、角度、健康比、时间等继续用 typed numeric data。

---

# 21. UtilityAIPlugin 值得保留的实现思想

## 21.1 ScoreHysteresisThreshold

保留。

但升级为可按 action/state/category 配置。

---

## 21.2 Score breakdown

保留，而且提升为强制调试能力。

---

## 21.3 Tag filter

保留。

用于 cheap gate：

- Require；
- Ignore；
- TagQuery。

---

## 21.4 Last execute / finish time

保留为 DecisionHistory 输入。

---

## 21.5 Freeze score

保留为可选策略，不作为默认。

---

## 21.6 Action execution 与 selection 分离

保留思想。

但在 LGF 中进一步拆成：

```text
Utility scorer
StateTree owner
Domain executor
Authority
```

---

# 22. UtilityAIPlugin 明确拒绝项

## 22.1 固定 25ms 全 Action 扫描

少量 NPC 可用。

大规模不作为默认。

---

## 22.2 每个 Action 一个 UObject

复杂高价值 Actor 可以接受。

Mass 大量实体默认不接受。

---

## 22.3 Blueprint scoring 热循环

设计期方便。

Production 大规模默认将核心 scorer 数据化/C++ 化。

---

## 22.4 `CalculateDataScore()` 尚未完成

README 的“data scoring”理念不能被写成已完成 production feature。

固定源码仍 TODO。

这是本系列“README 不是 active code evidence”的又一个案例。

---

## 22.5 Utility component 自己持有 CurrentAction

如果项目不用 StateTree，这可以成立。

但 LGF 默认引入 StateTree 后，不再允许第二个 high-level current owner。

---

# 23. StateTree Utility Consideration 的采用策略

## UE5.7 主线

LGF 当前目标仍是 5.7。

不要假设 5.8 editor/API 节点完全可用。

实现 scorer kernel：

```text
EvaluateAttack(Context)
EvaluateDodge(Context)
EvaluateHeal(Context)
```

通过 5.7 adapter 接入现有 StateTree/selector 能力。

---

## UE5.8

可以评估原生 Utility selector。

如果采用：

- adapter 内封装 Consideration；
- public ABI 不暴露实验节点类型；
- 自动化测试选中结果；
- 记录 API 版本。

---

# 24. Decision Generation

所有外部异步执行都应绑定同一 generation。

```text
DecisionGeneration = 42
Intent = Attack
AbilityRequest generation=42
MoveRequest generation=42
```

StateTree 切换 Dodge：

```text
DecisionGeneration = 43
```

此时 generation 42 的：

- Move completion；
- async trace；
- ability callback；
- montage callback；

即使回来，也不能重新驱动当前决策。

---

# 25. DecisionIntent

推荐独立于 StateTree internal node：

```text
DecisionIntent
{
  IntentTag,
  TargetStableId,
  WorldPoint,
  AbilitySemanticId,
  SmartObjectSemanticId,
  Priority,
  DecisionGeneration,
  CreatedAt,
  ExpiresAt
}
```

不是所有字段都必须存在。

但 intent 是业务层稳定数据。

---

# 26. Authority

AI 通常在服务器执行，但仍不要混淆：

```text
“服务器上的 AI 选择 Attack”
```

和：

```text
“Attack 已造成伤害”
```

Attack intent 仍要经过 GAS/Combat Authority validation。

这对以后：

- replay；
- prediction；
- bot possession；
- remote proxy；
- server perf；

都更安全。

---

# 27. 客户端职责

远端客户端不需要跑完整权威 StateTree 来决定结果。

可以：

- 接收表现所需 state/intent；
- animation prediction；
- cosmetic anticipation；
- debug mirror。

不能：

- 客户端 utility 分数决定 server damage；
- 客户端 StateTree transition 发放 loot。

---

# 28. Debugger 是 AI 系统的一部分

UtilityAIPlugin 的 Gameplay Debugger 是非常值得吸收的方向。

LGF AI Debug 至少显示：

```text
StableAgentId
AvatarGeneration
DecisionGeneration
DecisionOwner
Active StateTree path
Current Intent
Current Target
Player Command
Top candidates
Score breakdown
Hysteresis threshold
Minimum dwell remaining
Ability executor
Mover request
SmartObject claim
Last interrupt reason
Last transition reason
Context freshness
```

没有这些信息，Utility AI 调参几乎只能靠猜。

---

# 29. Replay / 可重复性

Weighted Utility 有随机时，应考虑：

- server authoritative random；
- seeded stream；
- debug/replay capture；
- save 是否需要最终结果而非 RNG internal state。

不要让每个客户端自己抽不同动作。

---

# 30. Save / Load

长期保存：

- stable intent；
- target stable id；
- phase；
- cooldown；
- player command；
- quest/AI persistent state。

不保存：

- task pointer；
- StateTree execution frame；
- transient request handle；
- current Blueprint node pointer。

加载后重建 runtime。

---

# 31. Avatar 替换

变身时：

```text
Old Avatar
→ DecisionOwner freeze
→ cancel old executor
→ capture stable DecisionState
→ old Avatar teardown
→ new Avatar bind
→ rebuild StateTree context
→ validate intent against new form
→ resume or select fallback
```

例如玩家/NPC 变成树桩：

Attack intent 可能不再兼容。

此时保持 StableAgentId，但重新选择：

```text
DisguisedIdle
```

---

# 32. NPC 吸收/变形

如果用户吸收 NPC 并变成该 NPC：

不要把 NPC 原 StateTree runtime pointer 转移给玩家。

应该转移：

- FormData；
- animation set；
- permitted ability set；
- appearance；
- stable semantic data。

玩家控制层替代 autonomous DecisionOwner。

---

# 33. Pet AI

宠物建议双层：

```text
Command Layer
 ├─ Follow
 ├─ Stay
 ├─ AttackTarget
 ├─ Passive
 └─ Mount

Autonomous Layer
 ├─ self-preservation
 ├─ combat micro
 └─ idle flavor
```

Command Layer 能 gate Autonomous Utility。

---

# 34. 不要所有东西都做 StateTree

适合纯函数/直接代码的逻辑：

- damage formula；
- stat aggregation；
- inventory transaction；
- simple projectile step；
- deterministic low-level movement math。

StateTree 主要解决编排行为。

---

# 35. 不要所有东西都做 Utility

固定确定流程：

```text
Dead
→ Respawn
```

不需要 utility。

脚本 Boss phase：

```text
HP < 50%
→ Phase2
```

也不需要 utility。

Utility 应用于“多个都合法、哪个现在更合适”的问题。

---

# 36. 不要所有东西都做 BehaviorTree

StateTree 已经能表达：

- 状态；
- transition；
- event；
- hierarchical active path；
- utility selector。

小动作不需要再套一个完整 BT。

只有 legacy / complex sequence 已被 BT 证明合适时再保留。

---

# 37. 性能预算

## Full Avatar

几十个近战敌人可以更频繁决策。

例如：

- combat dirty event；
- 5~10Hz fallback reevaluation；
- emergency immediate event。

不必固定 40Hz。

---

## Mass Agent

成千上万：

- signal/event driven；
- 0.2~2s bucket；
- LOD dependent；
- batch scorer；
- cheap fragments。

---

## Boss

数量很少。

允许更复杂 scorer 与 debug 数据。

---

# 38. 决策成本必须可观测

统计：

- decisions/sec；
- candidate scores/sec；
- average candidates；
- context build cost；
- scorer cost；
- StateTree transition count；
- aborted actions；
- stale callback rejects；
- oscillation count；
- promotion decision rebuild cost。

---

# 39. Oscillation 诊断

记录：

```text
Agent 101
12.000 Attack 0.71
12.050 Dodge 0.72 -> switch
12.100 Attack 0.73 -> switch
12.150 Dodge 0.74 -> switch
```

如果 1 秒切 20 次，不是“AI 很聪明”。

而是：

- hysteresis 太小；
- context noise；
- dwell 缺失；
- scorer domain 错；
- event storm。

---

# 40. StateTree Parameter 使用边界

Parameters 可作为配置/入口数据。

但 promotion/save 不应把 parameter binding path 当稳定身份。

稳定业务 state 仍在 LGF 自己的数据结构里。

---

# 41. Linked / External StateTree

适合复用：

- shared combat subtree；
- common locomotion behavior；
- pet command subtree；
- mount reaction subtree。

但需要版本化：

- asset identity；
- expected parameters；
- context schema；
- failure fallback。

---

# 42. Event-driven transition

GameplayTag event 可以作为：

- DamageReceived；
- TargetLost；
- PlayerCommand；
- AbilityEnded；
- SmartObjectInvalid；
- PromotionComplete。

Event payload 的业务数据仍要稳定可验证。

不要只靠“收到 Tag 就假设 target 指针仍然有效”。

---

# 43. Re-entry boundary

StateTree transition/task callback 也是前面框架轮次定义的 re-entry boundary。

当 Task 调用：

- Ability；
- Delegate；
- Blueprint；
- Spawn；
- async load；

回来后重新验证：

- Agent；
- Avatar generation；
- Decision generation；
- target；
- current state compatibility。

---

# 44. LGF 推荐模块边界

```text
LGF Foundation
  StableAgentId
  DecisionIntent DTO
  DecisionContext DTO
  UtilityScore DTO

LGF AI Core
  Pure Utility Kernel
  Decision History
  Command Priority

LGF StateTree Adapter
  StateTree nodes/tasks/evaluators
  target-version integration

LGF Mass Adapter
  Mass decision fragments
  promotion/demotion bridge

LGF GAS Adapter
  ability executor task
```

这样 UE API 改动不会穿透 Foundation。

---

# 45. 推荐最小实现顺序

1. 定义 DecisionIntent；
2. 定义 DecisionContext；
3. 做纯 scorer；
4. 做 debugger 输出；
5. 单 Actor StateTree adapter；
6. StateTree -> GAS Task；
7. cancellation/generation；
8. pet command priority；
9. promotion continuity；
10. Mass budget adapter。

不要一开始就做完整 MassStateTree + Utility + SmartObject + GAS 大一统系统。

---

# 46. R12 行为验收映射

## CPP-68

StateTree 已有 Utility selector 时，不额外建立 25ms Utility current-owner。

## CPP-69

Consideration/scorer 纯函数化、归一化、无副作用。

## CPP-70

StateTree Task active-path completion，不按 BT Sequence 解释。

## CPP-71

event-driven reevaluation + hysteresis/dwell/cooldown。

## CPP-72

selector 不应用 Authority gameplay effect。

## CPP-73

显式 interruption/cancel/generation，而非 Busy bool。

## CPP-74

debugger 显示候选、score breakdown、transition reason。

## CPP-75

Mass decision budget、低保真 context、数据导向评分。

## LGF-45

StateTree / Utility / GAS 单一高层 owner 分工。

## LGF-46

StateTree interruption 到 GAS exact cancel bridge。

## LGF-47

Mass promotion 时 stable DecisionState 连续，runtime StateTree 重建。

## LGF-48

宠物/坐骑玩家命令优先于 autonomous utility。

---

# 47. 与前十一轮的连接

## ActionRoguelike

继承其 Authority revalidation 与异步 generation 思想。

## Obsidian / RockInventory / Combee

延续“稳定业务身份 != runtime handle”。

## AyaDog GameplayFramework / Lyra

延续 stable owner vs replaceable Avatar。

## GASP-ALS-R / ALS-Refactored

StateTree 不进入 AnimThread；Animation 只是 execution/presentation。

## GASDocumentation / GASShooter

StateTree 选择 intent，不替代 PredictionKey/TargetData/GAS Authority。

## Mass R11

StateTree/Utility 成为低/高保真 Agent 的 Decision 层，而 Mass 仍是 simulation layer。

---

# 48. 最终 LGF 决策

默认架构：

```text
Sensors / Gameplay Events / Player Commands
                ↓
        DecisionContext Snapshot
                ↓
       StateTree Decision Owner
        ↙               ↘
Utility Selector      Deterministic State
        ↓
        DecisionIntent
                ↓
GAS / Mover / SmartObject / Domain Executor
                ↓
          Authority Validation
                ↓
        Replicated Canonical Result
```

大规模 Mass：

```text
Signals / Dirty Buckets
        ↓
Low Fidelity Context
        ↓
Budgeted Utility/StateTree Adapter
        ↓
Mass Intent Fragment
```

promotion：

```text
Stable DecisionState
→ Full Avatar
→ rebuild StateTree runtime
→ continue compatible intent
```

这套边界允许：

- 普通敌人；
- Boss；
- 城市居民；
- 远处生态 NPC；
- 跟随宠物；
- 可骑任意 NPC；
- NPC/Prop 变身；

共享统一 Decision 语义，同时不强迫所有实体支付同样 runtime 成本。

---

# 49. 本轮明确未证明的内容

本轮没有执行：

- UE5.7 UBT；
- UE5.8 UBT；
- StateTree Editor asset compile；
- PIE；
- Dedicated Server；
- MassStateTree 10k/50k benchmark；
- GAS + StateTree 实际 cancellation；
- pet/mount runtime；
- promotion/demotion runtime；
- Utility Consideration API 跨 5.7/5.8 compatibility test。

因此本轮交付的是：

**架构与 Skill 合同蒸馏，不是 LGF StateTree runtime 已实现。**

---

# 50. 维护检查表

任何未来 StateTree / Utility AI 改动前检查：

- [ ] 目标 UE 版本是否固定？
- [ ] 当前 StateTree/Consideration API 是否稳定？
- [ ] 是否只有一个 high-level Decision Owner？
- [ ] utility scorer 是否纯函数？
- [ ] numeric input 是否归一化？
- [ ] 是否有 hysteresis/dwell/cooldown？
- [ ] TasksCompletion 是 ANY 还是 ALL？
- [ ] async Task 是否有 generation？
- [ ] State Exit 是否精确 cancel GAS/Mover/claim？
- [ ] old callback 是否拒绝？
- [ ] player command 是否能压过 autonomous AI？
- [ ] Mass 低保真决策是否有预算？
- [ ] promotion 是否保存 stable intent 而不是 runtime frame？
- [ ] debug 是否能解释“为什么选这个动作”？
- [ ] scorer 是否有 perf counter？
- [ ] Authority result 是否仍由 GAS/domain system 决定？

