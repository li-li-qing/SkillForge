# LGF MassEntity / 大规模 AI Hybrid 合同

> 用于 LGameplayFramework 在大地图、大量 NPC、环境生物、宠物、坐骑、城镇人群中引入 MassEntity/MassGameplay 思路。目标是保持现有 Foundation、Pawn+Mover、GAS、GASP、Equipment、GameplayCamera 作为高交互主链，同时用 Mass 降低远景/群体 simulation 成本。

## 1. 不把 LGF 重写成 Mass Framework

LGF 已有：

- stable Request/Authority；
- Actor/Pawn Avatar；
- Mover；
- GAS；
- Equipment/Inventory；
- GASP/PSD/PSS；
- GameplayCamera；
- UI/Navigation；
- Save identity。

Mass 只解决“很多同类实体如何低成本模拟与表示”，不是替换上述全部系统。

推荐：

```text
LGF Foundation / Authority / Save
               |
        Stable Agent Registry
         /             \
 Mass Simulation      LGF Pawn/Actor
 low fidelity         high interaction
```

## 2. StableAgentId 是桥，不是 FMassEntityHandle

每个可跨 LOD/representation 存活的 NPC/宠物至少有：

```text
StableAgentId
DefinitionId
PersistentOwnerId (optional)
Persistent state key / save record
```

runtime：

```text
FMassEntityHandle
RepresentationGeneration
CurrentAvatarActor (optional)
CurrentMassEntity (optional)
```

都只是 cache。

禁止：

- Save `FMassEntityHandle`；
- Quest 直接引用 Actor pointer；
- Pet 存档用 ISM index；
- Hotbar/target lock 长期保存 Mass chunk/index。

## 3. NPC simulation tiers

### Tier A — Population aggregate

适用：

- 很远的城镇人口；
- 离线资源；
- 不需要逐实体位置。

只模拟数量/预算/时间。

### Tier B — Mass low fidelity

适用：

- 远处行人；
- 环境动物；
- 未交互宠物群；
- 战场背景兵。

保留 compact：

- AgentId；
- transform；
- movement intent；
- high-level state；
- health summary（如果业务允许）；
- LOD/representation；
- behavior/task compact data。

### Tier C — Mass + high-res Actor representation

适用：

- 靠近玩家但尚未进入完整战斗；
- 需要 skeletal representation /碰撞；
- 仍由 Mass 作为主要 simulation owner。

Actor 仍然是 ephemeral representation。

### Tier D — Full LGF Avatar

适用：

- 玩家目标；
- 正式战斗；
- 可骑乘；
- 复杂交互；
- Equipment/GAS；
- Mover/PhysicsControl；
- 精确碰撞/HitWindow；
- Quest critical NPC/Boss。

## 4. Promotion：Mass -> LGF Avatar

Promotion 是 Authority transaction，不是“SpawnActor 后把 transform 拷过去”。

### 4.1 预检

确认：

- StableAgentId 仍存在；
- 当前 RepresentationGeneration；
- 没有另一笔 promotion；
- Definition/FormData 可用；
- target world/level ready；
- server budget/actor pool 有容量；
- Agent 没有已 death/despawn。

### 4.2 建立 Avatar

```text
reserve promotion generation
 -> spawn/reuse Actor/Pawn
 -> bind StableAgentId
 -> apply canonical state
 -> InitState / PlayerState-or-Agent owner
 -> ASC/Mover/Physics/Anim ready
 -> apply compatible Equipment/Loadout
 -> camera/input only if locally controlled mount/player case
 -> set CombatOwner=Actor
 -> publish Actor representation ready
```

在 `Actor ready` 前：

- 新交互仍保持 Pending/拒绝；
- 不能同时让 Mass damage 与 Actor GAS 都消费；
- presentation 可以暂时继续 old representation。

### 4.3 generation

每次 promotion/demotion：

```text
RepresentationGeneration++
```

所有 async callback、spawn callback、asset callback、Actor event 带 generation；旧 generation 直接拒绝。

## 5. Demotion：LGF Avatar -> Mass

不要直接 Destroy Actor。

顺序：

1. fence 新 Combat/Interaction requests；
2. 等待/取消本 Avatar 的 transient Ability/HitWindow/RootMotion；
3. commit Health/Transform/Behavior/Equipment semantic state 回 canonical Agent state；
4. revoke Avatar-scoped GAS grants；
5. release Camera/Input/Linked Anim Layer/PhysicsControl；
6. set CombatOwner=Mass；
7. update Mass entity fragments；
8. release/pool Actor；
9. generation++；
10. publish representation change。

不保存：

- montage section；
- current AnimInstance pointer；
- Mover internal transient handle；
- Actor component pointers。

## 6. Combat routing fence

Hybrid 最大风险是双伤害。

Authority Agent record 至少保存：

