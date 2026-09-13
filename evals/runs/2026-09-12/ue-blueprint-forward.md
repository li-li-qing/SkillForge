# UE Blueprint 有技能行为冒烟评估

- 日期：2026-09-12。
- 条件：with-skill；仅 BP-01、BP-02 两例；文本分析与操作方案。
- 模型身份：后端模型 ID 与具体推理设置未向本子上下文暴露。宿主指令将助手描述为 Codex、基于 GPT-6；此描述不是对实际后端 ID 的核验，不据此猜测具体版本。
- 能力边界：只读取允许的评估说明、目标技能、参考资料与背景技能说明，并写本报告。无网络访问、真实 UE 项目或引擎源码读取、资产解析、编辑器、构建、编译、保存游戏资产或 PIE。
- 隔离说明：作答前未读取 expectations、基线或其他结果。使用 PowerShell 将行为 JSON 投影为 id/prompt 后才展示给回答上下文；底层解析器读取了 JSON 文件，但 expectations 未被输出或用作回答输入。
- 本次不是跨模型、跨 Agent 或真实编辑器验收；不作改善声明。

## 实际加载内容

1. `evals/README.md`：仓库行为评估约定。
2. `skills/skillforge-ue-blueprint/SKILL.md`：指定的有技能条件。
3. `skills/skillforge-ue-blueprint/evals/behavior-cases.json`：冻结前仅显示 id/prompt。
4. `skills/skillforge-ue-blueprint/references/initialization-communication.md`：初始化、通信、Construction Script 的既有版本证据记录。
5. `skills/skillforge-ue-blueprint/references/asset-delivery.md`：文本交付与改图后保存验收边界。
6. `skills/skillforge-ue-blueprint/references/cases.md`：技能内代表案例及核验状态；这是事前允许读取的目标技能参考，不是本轮评分结论。
7. 背景技能：实际读取 `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/using-superpowers/SKILL.md`。其 `SUBAGENT-STOP` 明确让被派遣子代理忽略该技能，故未执行其工作流。其他背景技能只在宿主目录清单中可见，未读取正文或调用。

技能参考中的引擎源码核验属于资料作者的既有记录；本轮没有复核引擎文件或访问参考中的外部链接。宿主系统规则、已安装技能目录和既有模型能力属于背景，不能归因于目标技能。

## 冻结前工具轨迹

1. `functions.exec` 调用三个独立的 `tools.exec_command`（`Promise.allSettled`）：分别用 `Get-Content -Raw` 读取评估 README、目标 SKILL.md、背景 using-superpowers/SKILL.md，三个结果均成功。
2. `functions.exec` → `tools.exec_command`：`Get-Content ...behavior-cases.json -Raw | ConvertFrom-Json`，随后 `Select-Object id,prompt | ConvertTo-Json -Depth 8`；仅两例的 id/prompt 出现在输出中。
3. `functions.exec` 调用三个独立的 `tools.exec_command`（`Promise.allSettled`）：读取上述三个目标技能参考，三个结果均成功。
4. `functions.exec` → `tools.apply_patch`：创建本报告，并在任何 expectations 自查前写入以下两份原始回答。

## 已冻结的原始回答

<!-- RAW_ANSWERS_BEGIN -->

### BP-01

**Prompt**

UE5 背包 Widget 在 Event Construct 里 Cast 到玩家背包组件，偶尔 Accessed None。关掉再打开又好了。论坛说插入 Delay 0.2 就能好。当前只能读文本，无法连接编辑器，也没有 uasset 解析工具。请给出可执行的蓝图修改说明和验证步骤，并准确说明这次能交付到哪一步。

**原始回答**

先把背包来源的赋值、就绪检查和界面刷新改成显式流程。`Delay 0.2` 只能改变时序，不能证明组件已创建、玩家选对了或背包数据已经加载完成。重开恢复符合初始化时序问题，但仅凭描述还不能确定具体原因，也不能确定报错就发生在 Cast 节点。

本次没有资产读取、改图或运行能力，能交付下面这份接线说明和验证清单。资产名、组件类型与事件签名仍需在工程中核对；下面以 `WBP_Inventory`、`BP_InventoryComponent` 等作为示例自定义名称，均不表示已确认存在，也不是 UE 自带的背包 API。

