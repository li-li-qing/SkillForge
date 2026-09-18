# LGF AI 决策编排：StateTree / Utility / GAS / Mass

> 用于 LGameplayFramework 的 NPC、Boss、宠物、坐骑、Mass promotion Avatar 引入 StateTree / Utility scoring。保持 LGF Foundation、Authority、GAS、Mover、GASP、Inventory/Equipment、StableAgentId 为业务主链；AI 只选择意图，不越权成为第二个 Gameplay Authority。

## 1. LGF 的默认 Decision Stack

### 近战范围内却反复 Chase/Attack

旧 LGF 战斗动画案例中，AI Profile 攻击距离、Ability 激活距离、Controller 的 Strike 常量与寻路 Acceptance Radius 各自演化，造成“范围内 → 停顿 → 追击”。这是诊断线索，不是未读当前源码就认定的根因。

对同一目标/服务器帧记录距离的测量口径（中心或表面）、EnterRange、ExitRange、寻路到达半径、LOS/朝向、能力激活结果与回退原因。若确证同一攻击规则存在相互冲突的阈值，统一权威进入距离，并在需要时设一个命名明确的退出迟滞；不同能力合法射程不必强行变成同一常量。Acceptance Radius 只负责寻路到达，不暗中变成第二个攻击门槛。

“必须目标静止才攻击”是独立玩法策略，不是默认修复。分别测试移动/静止目标、距离边界往返、冷却或阻挡、路径到达；不要通过扩大所有攻击距离或忽略 Ability 拒绝使日志看似稳定。来源为旧 combat-animation-failure-modes 参考，本次技能维护未运行 AI。

推荐：

```text
Perception / Agent Context / Player Command
                 |
                 v
          Decision Context
                 |
                 v
       StateTree Decision Owner
       /       |        \
 EnterCond   Utility   Transition/Event
                 |
                 v
           DecisionIntent
      /           |           \
 Movement       Combat       Interaction
   Mover/Nav       GAS       SmartObject
      \            |             /
               Authority
                 |
          Canonical Agent State
```

### 核心规则

- StateTree 选择“现在应该做什么”；
- Utility 决定“多个可行候选哪个更值得”；
- GAS 决定技能能否启动、成本、预测、命中与结果；
- Mover/Nav 拥有 movement truth；
- SmartObject 拥有 reservation 生命周期；
- Inventory/Equipment 拥有物品真值；
- Stable Agent record 拥有可跨 representation 的高层 AI 状态。

禁止 StateTree / Utility 直接成为第二个 damage/inventory/equipment authority。

## 2. 版本策略：5.7 主线 + 5.8 适配

LGF 当前已有 UE5.7 目标，未来可能升级 5.8。

### 2.1 StateTree core

StateTree hierarchical state/transition/task/context 可以作为 adapter 后的决策框架。

### 2.2 Utility consideration

5.8 当前有原生 Utility Selector/Consideration，但 consideration API 官方仍标 Experimental。

因此 LGF 不在 Foundation public header 直接暴露：

```text
FStateTreeConsiderationBase
EStateTreeStateSelectionBehavior 5.8-only assumption
```

而建立 game-owned decision model：

```text
FLGFDecisionCandidate
FLGFDecisionScore
FLGFDecisionIntent
ILGFDecisionScorer / service
```

StateTree adapter 负责把 score/context 映射到目标版本。

这样：

- 5.7 可以用自定义 Evaluator/Condition/Task/selector adapter；
- 5.8 可以选择 native Utility Consideration；
- Mass 可以复用同样 score kernel 做 batch；
- Save 不依赖 StateTree runtime type。

## 3. 一个 Agent 只有一个高层 Decision Owner

### 3.1 高保真 LGF Avatar

通常：

```text
AIController / AgentBrain
 -> StateTree
 -> intent
```

不要同时运行：

```text
StateTree CurrentState
UtilityAI CurrentAction
BehaviorTree ActiveNode
Pawn Tick switch-case
```

四套系统竞争。

### 3.2 允许组合，但所有权清晰

例如 StateTree Attack 状态内部执行单用途 BehaviorTree：

```text
StateTree owns high-level state
 -> BT owns local tactical sequence only while task active
```

或：