```text
StableAgentId
RepresentationGeneration
CombatOwner = Mass | Actor
CurrentEntityHandle (runtime)
CurrentActor (runtime)
```

每个 damage command：

```text
DamageId
TargetStableAgentId
Expected/Observed Generation (optional candidate)
Source identity
Hit data
```

Authority：

1. resolve current record；
2. read current generation；
3. 选择唯一 CombatOwner；
4. idempotency check DamageId；
5. Actor path -> LGF GAS/combat；
6. Mass path -> server-only Mass damage queue/processor；
7. commit canonical health/death；
8. replicate/presentation。

旧 Actor callback 和旧 Mass command 在 generation mismatch 时拒绝。

## 7. Mass-only damage 的限制

纯 Mass 远景受击只有在玩法允许时使用：

- damage 规则简单；
- 不需要预测 Montage；
- 不需要 per-hit complex GAS effect stack；
- 不需要即时 equipment break/physics reaction。

如果 AoE 命中一个即将进入高保真战斗的 NPC，可以：

- Authority 在 Mass canonical state 扣血，然后 promotion 使用结果；或
- 先 promotion，再由 GAS 消费该 DamageId。

不能两边都算。

## 8. 玩家骑乘任意 NPC / 宠物

### 8.1 远处宠物

可以 Mass：

- 跟随简化；
- roam；
- population；
- low-rate behavior；
- ISM/low actor representation。

### 8.2 骑乘前必须 promotion

骑乘需要：

- Mover；
- collision；
- skeleton/AnimInstance；
- socket；
- retarget/linked layers；
- camera；
- input；
- ability compatibility；
- mount/dismount transaction。

所以不能“玩家 Attach 到 Mass ISM”。

### 8.3 Mount transaction

```text
Client RideIntent(PetId)
 -> Authority resolve PetId
 -> validate owner/range/state/cooldown
 -> ensure/promote Pet Avatar
 -> wait AvatarReady generation
 -> transfer movement/input role
 -> bind rider socket/animation
 -> switch GameplayCamera context
 -> grant mount-scoped abilities
 -> publish Mounted state
```

Dismount 反向撤销。

## 9. NPC 吸收/变身与 Mass

玩家吸收任意 NPC 时：

- 被吸收 NPC 的 `StableAgentId` 与玩家 FormData 是不同 identity；
- 不直接把玩家 ASC 迁到 Mass entity；
- 只把 NPC Definition/Form/appearance/ability recipe 复制为玩家的 shape recipe；
- 玩家仍保持 stable PlayerState/Agent + current LGF Avatar；
- 如果原 NPC 是 Mass，Authority 在吸收 transaction 中处理其 despawn/death/loot。

不要让一个 MassEntityHandle 成为玩家变身后的 owner identity。

## 10. StateTree 在 LGF 的位置

StateTree 可同时用于 Actor AI 与 Mass AI，但职责是 high-level behavior orchestration。

LGF 建议：

```text
Perception / world facts
 -> compact blackboard/state fragments
 -> StateTree selects intent
 -> Mass processor or LGF Ability/Request executes intent
```

不要在 StateTree Task 里直接：

- 改 Inventory truth；
- 发奖励；
- 绕过 GAS 扣血；
- 随意 Spawn/Destroy gameplay Actor；
- 每 tick 做大量 path query。

这些仍走 Authority services/commands。

## 11. ZoneGraph 与现有导航

ZoneGraph 适合：

- 城镇道路；
- 人群车流；
- 设计好的巡逻 lane；
- 大量 Agent 的 lightweight corridor。

NavMesh/Mover 仍适合：

- 高交互近战 NPC；
- 自由导航；
- 动态障碍；
- 玩家控制/坐骑；
- 精确 reachability。

Promotion 时可以把 Mass lane/target 转成 Actor initial navigation intent，但不要强制让高保真 Mover 继续以 Mass lane transform 为每帧真值。

## 12. SmartObject

可用于统一：

- 椅子；
- 采集点；
- 门；
- 工作台；
- 商店柜台；
- 坐骑点；
- NPC idle spot。

但 reservation != reward authority。

LGF interaction：

```text
SmartObject candidate/claim
 -> LGF Request/Authority revalidate
 -> execute domain action
 -> release claim
```

世界物品/奖励/库存仍由 LGF Authority。

## 13. Mass Signal 与 LGF EventBus

不要把两者混成同一条总线。

- **Mass Signal**：Mass entity wakeup；
- **LGF EventBus/GameplayMessage**：跨 subsystem/presentation notification；
- **Authority Request/Command**：业务 mutation；
- **FastArray/replication**：网络 state projection。

示例：

```text
Lootable corpse changed
 -> canonical Authority state
 -> signal nearby Mass scavengers "LootAvailable"
 -> Mass agents re-query facts
 -> winner sends Authority interaction request
 -> reward transaction
 -> GameplayMessage/UI projection
```

