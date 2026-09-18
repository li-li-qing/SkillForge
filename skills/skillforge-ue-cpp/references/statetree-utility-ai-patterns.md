# StateTree / Utility AI 决策与执行合同

> 用于 UE5.7/5.8 的 StateTree、AIController、GameplayStateTree、MassStateTree、Utility Scoring、BehaviorTree/GAS/SmartObject 组合设计。目标不是把所有 AI 都改成同一种树，而是明确“谁选择意图、谁执行行为、谁提交 Authority 业务结果”。

## 1. 先做版本与成熟度判断

StateTree 与 Utility AI 都属于容易被旧教程误导的领域。研究前先固定目标引擎、插件版本和 active code path。

### 1.1 当前证据层级

优先级从高到低：

1. 当前消费工程真实 UE 版本、Engine Source、启用插件和 Build.cs；
2. 同版本 Epic 官方 API / release notes；
3. 固定 commit 的当前样例；
4. 维护中的第三方插件；
5. 旧博客、旧视频、旧 fork；
6. stars、README 宣称、仓库更新时间。

### 1.2 UE5.8 StateTree 的当前能力

UE5.8 官方资料显示 StateTree 仍是通用 hierarchical state machine，当前核心能力包括：

- State / Group / Linked / LinkedAsset / Subtree；
- Enter Conditions；
- Tasks / Global Tasks / Evaluators；
- Transition / Event；
- Context Data / Parameters / Property Binding；
- 可配置 Task Completion；
- External StateTree；
- Starting State、Compiler Manager、debugger 等持续增强；
- Utility child selection：Highest Utility / Random Weighted by Utility；
- Utility Consideration、Weight、Response Curve。

但是不要把“功能存在”写成“全部 Production Stable”。当前官方 API 对 `FStateTreeConsiderationBase` 明确标记 **experimental / API expected to change**。因此：

```text
StateTree hierarchical orchestration
    = 当前可采用的框架能力

Utility Consideration API
    = 当前功能可用，但需要 adapter / version gate
```

尤其 LGF 当前主要目标仍包含 UE5.7，不能让 public Foundation API 直接暴露 5.8-specific Utility Consideration 类型。

### 1.3 5.7 与 5.8 不假设行为完全相同

UE5.7 API 已能看到 `FStateTreeConsiderationBase` 与 `EStateTreeTaskCompletionType`，但不应从“类名存在”推断 5.7 编辑器、selector、binding、debugger 与 5.8 完全一致。

对目标 UE5.7.4：

- 查实际 Engine Header；
- 查 StateTree.uplugin / GameplayStateTree；
- 编译自定义 Task/Condition/Consideration adapter；
- 打开 Editor 验证 selection behavior 与 binding UI；
- 不从 5.8 页面直接复制签名。

## 2. 默认架构：一个高层 Decision Owner

最容易出问题的做法是同时让：

- UtilityAIComponent；
- StateTree；
- BehaviorTree；
- GAS Ability；
- AIController Tick；

都“决定下一步干什么”。

默认规则：**同一 decision domain 只有一个高层 decision owner。**

推荐：

```text
Perception / canonical context
        |
        v
StateTree hierarchical decision owner
        |
        +-- Enter Conditions: 是否可进入
        +-- Utility/selector: 同级候选谁更优
        +-- Transition/Event: 什么时候重选
        |
        v
Decision Intent
        |
        +-- Movement request -> navigation/Mover owner
        +-- Attack request   -> GAS/Combat owner
        +-- SmartObject      -> reservation/execution owner
        +-- Animation        -> presentation owner
```

StateTree 负责 orchestration，不拥有所有 gameplay truth。

### 2.1 什么时候不需要第二套 Utility AI

如果需求只是：

> 在 `Attack / Heal / Flee / TakeCover` 四个 sibling State 中根据分数选一个

UE5.8 已有 Utility Selector/Consideration，应优先评估直接表达在 StateTree 中，而不是增加：

```text
UtilityAIComponent -> CurrentAction
StateTree           -> CurrentState
```

两个独立 current owner。

### 2.2 什么时候独立 Scorer 仍有价值

可以保留独立 utility scoring kernel 的情况：