```text
Squad Utility Director owns squad intent
 -> individual StateTree consumes assigned intent
```

此时不是两个同层 owner。

## 4. Decision Context 是 Snapshot，不是对象漫游

StateTree/utility 读取统一 context：

```text
StableAgentId
RepresentationGeneration
HealthRatio
ResourceRatio
TargetStableAgentId
TargetDistance
LOSState
ThreatBand
RecentDamage
AbilityReadinessSummary
CurrentCommand
CurrentIntent
LastAction timestamps
SensorFreshness
World/Combat phase
```

### 4.1 不让 Consideration 每次扫世界

禁止每个 score：

- GetAllActors；
- sync EQS；
- sync nav path；
- 全场 Threat TMap 遍历；
- 直接询问每个 AbilitySpec。

这些由 sensor/cache/service 更新 context。

### 4.2 Freshness

每个可过期数据带：

```text
UpdatedAt
Generation
ValidUntil / MaxAge
Source
```

决策可以拒绝 stale target，而不是把 2 秒前 LOS 当当前事实。

## 5. LGF DecisionIntent

推荐逻辑字段：

```text
DecisionId / Generation
AgentId
IntentType
TargetAgentId / TargetLocation
Source = Autonomous | PlayerCommand | Squad | Script
Priority
Score / Reason (debug)
IssuedAt
ExpiresAt
```

运行时指针只是 cache。

### 5.1 Intent 不等于业务成功

```text
Intent = Attack(TargetA)
```

不代表：

- Ability 已激活；
- hit accepted；
- damage committed；
- TargetA 还活着。

Task 仍要等待 execution owner result。

## 6. StateTree Attack Task -> GAS

推荐流程：

```text
Enter Attack State
 -> Resolve Target StableAgentId
 -> Request Ability/Combat command
 -> GAS Authority/Prediction checks
 -> Started / Pending / Rejected
 -> Task stores activation/generation
 -> Combo/HitWindow executes
 -> Ability outcome
 -> Task Succeeded/Failed
 -> transition
```

### 6.1 复用已有 LGF identity

与多刀刃/连招规则结合：

```text
Agent DecisionGeneration
AvatarGeneration
Ability Activation identity
Combo Sequence
Section
HitWindowGeneration
PartId
DamageId
```

AI Task 不能用一个 bool `bAttacking` 替代这些身份。

## 7. AI Interrupt 与 GAS Cancel Bridge

场景：五段连招中 Utility 发现 Flee 更高。

### 7.1 Decision 不直接切走

先判断：

```text
CurrentAction InterruptPolicy
Current Section cancel window
Incoming Reason/Priority
Hard override? (Death/Stun)
```

### 7.2 RequestCancel

```text
StateTree wants Flee
 -> Request GAS cancel
 -> AcceptedImmediate | Pending | Rejected
```

- Immediate：cleanup 后转 Flee；
- Pending：进入 PendingCancel 或维持 Attack state 等 outcome；
- Rejected：保持 current state，设置 retry/event。

### 7.3 Movement 单 owner

Flee MoveTo 不能与：

- attack RootMotion；
- Mover layered move；
- traversal；
- mount rider movement；

同时写 capsule movement truth。

## 8. Utility Scoring Kernel

LGF 自己的 scorer 应是纯数据函数，便于 5.7/5.8/Mass 复用。

例如：

```text
Input: FLGFDecisionContext + CandidateDefinition
Output: FLGFDecisionScore
```

`FLGFDecisionScore` 可包含：

```text
FinalScore
RawInputs[]
NormalizedScores[]
Weights[]
FilterReason
```

### 8.1 Scorer 禁止

- ActivateAbility；
- modify threat；
- Claim SmartObject；
- write movement；
- award reward；
- mutate Inventory。

### 8.2 Curves 与 DataAsset

可把调参数据放 DataAsset：

```text
Health response curve
Distance response curve
Threat curve
Cooldown bias
State switch penalty
```

算法在 C++，数据可设计师调整。

## 9. Hysteresis / Dwell / Cooldown

推荐统一在 Decision policy 层处理，而不是每棵 StateTree 私自复制。

记录：

```text
CurrentIntent
CurrentScore
EnteredAt
MinimumDwell
LastActionTime[ActionId]
ActionCooldown
SwitchPenalty
```