**先定位对象与报错**

找到负责显示背包的 Widget Blueprint，确认父类、`Event Construct` 中报错所指的访问节点，以及创建它的 `Create Widget` 调用方。沿报错节点的 `Target` 数据线检查：该引用由谁赋值、在什么执行分支赋值、是否属于当前 Owning Player/Pawn、报错实例是否就是刚创建的 Widget。记录调用顺序、对象名称、有效性和数据就绪状态。类默认值、关卡放置实例和当前运行实例要分清。

如果 Cast 的 `Object` 实际接的是 Pawn/Character，却要 Cast 为库存组件，这是对象来源不对。应先从正确 Actor 上取得已有组件，再根据返回类型决定是否需要 Cast。Cast 不会创建组件，也不会等待异步或复制数据。把“引用有效”“类型符合”“库存数据就绪”分别处理。

**准备变量和明确的数据契约**

在背包 Widget 中新增或复用以下内容，库存组件继续拥有库存业务真值，Widget 只显示它提供的状态：

| 示例名称 | 类型/默认值 | 用途 |
|---|---|---|
| `InventorySource` | 项目库存组件的对象引用；None | 当前要显示的库存来源，由创建/管理界面的拥有者提供 |
| `BoundSource` | 同类型对象引用；None | 实际已绑定通知的旧来源，便于清理 |
| `bInventoryBound` | Boolean；false | 防止同一 Widget 对同一来源重复绑定 |
| `SetInventorySource(NewSource)` | 自定义函数；输入为库存组件对象引用，无返回值 | 接受来源或来源变更 |
| `RefreshInventoryFromSource` | 自定义函数 | 检查来源与数据状态，读取快照并刷新显示 |
| `ReleaseInventorySource` | 自定义函数 | 解除本 Widget 的订阅并清理引用 |

需要映射到项目现有能力的契约是：查询库存是否可读、读取当前库存快照、库存就绪通知、库存变化通知。为便于说明，下文将它们称为 `IsInventoryReady`、`GetInventorySnapshot`、`OnInventoryReady` 和 `OnInventoryChanged`。这些都是项目函数/Dispatcher 的示例名；若不存在，先在数据拥有者上明确等效契约，不能凭名称添加一个看似内置的节点。就绪应由实际加载/初始化完成流程发出。通知处理事件的参数必须与实际 Dispatcher 签名完全匹配。

**把来源交给正确的 Widget 实例**

在现有 UI 创建者处，用实际所属玩家的 PlayerController 接 `Create Widget` 的 `Owning Player`，把 `Return Value` 保存为当前背包 Widget 引用。来源已可取得时，在有效的 Widget 上调用 `SetInventorySource`：`Target` 接这个创建返回值，`NewSource` 接该玩家实际的库存组件。

如果组件在 Pawn 上，可在项目确认的 Pawn 引用有效分支使用 `Get Component by Class`，`Target` 接该 Pawn、`Component Class` 指定库存组件类；根据实际输出类型做一次必要的 Cast，成功输出接 `NewSource`。如果组件实际属于 PlayerState 或其他服务，就从该真实拥有者取，不能擅自迁到 Pawn。不要用固定的 Player 0 替代所属玩家。找不到来源或 Cast 失败时，给 Widget 传 None 并记录来源；不要沿失败分支调用库存函数。

当组件尚未创建时，由实际拥有者的组件可用/玩家切换入口再调用 `SetInventorySource`。当组件已存在但数据仍在加载时，可以先传入组件，让界面订阅它的就绪通知。`Event Construct` 可以显示初始等待状态，但不再以它的执行时间充当依赖已经就绪的保证。

**接 `SetInventorySource` 的执行线和数据线**