- 多棵 StateTree 共用同一战略评分；
- Squad/Director 级决策；
- 需要对大量 Mass entity 做批量 POD 评分；
- 要跨 gameplay domains 统一预算；
- 目标版本 StateTree utility API 不稳定；
- 需要自定义数学模型、训练/自动调参或离线模拟。

但 scorer 输出应是：

```text
DecisionIntent
ScoreSnapshot
CandidateReason
Generation
```

而不是直接：

```text
ActivateAbility()
ApplyDamage()
MoveTo()
ClaimSmartObject()
```

## 3. Utility Score 必须是纯评估

### 3.1 Consideration 不提交副作用

评分阶段默认禁止：

- 扣血；
- 扣蓝/耐力；
- 消耗 cooldown；
- 增加仇恨；
- Claim SmartObject；
- 改 Inventory；
- Spawn Actor；
- Activate GameplayAbility；
- 写 canonical target owner。

原因：候选 A、B、C 都需要被“看一眼”。如果 CalculateScore(A) 已改变世界，B 的评分就受评估顺序污染。

正确：

```text
read snapshot/context
 -> normalize input
 -> response curve
 -> score composition
 -> choose winner
 -> command/task attempts commit
 -> Authority revalidate
```

### 3.2 Score 输入归一化

每个 consideration 至少明确：

- 原始输入域；
- clamp 范围；
- normalize 方式；
- response curve；
- weight；
- freshness；
- missing-data fallback。

例如：

```text
HealthRatio     [0..1]
DistanceMeters  [0..30] -> normalize [0..1]
TimeSinceHit    [0..8s] -> clamp
AmmoRatio       [0..1]
```

不要用“100米”“0.7血量”“2秒冷却”未经归一化直接相乘。

### 3.3 组合方式是设计合同

UE5.8 StateTree 当前 Utility Consideration 使用逻辑表达：

- AND 类似取较低分；
- OR 类似取较高分；
- 最终 normalized score 再乘 state Weight。

第三方 UtilityAIPlugin 则示范了 Multiply / Min / Max 一类组合。

无论采用哪一种，都要定义：

- empty list；
- 0 值；
- NaN/Inf；
- negative value；
- weight > 1；
- tie；
- missing sensor；
- stale input。

不能只说“utility score 0..1”然后允许最后 weight 无边界扩大却不记录。

## 4. Hysteresis：评分高一点不等于马上切换

Utility 系统最常见 bug 不是“分数算错”，而是状态抖动：

```text
Attack 0.51 -> Flee 0.52 -> Attack 0.53 -> Flee 0.54 ...
```

### 4.1 至少选择一种稳定策略

- `ScoreHysteresisThreshold`：新候选必须高出当前一定幅度；
- switch penalty：切换行为额外扣分；
- minimum dwell time：状态至少维持一段时间；
- cooldown：刚做过的行为临时降权；
- sticky intent：当前 action 保留 bias；
- interruption window：执行层不允许随时切。

`bohdon/UtilityAIPlugin` 中的 ScoreHysteresisThreshold 和 active score freeze 是值得吸收的机制，但不应直接照抄固定 Tick 架构。

### 4.2 FreezeScore 不是完整中断政策

“冻结当前分数”只解决当前 score 不下降，不能表达：

- 死亡必须立即中断；
- Stun 可以强制中断；
- 普通 Flee 要等攻击 cancel window；
- cinematic lock 不允许任何普通行为；
- mount 玩家输入比宠物 autonomous AI 优先。

所以需要独立 interruption policy。
在维护文档与调试输出中统一把这一合同称为 **Interrupt Policy**，避免被误解成一个 `bBusy` 布尔量。

## 5. Interruption 是异步协议

### 5.1 不用单个 bBusy

更完整的中断信息：

```text
CurrentActionId
CurrentGeneration
Interruptibility = None | Soft | Hard
AllowedInterruptReasons/Tags
MinimumDwellUntil
PendingCancel
ExecutionOwner
```

### 5.2 Abort 不等于已停止

当决策器要求切换：

```text
Decision wants Flee
 -> RequestCancel(Attack)
 -> Execution owner returns Accepted / Pending / Rejected
 -> wait for authoritative cleanup
 -> confirm old generation ended
 -> enter Flee
```

