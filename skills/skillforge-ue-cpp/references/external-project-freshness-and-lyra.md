# 外部 UE 项目时效性门与现代 Lyra 模式

用于从 GitHub、Epic Sample、社区样例和旧生产项目吸收 UE 架构时，先判断**技术时效性**，再决定是否写入长期 Skills。项目“能编译”“Star 很多”“作者知名”都不是现代性证据。

本参考同时记录 Lyra 作为持续更新官方样例提供的现代框架模式。Lyra 不是模板代码生成器，也不是必须整套采用的运行时依赖。

## 1. 先做技术时效性分级

每个外部项目在进入 Skills 前先标一类：

| 等级 | 含义 | 允许写进 Skills 的内容 |
|---|---|---|
| `Current` | 目标 UE 版本接近当前项目，近期仍维护，关键 API 与当前源码/官方文档一致 | 机制 + 经核实的当前接口 |
| `Stable-but-old` | 项目较旧，但核心机制在当前 UE 仍成立 | 机制；具体 API 必须标“重新核对” |
| `Historical` | 设计思想有价值，但关键 API、生命周期或系统已被 UE 后续版本替代 | 历史意图、迁移线索、反例 |
| `Reject` | 已知存在严重架构债、权限问题、版本冲突，或现代方案明显更优 | 仅记录“为什么不采用” |

至少记录这些证据：

1. 固定仓库 commit/tag；
2. license；
3. 最后维护时间；
4. 项目声明的 UE 版本；
5. `.uproject` / `.uplugin` / `Build.cs` / release note 的实际版本证据；
6. 当前目标 UE 官方文档；
7. 当前引擎源码或用户真实项目的对应实现；
8. 后续版本是否明确修复/重写过旧模式；
9. 是否有新的替代技术；
10. 目标项目是否真的需要这个子系统。

### 不允许用作现代性结论的证据

- Star 数；
- Fork 数；
- README 截图；
- “Epic/大厂项目里出现过”；
- 某篇旧博客仍能被搜索到；
- 旧蓝图节点还没有被删除；
- 代码能够在旧 UE 分支编译。

## 2. 版本冲突的 Authority 顺序

当不同来源冲突时，默认优先级：

1. 用户当前实际工程与其明确约束；
2. 当前目标 UE 分支源码；
3. 与目标版本匹配的 Epic 官方文档；
4. 同版本官方 Sample；
5. 近期维护的高质量社区工程；
6. 老版本官方 Sample；
7. 老版本社区工程/教程。

旧来源可以解释“为什么这个系统最初这样设计”，但不能覆盖当前实现。

## 3. Lyra 是最适合做版本迁移训练的样例

Lyra 会随 UE 大版本更新。Epic 的升级文档明确建议：升级 UE 时，同时下载对应的新 Lyra，并比较旧、新版本如何处理引擎 API 与框架变化。

因此研究 Lyra 时不能写“Lyra 一直这样做”，而应写：

- **哪一个 UE 版本开始这样做**；
- 旧版本做法是否已被 Epic 自己替换；
- 这条机制是否仍存在于当前文档；
- 目标项目要吸收机制还是类体系。

### 3.1 典型案例：Pawn Init State

Lyra 5.0 的 Pawn 初始化早于新的 Init State 系统。Epic 在 5.1 将 `LyraHeroComponent` / `LyraPawnExtensionComponent` 的初始化流重写为 `IGameFrameworkInitStateInterface` + `GameFrameworkComponentManager` Init State，明确目的就是修复网络复制竞态，并提高 feature component 扩展能力。

所以：

- 5.0 的固定初始化顺序属于 `Historical`；
- 5.1+ 的显式 readiness state 属于 `Current mechanism`；
- 具体类名与 API 仍需按目标 UE 版本核对。

## 4. 模块化 Pawn 不假定 BeginPlay 顺序

当一个 Pawn 需要等待：

- PawnData；
- Controller/Authority；
- PlayerState；
- ASC；
- InputComponent；
- GameFeature 注入组件；
- Camera/Input/Equipment/Animation 等 feature；

不要把这些依赖写成 `BeginPlay()` 里固定顺序调用。

推荐状态语义：

- `InitState.Spawned`：Actor/feature 已生成，完成基础注册；
- `InitState.DataAvailable`：本 feature 所需复制/加载数据都已经可用；
- `InitState.DataInitialized`：数据已消费并完成本 feature 的绑定/授予；
- `InitState.GameplayReady`：对外可安全交互。

这些名字来自 Lyra 5.1+；其他项目可以使用等价状态，不需要复制类名。

### 4.1 规则