### 9.1 Hard override

以下通常忽略 minimum dwell：

- Dead；
- Disabled；
- hard Crowd control；
- owner command requiring immediate stop；
- critical traversal safety。

具体按项目设计，不写死。

## 10. Player Command 与 Autonomous AI

宠物命令例如：

- Follow；
- Stay；
- Attack Target；
- Passive；
- Return；
- Mount。

客户端只发 intent：

```text
PetCommandId
OwnerId
PetAgentId
CommandType
TargetAgentId/Location
Generation
```

Authority revalidate：

- ownership；
- control capability；
- distance；
- pet current state；
- representation generation；
- target validity。

### 10.1 Command priority

推荐：

```text
Death/Disable
> Explicit owner hard command
> Script/Quest override
> Squad order
> Autonomous Utility
> Idle fallback
```

实际项目可以调整，但必须只有一份政策。

### 10.2 Command 不直接 Set StateTree current state

命令进入 canonical command layer，再由 StateTree 通过：

- root CommandOverride state；
- Enter Condition；
- event；
- utility bias；

消费。

这样 StateTree asset 可以替换，网络 command protocol 不变。

## 11. Mass -> LGF Promotion 的 Decision Continuity

低保真 Mass NPC 不需要保存完整 StateTree runtime。

### 11.1 Canonical decision continuity

保存：

```text
StableAgentId
HighLevelIntent
TargetStableAgentId
LastAction times
Cooldowns
Need/Threat summary
DecisionSeed (if needed)
Command
```

不保存：

- active StateTree node pointer；
- UStateTreeComponent pointer；
- UtilityAction UObject；
- Task instance handle；
- local MoveTo handle。

### 11.2 Promotion

```text
Mass owns decision
 -> fence Mass decision writer
 -> copy canonical decision context
 -> spawn/reuse LGF Avatar
 -> initialize AIController/StateTree
 -> map stable DecisionState into target-version **StateTree parameters** / Context
 -> choose starting state / reselect
 -> CombatOwner=Actor
 -> StateTree becomes decision owner
```

### 11.3 Demotion

```text
fence new high-fidelity requests
 -> finish/cancel transient tasks
 -> write high-level intent/target/cooldowns back
 -> stop StateTree
 -> invalidate DecisionGeneration
 -> release AIController/Avatar runtime
 -> Mass resumes low-fidelity decision
```

## 12. 不要求 bit-for-bit 恢复 StateTree

目标是玩家可见行为连续：

- NPC 仍在追同一个敌人；
- 逃跑 cooldown 没被重置；
- 宠物 Follow 命令没丢；
- 刚用过大招不会 promotion 后立刻再用。

不需要恢复：

- StateTree editor state index；
- internal runtime frame；
- exact task local timer。

## 13. Mass 低保真 Utility

对于 1 万+ Agent：

```text
Mass Signal / Dirty Set
 -> batch scorer Processor
 -> compact IntentFragment
 -> low-frequency State/Intent execution
```

不要给每个 Mass entity：

- AIController；
- UStateTreeComponent；
- UObject UtilityAction array；
- 25ms Tick。

如果采用 `UMassStateTreeTrait`，要明确它属于 MassAI experimental 路线，并在目标 5.7/5.8 重新验证内存/调度成本。

## 14. Boss / 少量复杂 NPC

Boss 数量少、行为复杂时不强求 Utility：

- hierarchical StateTree；
- explicit phases；
- script/encounter state；
- GAS abilities；

往往比几十个 utility consideration 更容易设计与调试。

Utility 更适合“多个都合理，需要自然偏好”的选择，而不是取代所有脚本逻辑。

## 15. SmartObject / Interaction

StateTree 只选择“我要去坐椅子”。

执行：

```text
Find candidate
 -> Authority reservation/claim
 -> Move
 -> Use
 -> release claim
 -> Task outcome
```

如果中断：

- release exact claim handle；
- generation fence；
- 不让新 state 继承旧 reservation。

## 16. Debugging

每个 Agent 可选择开启 ring trace：

```text
DecisionGeneration
Current State path
Candidates + score elements
Winner reason
Current command
Transition reason
Execution request id
Execution outcome
Interrupt reason
Target freshness
```