不要：

```text
Abort();
CurrentAction = NewAction;
```

然后假设 Montage、RootMotion、HitWindow、MoveTo 都已同步结束。

### 5.3 每次执行带 generation

异步回调至少校验：

```text
AgentId
DecisionGeneration
StateGeneration
ActionGeneration
AvatarGeneration (if relevant)
```

旧 action 的 Finish/Abort/MoveCompleted/AbilityEnded 不能结束新状态。

## 6. StateTree 的 Task 不是 BehaviorTree Sequence

### 6.1 Active path

StateTree 选择叶状态后，Root 到叶的 state path 同时 active。父状态与叶状态的 Task 可以同时活跃。

不要用下面的心智模型：

```text
Task[0] 完成
 -> Task[1]
 -> Task[2]
```

Task array 不是默认 sequence。

### 6.2 UE5.7/5.8 有 TaskCompletion 策略

当前 API 有 `EStateTreeTaskCompletionType`，至少包含：

- `ALL`：所有 participating tasks 完成；
- `ANY`：任一 participating task 完成。

UE5.8 `UStateTreeState` 还有 `TasksCompletion` / compiled `CompletionTasksControl`。

因此设计时必须显式回答：

> 这个 state 是 ANY 完成，还是 ALL 完成？

不要依赖旧文档里“第一个 Task 完成就触发 transition”的泛化描述，也不要假设 task order 等于 execution sequence。

### 6.3 真正 sequence 用状态表达

需要：

```text
Find Target
 -> Move To Target
 -> Use SmartObject
 -> Recover
```

优先：

```text
Parent: UseObject
  Child: Find
  Child: Move
  Child: Use
  Child: Recover
```

配合 Next / explicit transitions。

这样每一步：

- 生命周期可见；
- timeout 可见；
- debugger 可见；
- cancel 边界明确。

## 7. Task 的 Async Lifecycle

每个 Task 若启动：

- MoveTo；
- Gameplay Ability；
- timer；
- async trace；
- EQS；
- SmartObject claim/use；
- asset load；
- delegate；

必须在 Exit/Stop/Abort/Owner destruction 路径：

1. 保存 exact handle/id；
2. 请求取消；
3. unbind delegate；
4. invalidate generation；
5. late callback revalidate。

### 7.1 ExitState 不是业务提交点

不要因为 StateTree Exit 就默认：

- 技能成功；
- MoveTo 到达；
- SmartObject 使用成功；
- reward 已发。

Exit 可以来自：

- 成功；
- 失败；
- 外部 event；
- higher-priority transition；
- tree stop；
- avatar destroy。

业务 result 应由执行 owner 返回。

## 8. Event-driven 重选优先于固定高频 Tick

`bohdon/UtilityAIPlugin` 当前组件固定 `TickInterval = 0.025f`，每 Tick 对全部 action UpdateScore。这适合小规模样例，但不是通用生产默认。

### 8.1 触发来源

优先：

- perception target changed；
- damage received；
- health band changed；
- ammo/ability ready changed；
- SmartObject reservation changed；
- command arrived；
- StateTree Event；
- Mass Signal；
- decision context marked dirty。

### 8.2 连续量仍可低频采样

距离/角度/approach velocity 等连续量可按：

- 10 Hz；
- 5 Hz；
- 2 Hz；
- Simulation LOD；
- significance；
- current action needs；

而不是所有 AI 固定 40 Hz。

### 8.3 State custom tick rate

UE5.8 StateTree state 本身有 custom tick rate 相关能力；即使使用该能力也要按实际成本 profile，不能“设置了 0.1s 就自动高性能”。

## 9. 感知与昂贵查询做 Cache + Freshness

StateTree selection/utility 不能每次：

- `GetAllActorsOfClass`；
- EQS 全量；
- LOS trace N×M；
- Nav path sync query；
- 搜全部 SmartObject；
- 查询全场敌人。

正确是感知/空间系统产出：

```text
TargetStableId
LastSeenLocation
DistanceSq
LOSState
LastUpdatedTime
ThreatScore
Generation
```

StateTree/utility 读取该 snapshot。