1. 函数入口后，检查 `NewSource == BoundSource`、`bInventoryBound` 和 `Is Valid(NewSource)`。三者都满足时，将 `NewSource` 保持为 `InventorySource`，直接调用 `RefreshInventoryFromSource` 并返回，不重复 Bind。即时刷新保证重开时得到当前状态，即使之前已经发过就绪事件。
2. 其他情况先调用 `ReleaseInventorySource`。其中对有效的 `BoundSource`，分别用 `Unbind Event from` 对应的 Dispatcher，`Target` 接 `BoundSource`，`Event` 接本 Widget 当初绑定的同一个处理事件。只移除本 Widget 的处理函数，不使用会清掉其他订阅者的 `Unbind All`。然后设置 `BoundSource=None`、`InventorySource=None`、`bInventoryBound=false`。
3. 回到设置函数，将 `NewSource` 数据引脚接 `Set InventorySource` 的值，并进入带执行分支的 `Is Valid` 检查。Invalid 分支显示“等待背包来源”并禁用依赖库存数据的操作，然后返回；后续由拥有者的真实来源可用入口重新进入，不用 DoOnce 把首次失败锁死。
4. Valid 分支：分别对就绪和变化 Dispatcher 使用 `Bind Event to`。两个节点的 `Target` 均接有效的 `InventorySource`；`Event` 分别接本 Widget 的自定义事件 `HandleInventoryReady`、`HandleInventoryChanged`。两个处理事件都调用 `RefreshInventoryFromSource`。绑定完成后设置 `BoundSource=InventorySource`、`bInventoryBound=true`，再立即调用 `RefreshInventoryFromSource`。
5. 这里采用“先订阅，再读当前快照”。仍需遵守项目实际事件契约，尤其是快照是否异步、订阅是否立即回调。若刷新是异步请求，完成时核对来源和本次界面会话，丢弃旧来源/旧请求结果。若只有接口引用而 Dispatcher 属于具体类，必须通过项目提供的订阅服务或明确的实现对象完成绑定，不能把不存在的 Dispatcher 接在接口 Target 上。

**接刷新与关闭流程**

`RefreshInventoryFromSource` 先 `Is Valid(InventorySource)`：无效则进入等待来源显示并返回；有效才调用 `IsInventoryReady`，其 `Target` 接 `InventorySource`，返回 Boolean 接 `Branch.Condition`。false 分支显示加载中并禁用库存操作；true 分支调用实际快照函数，Target 同上，将快照返回值接现有的列表/格子刷新逻辑。刷新入口每次都检查有效性和就绪，不能只在第一次检查一次。

在项目的背包关闭/停用入口调用 `ReleaseInventorySource`。单纯 `Set Visibility` 隐藏不保证触发 `Destruct`，因此不能只靠 `Destruct` 清理；`Destruct` 可作为额外的幂等清理入口。拥有者也要按界面活跃状态撤销或忽略等待中的外部回调，避免关窗后又把来源绑定回来。

再次打开时从拥有者传入当前来源并立即同步。Pawn/玩家库存来源切换时也走同一函数，先清旧源，再订新源。销毁后重新创建 Widget 时，把引用交给新实例。`bInventoryBound` 只描述本实例当前确实已建立的订阅，不用它永久跳过未来的重新初始化。

**实施后的验证步骤，目前均待执行**

先核对实际函数和 Dispatcher 签名、关键 Target 与失败分支，编译库存源、Widget 及受影响的 UI 创建者；保存准确的目标资产包，重新加载并读回关键节点和默认值。编译通过不能证明生命周期问题已解决。

再在项目实际运行环境中执行：

| 场景 | 应观察到的结果 |
|---|---|
| 冷启动首次打开，库存已经就绪 | 立即显示当前快照；无 Accessed None |
| 组件晚创建，或组件存在但库存数据晚到 | 先显示等待/加载状态，真实就绪后自动显示；超过 0.2 秒也能正常恢复 |
| 不同方式连续关闭/重开，包括隐藏复用 | 每次状态最新；单次库存变化只触发一次本 Widget 的刷新回调 |
| 重复传入同一来源 | 不增加订阅次数，仍能补读最新快照 |
| 换 Pawn 或换库存来源 | 旧来源更新不再影响界面；新来源即时同步并继续更新 |
| 来源失效、Widget 销毁再创建 | 不访问无效引用，无旧回调污染新实例；新实例正常初始化 |

保留错误日志和每个 Widget/来源的回调计数，核实没有吞掉错误或永久停在空白状态。只有工程本身涉及多人时，再覆盖实际所属玩家和复制到达顺序。

这次完成的是文本修改方案与可观察验收步骤。没有读取真实蓝图图结构，没有修改 `.uasset`，没有执行编译、资产保存/重载或运行回归，因此不能报告故障已修复。

### BP-02