- readiness 是**条件集合**，不是时间延迟；
- `CheckDefaultInitialization()` 类操作允许多次触发，因此必须幂等；
- 每个 feature 只知道自己的依赖；
- 一个 feature 到达 ready 不代表所有 feature ready；
- 解绑同样有状态与 generation；
- 迟到 callback 重新验证当前 world/session/avatar generation；
- 调试输出“卡在哪个依赖”，不能只输出 `Not Ready`。

## 5. PlayerState ASC 与可替换 Avatar

Lyra 当前官方文档仍采用：稳定 GAS state 可放在 PlayerState，当前 Pawn 作为 Avatar。

这允许：

- Attribute/GameplayEffect 跨死亡或 Pawn 变化保留；
- Pawn-specific AbilitySet 在 Pawn 生命周期内授予，离开 Pawn 时撤销；
- Equipment 或 GameFeature 作为另一类 grant source；
- Avatar 在获得有效 possession 前不激活需要 Avatar 的 OnSpawn ability。

### 5.1 必须区分两种 grant

**Persistent player grant**：

- 账户/角色长期能力；
- 长期 AttributeSet；
- 跨 Pawn 保留的 Effect。

**Pawn-scoped / source-scoped grant**：

- PawnData AbilitySet；
- 当前装备；
- 当前 Experience/GameFeature；
- 当前形态专属能力。

后者必须保存 exact `GrantedHandles` / spec handles，由 grant source 精确撤销。

不要因为 ASC 在 PlayerState 就让所有 ability 永久存在。

## 6. PawnData 是组合描述，不是真值仓库

Lyra 的 PawnData 语义可抽象为：

- Pawn class；
- AbilitySets；
- InputConfig；
- TagRelationshipMapping；
- 默认 Camera Mode；
- 其他构造当前 Avatar 的静态配置。

它适合作为 DataAsset 配方，不应该存：

- 当前生命值；
- 当前装备实例；
- 当前 prediction state；
- 当前输入按下状态；
- 当前 Avatar generation；
- 运行时网络真值。

对变身/骑乘系统，这种配方模型可以映射成 FormData/MountData，但不要把 LyraPawnData 变成万能对象。

## 7. Experience 是异步 readiness barrier

Lyra Experience 的关键价值不是“高级 GameMode”，而是：

1. 选中一组玩法配置；
2. 异步加载所需 GameFeature Plugins 与 Primary Assets；
3. 执行 Action Sets；
4. 直到完整 Experience loaded 才宣布玩法 ready。

因此：

`BeginPlay != Gameplay Ready`

### 7.1 正确边界

异步 load callback 应验证：

- 当前 World 仍存在；
- 仍然是同一 match/session；
- Experience request generation 未过期；
- feature plugin 状态符合预期；
- 依赖的 Pawn/Input/UI 不被旧请求重复注入。

### 7.2 Feature activation 必须可逆

GameFeature/Experience 可能：

- 加组件；
- 加 AbilitySet；
- 加 Input Config/Binding；
- 加 HUD layout/extension；
- 注册消息监听；
- 注册资源路径。

所有这些都需要 handle/source identity 和对称 remove。

## 8. GameFeatures 当前仍不是“无风险默认”

当前 UE 5.8 GameFeatures API 页面仍将其标成 Beta，并提示 shipping caution。

所以：

- “Lyra 使用 GameFeatures”只证明 Epic sample 的组合方式；
- 不自动证明你的商业项目必须接受这个 Beta 依赖；
- 在目标平台、补丁策略、打包、版本升级流程不允许时，可以保留静态模块 + DataAsset composition；
- 如果真正需要 DLC/mod/玩法包按需启停，GameFeatures 才有更明显收益。

必须在架构决策记录中写清：

- 动态 feature 的实际收益；
- 不采用时的替代方案；
- 平台支持与 build pipeline；
- feature unload 是否真的需要；
- save/version compatibility。

## 9. Inventory 与 Equipment 是不同生命周期域

当前 Lyra 官方 5.8 文档仍强调：

- Inventory Item：只要所有者拥有它，实例长期存在；
- Equipment：从 Inventory 中取出的“正在使用”状态，只在 equipped 时创建；
- Equipment 可以生成可见 Actor、改变 UI、授予 active/passive Abilities；
- Unequip 后这些装备期副作用应消失。

可抽象成：

```text
Persistent Item Identity/State
        ↓ Equip request
Applied Equipment Generation
        ├─ spawned actors
        ├─ ability grants
        ├─ socket / trace bindings
        ├─ linked animation layers
        ├─ reticle / device properties
        └─ presentation listeners
```

Unequip 只撤销 applied generation，不销毁长期 Item identity。

### 9.1 不把 Lyra Inventory 当复杂 ARPG 上限

Lyra 是 sample/gameplay framework，不代表其 Inventory 就适合：

- Diablo grid；
- 大量堆叠物；
- shared stash；
- nested containers；
- affix persistence；
- 多容器 transaction。