Commit 时若状态安全敏感，再 Authority revalidate。

## 10. Decision / Execution / Authority 三层分离

### 10.1 Decision

负责：

- attack / heal / flee / cover / interact 选择；
- target preference；
- high-level route/state。

不负责：

- damage commit；
- inventory mutation；
- loot；
- ability cost；
- exact movement simulation。

### 10.2 Execution

执行 owner 例如：

- GAS Ability；
- Mover/Nav movement request；
- SmartObject interaction task；
- Equipment action；
- Animation presentation。

### 10.3 Authority

多人游戏：

- server canonical decision 或 server validates request；
- client AI presentation 不决定 reward/damage；
- Utility score 可以是 server-only；
- replicated current intent 只给表现需要的数据。

## 11. StateTree 与 GAS

推荐：

```text
StateTree Attack State
 -> Task: Request Ability by tag/semantic command
 -> GAS returns Started/Pending/Rejected
 -> Task tracks exact activation/generation
 -> AbilityEnded/Outcome event
 -> Task Succeeded/Failed
 -> StateTree transition
```

禁止：

```text
Consideration score > 0.7
 -> ApplyGameplayEffectToTarget()
```

### 11.1 Ability can outlive selection attempt

LocalPredicted/Authority ability 可能：

- server reject；
- cancel pending；
- montage end late；
- target lost；
- stun interrupted。

StateTree Task 只在当前 generation 下消费 outcome。

## 12. StateTree 与 SmartObject

职责：

```text
StateTree = decide to seek/use
SmartObject = discover + slot/claim/reservation
Task = execute interaction
Domain owner = reward/business effect
```

Utility consideration 可以评分：

- distance；
- availability candidate；
- need；
- risk。

但不能在 scoring 阶段 Claim。

## 13. StateTree 与 BehaviorTree

不要为了技术更新而无条件删除 BehaviorTree。

BehaviorTree 仍适合：

- 已成熟的大量 BT 资产；
- decorator/service/task 工具链；
- event-driven blackboard 逻辑；
- 现有团队熟悉度高。

StateTree 更适合：

- hierarchical state lifecycle；
- explicit transitions/events；
- reusable linked/external trees；
- task/context binding；
- 需要状态进入/退出语义的 orchestration。

迁移标准是维护成本、调试与性能证据，不是“StateTree 更新所以 BT 过时”。

## 14. StateTree Utility 与独立 UtilityAI 的选择

| 场景 | 推荐 |
|---|---|
| 单棵树 sibling state 评分 | StateTree Utility Selector（目标版本验证） |
| UE5.7/5.8 跨版本 Production | game-owned pure scorer + StateTree adapter |
| Squad/Director 战略 | 独立 scorer/service，再输出 intent |
| Mass 1万 entity | POD/batch scorer 或 MassStateTree，按 LOD 预算 |
| 复杂执行 | StateTree Task + GAS/Nav/SmartObject execution owner |
| Debug 调参 | 保留 score breakdown + response curve + transition trace |

## 15. UtilityAIPlugin 可吸收与拒绝项

固定样本：`bohdon/UtilityAIPlugin@0f49e0c6d420497d3102c3975601360dc120bf15`，MIT，最后提交 2025-04-06；未固定 EngineVersion，因此不作为 UE5.8 API authority。

### 15.1 可吸收

- `ScoreHysteresisThreshold`；
- action score freeze 作为稳定策略之一；
- GameplayTag require/ignore/query filter；
- ExecuteCount / LastExecuteTime / LastFinishTime；
- score element breakdown；
- debugger 展示候选与分数；
- decision 与单用途 BehaviorTree/Ability execution 解耦的总体思想。

### 15.2 不直接吸收

- 每个 AI 固定 0.025s 全 action scan；
- 每个 action 一个 UObject 作为 Mass 默认；
- `CalculateDataScore()` 当前 TODO 却宣称 data-driven 已完成；
- Blueprint score hot loop 作为大规模默认；
- `ConditionalBeginDestroy()` 作为一般 UObject lifecycle 模板；
- UtilityAIComponent 和 StateTree 同时拥有 CurrentAction/CurrentState 决策权。

## 16. Debug Evidence