**Prompt**

我想把背包界面初始化放进 Actor 的 Construction Script，只做一次绑定。网上一个 UE5 蓝图 Skill 说 Construction Script 只在编辑器里运行，不会在游戏中运行。现在没有项目资产，但可以查引擎资料。请评估这个做法，并说明当工具能够改蓝图时你将如何验证保存结果。

**原始回答**

不建议把运行期背包 UI 的外部数据订阅放到 Actor 的 Construction Script，也不能用它保证“只绑定一次”。Construction Script 可参与编辑器重建和运行期 Actor 生成；运行时数据依赖是否就绪，需要另外的初始化契约。

本次评估禁止联网和读取真实引擎源码，因此我没有实际打开那篇网络 Skill、Epic 页面或本机 UE 源码。当前可用证据是随目标技能提供的版本核验记录：`references/initialization-communication.md` 与 `references/cases.md` 记录，在 UE 5.7.4、CL 51494982 中，`Engine/Source/Runtime/Engine/Private/Actor.cpp` 的 `FinishSpawning` 进入 `ExecuteConstruction`，`ActorConstruction.cpp` 的构造流程可进入 `ProcessUserConstructionScript` / `UserConstructionScript`。这是资料作者已有的源码核验，不是我本轮独立完成的源码检查。它支持否定“Construction Script 只在编辑器执行”这个绝对说法，但目标项目版本仍未确认。

不能反过来将其说成所有 Actor 在每次游戏启动时都会以相同方式执行 Construction Script。编辑器重建、运行时动态生成、关卡加载与 cooked 构造结果属于不同路径。恢复查阅能力后，应先确定项目精确版本，并沿该版本的生成、构造和加载路径复核；技能参考中的外部 Epic 页面链接仅是后续查找入口，本轮未访问，不能当作本轮已验证来源。第三方 Skill 是待核验材料，不应凌驾于相应版本的引擎实现和可复现行为之上。

对于这项功能，应让构造逻辑负责适合反复重建的组件配置或预览。UI 创建由现有 UI 管理者或所属玩家负责，库存数据继续由现有库存组件/服务拥有。运行阶段显式传入当前库存来源，检查对象有效、所属关系与数据就绪，建立变化订阅并立即读取当前快照。`BeginPlay` 可成为发起这一流程的入口，但不能证明玩家、组件或异步库存数据全部就绪。

“一次”应定义为每个活跃 Widget 对当前数据源最多保留一份有效订阅：同源重复初始化不重复绑定；重开时补读当前状态；换 Pawn/来源先解绑旧源；关闭或销毁时按 UI 生命周期移除自己的处理事件。隐藏复用的界面应有明确停用入口，不能假定必定触发 `Destruct`。不要用 Construction Script、永久 DoOnce 或固定 Delay 来掩盖这些状态迁移。资产名、现有父类、UI 管理方式和事件签名现在未知，所以目前只能给出这个方案，不能声称已改好资产。

工具今后能够改图时，我会把“改图成功”“编译通过”“磁盘保存正确”和“运行正确”分别收集证据：

1. **确认能力和目标。** 先确认工具分别支持读图、改图、编译、保存、磁盘重新加载与运行。普通文件写入不代表可以安全修改 `.uasset`。定位完整资产包路径、父类、现有 Construction Script/运行初始化图、变量、组件、事件签名和调用方，并保留可恢复的修改前状态。
2. **实施并读回实际图。** 将运行期绑定移到明确的就绪/激活流程，补上同源幂等、旧源清理和失败分支。随后读取目标资产的实际节点、关键默认值、Target、执行线与数据线，确认接到正确实例和正确事件，且未改到同名资产或仅更改工具缓存。
3. **编译和保存。** 编译受影响的 Actor、Widget 和实际调用方，记录并处理编译诊断。保存明确列出的目标包，核对完整保存位置及实际保存结果。一个 API 返回 true 或文件时间戳发生变化，只是局部证据。
4. **验证持久化。** 在保护当前未保存工作的前提下，从磁盘重新加载目标包，或在新编辑器会话打开；读回关键变量、节点、Target、连线与事件签名，并确认编译结果。此处读取必须来自重新载入的资产，不能仅查原来的内存对象、摘要索引或缓存。若工具无法可靠重载，则报告“已保存但未完成重载核验”，不能补写成功结论。重载前处理本次授权范围内的保存，保留无关编辑，不能丢弃其他未保存工作。
5. **验证运行行为。** 按项目实际用法验证首次创建/打开、库存延迟就绪、反复开关、同源重复初始化、换源、销毁后重建，观察界面同步、回调次数和错误日志。相关 Actor 若支持动态生成，验证运行时生成路径；再按项目需要覆盖编辑器重建、关卡加载和打包运行，不能用一次 PIE 替代所有路径。网络角色只在该项目涉及多人时按实际角色补测。