这些继续使用项目现有容器规则。

## 10. Input 属于 Feature + UI 路由组合

Lyra 当前输入模式的可迁移语义：

- GameFeature 注册其 Input Config/Mapping；
- Enhanced Input 处理当前激活 Mapping Context；
- Ability Input 使用 InputTag 关联 AbilitySpec；
- CommonUI/Action Router 决定 UI 层是否截获输入；
- feature deactivate / Avatar detach 时移除相应注册。

### 10.1 禁止的反模式

- 全部 IMC 永远激活；
- 所有 InputAction 硬编码在 PlayerController switch；
- Widget 和 Pawn 同时认为自己拥有 input mode；
- GameFeature unload 后 binding 仍存活；
- Avatar swap 时重复 AddMappingContext；
- InputTag 通过每帧全表线性扫描能力列表。

## 11. CommonUI、Enhanced Input、Ability Input 是三层

概念上：

```text
Physical Input
    ↓
CommonUI / Action Router
    ├─ consumed by UI
    └─ routed to Game
            ↓
Enhanced Input Mapping Contexts
            ↓
Input Action / Input Tag
            ↓
Domain Command / Ability Spec
```

不要把 CommonUI 的 input mode、Enhanced Input 的 context、GAS 的 Ability input 混成一个 owner。

## 12. 官方 Sample 也要“选择性吸收”

Lyra 的优势是：

- 持续随 UE 更新；
- 大量多人/跨平台边界；
- GameFeature/ModularGameplay/GAS/CommonUI 等系统真实组合；
- 可以观察 Epic 如何修复旧版本架构。

但不应整套复制，因为：

- sample 需要展示很多 UE 功能，因此复杂度并非所有项目都需要；
- 部分系统仍是 prototype/sample scope；
- GameFeatures 当前仍有 Beta 标记；
- 你的项目可能已有成熟 Inventory、Mover、Camera、UI、Save 等系统；
- 直接引入会产生两套 ownership/lifecycle。

## 13. 对外部项目的固定蒸馏模板

以后每个项目报告至少包含：

### A. Snapshot

- Repo/来源；
- Commit/tag；
- License；
- 声明 UE 版本；
- 实际 descriptor/build 证据；
- 最后维护时间。

### B. Freshness Classification

- `Current` / `Stable-but-old` / `Historical` / `Reject`；
- 当前 UE 对照证据；
- 已知替代方案。

### C. Accepted Mechanisms

只写跨项目仍成立的机制。

### D. API Recheck Required

列出所有不能直接复制的类名、宏、函数签名、配置键。

### E. Rejected Patterns

写明为什么拒绝，避免未来 Agent 再次“重新发现”旧坑。

### F. Target Mapping

说明映射到当前项目哪个 ownership/lifecycle，不创建平行框架。

### G. Verification

至少覆盖：

- build/UHT；
- Listen Host；
- Remote client；
- JIP/reconnect；
- unload/reload；
- Avatar swap；
- async late callback；
- packaged build（若涉及 GameFeature/AssetManager/online）。

## 14. 新仓库也必须做 active-code evidence 分级

维护时间接近当前日期，只能说明仓库 fresh，不能自动证明每个 README feature 都 current。

对每个关键机制记录四级证据：

1. `Declared`：README、依赖、header、注释出现；
2. `Compiled`：目标 build 真正编译进入，不在 `#if 0` / Editor-only / dead branch；
3. `Runtime-active`：固定源码有真实调用链；
4. `Verified`：目标 UE 版本运行验证。

外部项目报告的 Accepted Mechanisms 必须至少有 Runtime-active 证据；写入“目标项目生产默认”前要求 Verified 或明确标记仍待验证。

典型检查：

- 搜索函数定义之外是否有 caller；
- 搜索 `#if 0` / feature macro / disabled plugin；
- README 的 rollback/thread-safe/Iris/save 等宣称是否能落到 active code；
- include 某 API 不等于采用该 API；
- unit/sample success 不等于多人 JIP/reconnect/packaged build success。

如果 README 与固定源码冲突，以固定源码为当前实现事实，并把冲突写进报告。

## 15. Fork freshness：先找 upstream，再看“仓库最后更新时间”

Mass 第十一轮补充一个新的时效性反例：一个 fork 可以在 2025 仍有维护动作，但真正 upstream 已经在 2026 更新到 UE5.8。研究流程新增：

1. 检查 README 是否说明 fork/detached/upstream；
2. 查默认分支最近 commit；
3. 查 upstream 同名/原作者仓库的 commit 与版本；
4. 比较当前目标 UE 的官方 release notes；
5. 只有确定“哪个仓库代表当前实现”后再做源码蒸馏。

不要因为 fork 更新时间较新就把它当当前主线。版本快速演化的系统（Mass、Mover、Iris、GameplayCamera、UAF 等）尤其需要这一步。