AI “看起来蠢”必须能回答为什么。

### 16.1 Decision trace

至少可采样：

```text
AgentId
DecisionGeneration
Timestamp
Candidates[]
  Action/StateId
  FilterReason
  Considerations[]
    RawInput
    Normalized
    CurveOutput
    Weight
  FinalScore
CurrentScore
HysteresisThreshold
SwitchPenalty
Winner
TransitionReason
```

### 16.2 StateTree trace

关联：

- active path；
- enter condition；
- event；
- transition source/target；
- Task completion/abort；
- external tree；
- generation。

UE5.8 StateTree debugger 持续增强，可用当前 editor/runtime trace，而不要维护第二套完全独立的日志格式。

### 16.3 大规模调试

2 万 NPC 不保存全量逐帧 trace。

使用：

- selected AgentId；
- ring buffer；
- sampling；
- error-triggered snapshot；
- debug category toggle。

## 17. MassStateTree 边界

UE5.8 当前存在：

- `UMassStateTreeSchema`；
- `UMassStateTreeTrait`；
- `UMassStateTreeSubsystem`。

但它们属于 MassAI / MassAIBehavior 路线，而 MassAI 当前官方仍为 Experimental。

因此：

```text
MassEntity core
 -> 可独立评估
MassStateTree/MassAIBehavior
 -> feature gate + version adapter
```

不要让 LGF Foundation public API 暴露 `FMassStateTreeInstanceHandle` 作为业务 identity。

## 18. 2万实体决策预算

禁止：

```text
20,000 × AIController
20,000 × StateTreeActorComponent
20,000 × N UObject Actions
40 Hz full scoring
```

优先：

```text
Low LOD Mass fragments
 -> signal/dirty set
 -> batch score subset
 -> compact high-level intent
 -> only promoted Actor gets full StateTree/GAS
```

或验证目标版本 MassStateTree 的实例内存/调度成本后再采用。

### 18.1 Budget 维度

- entity count；
- candidates/action count；
- scoring frequency；
- trace/EQS frequency；
- state transition frequency；
- UObject/instance memory；
- debugger overhead；
- event storm；
- promotion spike。

## 19. Player/Pet 命令优先级

AI autonomous decision 不应直接被 UI 改内部 State。

命令统一成：

```text
CommandId
OwnerId
TargetAgentId
CommandType
TargetId/Location
IssuedAt
ExpiresAt
Priority
Generation
```

Authority 验证后写入 command/intent layer。

StateTree 可以：

- 根层 CommandOverride state；
- 高优先 EnterCondition；
- consideration bias；

但 UI 不直接 `SetCurrentState(Follow)`。

## 20. 验证矩阵

迁入 Production 前至少验证：

### 20.1 Logic

- same score tie；
- hysteresis；
- min dwell；
- hard interrupt；
- soft cancel pending；
- TaskCompletion ANY/ALL；
- linked/external tree；
- event before/after transition；
- stale sensor；
- late async callback。

### 20.2 Network

- dedicated server；
- listen host；
- remote client；
- JIP；
- avatar death/respawn；
- Mass promotion/demotion；
- ownership transfer；
- high latency ability cancel。

### 20.3 Performance

- 10 / 100 / 1k / 10k agents；
- 4 / 12 / 32 candidates；
- 40Hz vs 10Hz vs event-driven；
- Blueprint vs native scorer；
- Actor StateTree vs Mass low-fidelity；
- debugger off/on。

## 21. Review Checklist

在批准 StateTree/Utility AI 设计前回答：

1. 当前目标 UE 版本？
2. StateTree utility API 在该版本是否已验证？
3. 谁是唯一 high-level decision owner？
4. score 是否纯查询？
5. 如何 normalize 和组合？
6. tie/hysteresis/min dwell 怎么处理？
7. interruption 与 async cancel 怎么处理？
8. Task Completion 是 ANY 还是 ALL？
9. expensive sensor 的 freshness 在哪？
10. gameplay commit 由谁 Authority 执行？
11. Mass/Actor 两层是否共享 stable identity？
12. 如何 debug “为什么选了它”？
13. 规模和频率是否 profile？
14. Experimental API 是否隔离在 adapter 后？