最终交付应列出实际修改并保存的资产包、图读回结果、编译诊断、磁盘重载核验和已运行场景。任何工具不具备或本次没有执行的环节都会标成未验证。目前没有项目资产，也未操作编辑器；这里交付的是依据已有资料的评估和后续验收方案。

<!-- RAW_ANSWERS_END -->

原始回答冻结状态：以上两份回答已先于 expectations 读取写入本文件。之后仅追加验收点自查与过程记录，不改写原始回答。

## 冻结后回答者自查

这是回答者自查，不是独立审阅或用户验收。原始回答区（包含两端标记，以 UTF-8 编码计算）的 SHA-256 为 `aceef40e056e52ae9c646b810c3cc6a4ed164a9c3797deb4f9620d37ba3a2109`。读取 expectations 前整份报告的 SHA-256 为 `86d18046b3d645ab8519321ed28d03359cf0d07f15bfdf6b61e9cddcb3027381`。

| 用例 | 验收点 | 自查判断与回答依据 |
|---|---|---|
| BP-01 | 把初始化时序、玩家所有权、组件创建与引用获取分开排查，不把固定 Delay 当作已证实修复 | 满足：要求沿错误节点 Target 追踪引用与赋值执行分支，区分所属玩家、组件晚创建和数据迟到；指出 0.2 秒不能证明就绪。 |
| BP-01 | 提供节点类型、变量类型、目标对象、执行线/数据线和有效/无效分支 | 满足：变量表明确对象引用及默认值；逐步列出 Create Widget、Get Component by Class、Cast、Is Valid、Branch、Bind/Unbind 的 Target、关键数据引脚和失败分支。 |
| BP-01 | 考虑界面重复打开时的重复绑定、更新来源和清理 | 满足：同源检查防止重复订阅；重开即时读快照；换源只解绑本 Widget 的旧处理事件；隐藏停用和 Destruct 均有清理安排。 |
| BP-01 | 不声称已经读取或修改资产、编译或通过 PIE | 满足：交付明确限于文本方案，并逐项标出资产读取、修改、编译、保存/重载和运行未执行。 |
| BP-02 | 核验 Construction Script 的运行场景，不采信仅编辑器运行的绝对结论 | 有限满足：引用技能已有 UE 5.7.4、CL 51494982 的 FinishSpawning 到用户构造脚本路径，区分编辑器重建、运行生成、加载与 cooked 路径；本轮禁止引擎读取/网络，故只是对既有资料的核对，未独立完成源码或运行核验。 |
| BP-02 | 基于运行期数据就绪、生命周期和职责提出初始化位置 | 满足：让构造逻辑处理可重建配置，由 UI 管理者/所属玩家在运行阶段提供库存源，以真实就绪入口初始化；明确 BeginPlay 也不等于全部依赖就绪。 |
| BP-02 | 不声称没有见过的具体图节点已存在 | 满足：说明资产、父类、UI 管理方式、事件签名未知；把节点改动作为未来执行方案，没有断言已见图内容。 |
| BP-02 | 工具支持时分别检查图修改、编译、保存与运行结果 | 满足：分列图读回、受影响蓝图编译、指定包保存、磁盘重载和场景运行，并说明各证据不可替代。 |

冻结后工具轨迹：`functions.exec` → `tools.exec_command` 读取本报告并计算冻结哈希；随后另一次 `exec_command` 仅投影输出两例 id/expectations；`tools.apply_patch` 追加本自查；最后读取本报告并重新计算原始回答区哈希，核对原文未变。期间仅通过 `collaboration.send_message` 向父代理告知已冻结的状态，没有访问其他评估结果、真实 UE 资产或外部资料。