## 16. 图资产/任务系统需要“双版本锚点”与 staged migration 审计

FlowGraph 这类长期维护插件会同时存在“最新设计分支”和“目标引擎兼容 release”。研究时不能只固定 default branch。

例如：

```text
FlowGraph latest 5.x @ c616a5d2...
 = Flow 2.4 in works / first UE5.9 release

FlowGraph v2.3-5.7 @ 8211b259...
 = 当前 LGF UE5.7 可直接验证的 compatibility anchor
```

规则：

1. `latest commit` 学架构演进和 bug fix；
2. `target-compatible tag` 学目标项目能实际编译/运行的 API；
3. 新分支机制要回查目标 tag 是否存在 active path；
4. 若需要 backport，用 adapter/feature gate，不把未来接口写进 Foundation public ABI。

图资产还有第二层时效性：**serialized asset migration path**。FlowGraph 2.3 明确要求较老 Data Pin 资产先经过 2.2/2.3 并 resave，再继续升级。这证明：

```text
current engine can open project
!=
all historical assets can skip-version safely migrate
```

外部项目审计因此新增：

- 是否存在 staged upgrade / resave note；
- saved node/graph stable IDs 是否成为持久 ABI；
- skipped-version fixtures 是否存在；
- README 的“supports UE5.x”是否区分 branch/tag；
- latest branch 是否已经面向下一引擎版本。


## SimpleQuest 0.8.1 的“今天提交也要做 active-code 审计”案例

`TheGeebus/SimpleQuest@46978ad2c81ba90f21836e7c468141523dedb95d` 是 2026-09-14 当天的 0.8.1 合并，README 明确 UE5.6-5.8，属于 Current-to-target。仍需逐项检查 active code：authoring graph 是否真编译到 runtime、Manager/State 是否真分权、Save snapshot 是否真 versioned、Dedicated/JIP 是否有实际 request/mirror path。

固定版本时同时记录 commit 与 tree：该 commit 的 tree 为 `daf658bd6c86f54ca024d76e58a9a81908635617`，tree SHA 不可冒充 commit SHA。

当前项目还展示另一个 freshness 维度：编辑器 dynamic pins、linked questline、conditions/outcomes 等作者工具持续变化，因此“runtime API 当前”不代表“serialized authored asset 永远无迁移成本”。对 graph/quest 工具增加 `Asset migration / pin reconstruction / stable semantic ID` 审查。

## 17. GenericGraph：高星旧项目也必须降级到 Historical architecture sample

R16 固定 `jinyuliao/GenericGraph@f9b8fe3de6bc2ef39ee771658ac4a8bf48c2e078`（2023-07-15，MIT）。仓库有较高 stars/forks 且未 archive，但默认分支最后明确的引擎迁移是 UE5.1；README 仍称 UE4 generic graph plugin，descriptor 为 1.0 且无 UE5.7/5.8 版本证据。

因此分类：`Historical architecture sample`。

### 仍可吸收

- Runtime/Editor 模块分层方向；
- Graph/Node/Edge 可扩展类型；
- Schema 集中连接合法性；
- Node 追加领域连接约束；
- explicit Edge/conversion node；
- authoring UEdGraph rebuild 到 runtime topology；
- auto-layout 作为 editor service。

### 必须目标版本重验

- `FAssetTypeActions_Base` / AssetTools 注册；
- ClassViewer；
- GraphEditor/Slate 具体接口；
- PackageSaved delegate；
- editor style / factory API；
- conversion-node schema details。

UE5.8 当前官方把 `UAssetDefinition` 描述为 Asset Actions 的替代系统之一；因此“旧 API 仍存在”不能被解释为“它仍是新项目首选”。新项目要按目标 5.7/5.8 证据选择 `UAssetDefinition`、ToolMenus 与当前 Asset editor 接入，legacy AssetTypeActions 仅作为兼容层候选。

### 旧项目源码也要做算法活性审查

GenericGraph 声称 graph 可以 cyclical，但 runtime `Print/GetLevelNum/GetNodesByLevel` 仅从 RootNodes 向 children 遍历且没有 visited/budget；TreeLayout/ForceDirected 也存在无 cycle guard 的遍历。这说明：

```text
feature flag exists
!=
all algorithms satisfy that feature contract
```

外部 Graph 项目以后增加：

- cycle-safe traversal 审计；
- rootless SCC；
- parallel edge；
- stable Node/Edge identity；
- canonical topology 与派生 cache；
- editor validation vs compiler/cook whole-graph validation；
- layout/search/context-menu scalability；
- authoring compile 是否 staging + atomic publish。

R16 正式合同见 [自定义 Graph Authoring / Compiler / Runtime 合同](generic-graph-authoring-patterns.md)。