AI Debugger/StateTree Debugger 与 LGF Combat diagnostics 关联 AgentId。

### 16.1 不只打印 CurrentState

错误分析至少区分：

```text
Decision chose Attack correctly
but GAS rejected cooldown
```

vs

```text
Decision incorrectly chose Attack because LOS cache stale
```

否则会修错层。

## 17. Save / Load

长期 Save 只保存业务层：

```text
StableAgentId
Persistent behavior flags
Command mode
Long cooldown timestamps (if design requires)
Pet stance
Quest/script state
```

不保存 StateTree runtime instance data，除非某个特定系统明确需要并有 schema/migration。

Load：

```text
restore canonical state
 -> create representation
 -> build DecisionContext
 -> start StateTree
 -> select current appropriate state
```

## 18. Avatar Rebind

变身/骑乘/Respawn：

1. stop/fence old DecisionGeneration；
2. cancel old Task handles；
3. unbind old perception/movement/ability delegates；
4. switch Avatar；
5. init Mover/GAS/GASP/Equipment；
6. rebuild context adapter；
7. start/reselect StateTree；
8. publish new generation。

旧 Avatar `MoveCompleted` / AbilityEnded / Montage callback 不能推进新 Avatar StateTree。

## 19. StateTree / Utility API 隔离

建议 LGF 模块边界：

```text
LGameplayFoundation
  no StateTree experimental utility type in public API

LGameplayAI
  DecisionIntent / Context / Scorer interfaces

LGameplayAIStateTreeAdapter
  target-version StateTree bindings/tasks/considerations

LGameplayMassAdapter
  optional Mass scoring/state bridge
```

如果项目目前模块命名不同，保持现有目录/依赖，不为了文档机械新增模块；重点是依赖方向。

## 20. Verification Matrix

### 20.1 Decision

- same score；
- switch threshold；
- min dwell；
- hard interrupt；
- owner command override；
- stale target；
- target death；
- ability rejected；
- cancel pending；
- TaskCompletion ANY/ALL。

### 20.2 Avatar lifecycle

- death/respawn；
- NPC transform；
- pet mount/unmount；
- possession transfer；
- Mass promotion/demotion；
- travel/load。

### 20.3 Network

- DS；
- Listen Host；
- remote client；
- latency/loss；
- JIP；
- duplicated command；
- old generation callback。

### 20.4 Performance

- 10 complex Boss AI；
- 100 full Pawn AI；
- 1k mixed；
- 10k Mass low-fidelity；
- event-driven vs fixed scorer tick；
- StateTree debugger/AI trace off/on。

## 21. 迁移策略

若当前项目已有 BehaviorTree/AIController：

1. 不删除；
2. 选一个低风险 NPC archetype；
3. 建 DecisionContext adapter；
4. 把 high-level state 迁 StateTree；
5. 执行层继续复用现有 GAS/Move/BT task；
6. 运行相同行为回放与 perf；
7. 有收益再扩展。

若当前已有 UtilityAI：

1. 保留 scoring curves/weights/debug data；
2. 把 scorer 改成 pure kernel；
3. 去掉直接 execution；
4. StateTree 作为 orchestration owner；
5. 对 UE5.8 native Utility Consideration 只做 adapter；
6. 等目标版本验收后决定是否替换 adapter。

## 22. Review Checklist

- [ ] 唯一高层 Decision Owner 明确。
- [ ] Utility score 无副作用。
- [ ] score normalization / curve / weight 可追踪。
- [ ] hysteresis / dwell / cooldown 有统一政策。
- [ ] TaskCompletion ANY/ALL 明确。
- [ ] interruption 是 async contract，不是 bool。
- [ ] GAS/Movement/SmartObject 仍拥有执行真值。
- [ ] StableAgentId 与 StateTree runtime 分离。
- [ ] Mass promotion/demotion decision continuity 有定义。
- [ ] Player pet/mount command 走 Authority command layer。
- [ ] 5.7/5.8 StateTree adapter 版本边界清楚。
- [ ] Experimental Utility/MassAI 不进入 Foundation public ABI。
- [ ] Debug trace 能解释“为什么选它/为什么没执行成功”。
- [ ] 性能由目标规模 profile，而不是固定 25ms tick。