Signal 本身不携带 reward truth。

## 14. 5.7 -> 5.8 适配边界

LGF 目标当前以 5.7 为主，升级 5.8 时不能把 Mass 代码当普通 minor bump。

建立 adapter 层：

```text
LGF Mass Adapter Interface
 |- Entity create/destroy
 |- Fragment access/query
 |- Signal
 |- LOD
 |- Representation bridge
 |- Agent stable identity bridge
```

Mass API 变化封装在 adapter/module 内，不渗透 Foundation、Inventory、GAS、Save。

### 14.1 compile matrix

至少：

- UE5.7 Editor/Development；
- UE5.7 Server；
- UE5.8 Editor/Development；
- UE5.8 Server。

无法双版本同时维护时，文档明确支持版本，不写模糊 `UE5.x`。

## 15. Experimental dependency gate

MassGameplay、MassAI、MassCrowd、ZoneGraph 当前官方仍有 Experimental 标记。

如果采用：

1. 独立 Runtime module；
2. `.Build.cs` 不让 Foundation public API 暴露 Mass 类型；
3. feature flag / plugin optional path；
4. fallback Actor AI；
5. Save schema 不依赖 Mass handle；
6. Cook/Package/DS 目标验证；
7. 升级 UE 前重复成熟度审查。

这样即使未来 Epic 调整 plugin，也不会让整个 LGF 编译链锁死。

## 16. Representation 与 Equipment/GAS

Mass low fidelity 不需要每个 NPC 复制完整：

- Inventory UObject graph；
- Equipment Actor；
- GAS AbilitySpecs；
- skeletal sockets。

可存 compact semantic summary：

```text
WeaponDefinitionId
ArmorVisualSetId
CombatArchetypeId
Health/Level summary
```

Promotion 时从 Authority inventory/equipment source 构造高保真 representation。

重要 NPC 如果 inventory 是真实可掉落/可交易真值，inventory 仍存在 stable server store，不依赖是否有 Actor。

## 17. LOD policy 不只是距离

建议评分：

```text
importance = distance
           + visible
           + combat_target
           + quest_relevant
           + interacting
           + owned_pet
           + party_member
           + recently_damaged
           + server_budget
```

例如：

- 很远的玩家宠物但正在返回主人：Simulation 中；
- 近距离路人但被墙遮挡：Actor 不一定必要；
- Quest Boss 即使暂时没人看：不能降成 aggregate 丢掉战斗状态。

## 18. Network

Mass 客户端只消费 server projection。

LGF 不允许：

- remote client Mass StateTree 决定奖励；
- remote client Mass damage 回传最终数值；
- client promotion actor 成为 Authority；
- client 用 visible LOD 决定 server NPC 是否存在。

每个客户端可以看到不同 representation/ReplicationLOD，但 server StableAgent state 唯一。

## 19. JIP / reconnect

JIP 不能依赖历史 signal/event。

需要：

- server canonical Agent registry；
- 当前 Mass replicated state；
- current promotion Actor state；
- StableAgentId mapping；
- current RepresentationGeneration。

Client join：

```text
receive current entity/actor projections
 -> build AgentId lookup
 -> resolve representations
 -> UI/targeting subscribes future deltas
```

不重放全部旧 signal。

## 20. Performance acceptance

LGF Mass 试验必须与现有 Actor AI baseline 比。

场景至少：

- 1k / 5k / 20k low fidelity NPC；
- 20 / 50 / 100 promoted Actor；
- 1 / 4 / 16 clients（按目标项目规模调整）；
- 城镇 idle；
- 大量 moving crowd；
- signal burst；
- AoE 命中大量实体；
- promotion storm；
- World Partition load/unload。

记录：

- Server frame；
- worker utilization；
- Actor count；
- Mass entity/chunk/archetype；
- StateTree count；
- path/smart object queries；
- memory；
- net bytes/client；
- promotions/sec；
- dropped/duplicate command count。

## 21. 第一阶段推荐落地顺序

不要先迁战斗。

### Phase 1：只读环境人群 prototype

- Mass Agent stable ID；
- transform/movement；
- simple ZoneGraph；
- ISM representation；
- no Save/no Combat。

### Phase 2：Actor promotion

- high-res Actor；
- stable identity bridge；
- promotion/demotion generation；
- no GAS yet。

### Phase 3：交互

- SmartObject + LGF Request；
- Actor interaction route；
- JIP。

### Phase 4：战斗 bridge

- single canonical CombatOwner；
- DamageId；
- GAS promotion path；
- death/loot transaction。

### Phase 5：宠物/坐骑

- PetId；
- promotion on ride；
- Mover/Camera/Animation binding；
- Save/reconnect。

每一阶段都先做性能和失败注入，再继续扩展。
