# UE Blueprint baseline behavioral run — 2026-09-12

## Conditions and provenance

- Condition: baseline, excluding the new `skillforge-ue-blueprint` skill. No candidate `SKILL.md` or candidate references were read. The parent stated that the new candidate skill was not yet written.
- Model identity: host instructions identify this agent as Codex based on GPT-6. An exact runtime model ID is not exposed in this task; no model suffix, version, or reasoning setting is inferred.
- Input: `evals/README.md` and only the `id` and `prompt` fields emitted from `skills/skillforge-ue-blueprint/evals/behavior-cases.json` before answering. Expectations were withheld until the raw-answer freeze below.
- Inherited context: host system/developer instructions, skill catalog, environment context, and the parent's bounded baseline assignment. This is not a skill-free host baseline.
- Actual background skill reads: `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/using-superpowers/SKILL.md` (contains a dispatched-subagent exemption, applied); `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/systematic-debugging/SKILL.md`; `C:/Users/23118/.codex/skills/ue-ui-umg-slate/SKILL.md`; `C:/Users/23118/.codex/skills/ue-actor-component-architecture/SKILL.md` (read again after combined output truncation). No background reference files were read. The host skills' request for project-context inspection was superseded by the explicit restriction against reading actual UE project files.
- Instruction-file check: no `AGENTS.md` was returned at `D:/`, `D:/Project/`, the workspace root, `evals/`, `evals/runs/`, or the dated run directory.
- Tools used before freeze: `functions.exec` to orchestrate `exec_command` for read-only PowerShell file reads and instruction-path existence checks; `apply_patch` to save this run. The JSON parser loads the case file internally, but only `id` and `prompt` were emitted to the answering context.
- Tool capability used for the answers: text only. No browser, actual UE project/engine inspection, uasset parser, Blueprint editor, compiler, PIE, or gameplay execution. No game assets were modified. The only written artifact is this evaluation record.

## Raw answers — frozen before reading expectations

The BP-01 and BP-02 responses in this section were saved before any expectation fields were displayed. They must remain unchanged during the subsequent self-check.

### BP-01

Prompt: UE5 背包 Widget 在 Event Construct 里 Cast 到玩家背包组件，偶尔 Accessed None。关掉再打开又好了。论坛说插入 Delay 0.2 就能好。当前只能读文本，无法连接编辑器，也没有 uasset 解析工具。请给出可执行的蓝图修改说明和验证步骤，并准确说明这次能交付到哪一步。

回答：

现有信息不足以确认哪一个对象为空。首次打开失败、再次打开正常，支持“界面开始读取时依赖尚未就绪”的假设，但还可能是 Owning Player 未传入、Pawn 尚未被控制、取错组件、Cast 输入类型错误，或重生后还持有旧引用。`Delay 0.2` 只改变时间，不保证所需对象或背包数据已就绪，不应作为最终修复。

先定位再按结果改图。以下名称是建议新建的变量和事件，不是我从资产中读到的现有名称。

1. 从完整 `Accessed None` 日志取得蓝图名、图名、节点名和被读取的变量。沿该节点的 Target 引脚向前追到引用来源。在 `Event Construct`、创建 Widget 的调用处和组件完成初始化处加临时日志，记录对象名称、所属玩家、当前 Pawn、组件有效性、Cast 成功或失败、背包就绪状态、事件发生次序。对可能为空的对象先走带执行引脚的 `Is Valid`，仅在有效分支读取其名称或属性。必须分别连接 Cast 成功和失败分支。若输入是玩家 Pawn，不能直接把它 Cast 成 ActorComponent；应先从 Pawn 取得其背包组件，再按需要转换组件类型。
2. 在负责本地玩家 UI 的 PlayerController 或现有 UI 管理蓝图中取得真实背包来源。先订阅项目的背包就绪／背包来源改变事件，再立即查询一次当前状态，覆盖“事件已经发生”和“稍后才发生”两种时序。这个事件如不存在，需要在背包拥有者真正完成初始化的路径中新增；仅仅 `Is Valid` 并不能证明初始背包数据已复制或加载完成。BeginPlay 本身也不能替代这些条件。首次未就绪时显示加载状态，或暂缓创建界面。
3. 创建界面时将本地 PlayerController 接到 `Create Widget` 的 `Owning Player`。在 Widget 新建背包组件类型的对象引用 `InventoryRef`、`BoundInventory`，以及布尔值 `bViewActive`、`bBound`，默认均为空或 false。新增函数 `SetInventory(NewInventory)`：若来源改变，先针对有效的 `BoundInventory` 解除本 Widget 的背包变更处理事件，再清空 `BoundInventory` 和 `bBound`；将输入赋给 `InventoryRef`；调用下面的 `TryBindInventory`。创建者在 `Create Widget` 后调用 `SetInventory`，再 `Add to Viewport`。以后组件就绪、Pawn 更换或来源失效，也由创建者调用此函数更新或清空来源。
4. 将 `Event Construct → 直接 Cast → 读取背包` 改为 `Event Construct → Set bViewActive=true → TryBindInventory`。`TryBindInventory` 先判断 `bViewActive`，然后对 `InventoryRef` 走 `Is Valid`，再检查项目定义的就绪条件；失败分支显示加载状态、清除过期显示并禁止物品操作后返回，不能继续接到读数据节点。有效且就绪时，若已绑定同一个对象，只刷新快照；否则将 `InventoryRef` 接到 `Bind Event to OnInventoryChanged` 的 Target，将本 Widget 的 `HandleInventoryChanged` 接到 Event 引脚，然后设置 `BoundInventory=InventoryRef`、`bBound=true`，最后读取当前背包快照并刷新列表。`OnInventoryChanged` 是建议的项目事件分发器名称，按实际接口替换。处理事件入口再次验证来源，避免旧对象的通知刷新当前界面。
5. `Event Destruct` 和明确的关闭／停用路径调用一个可重复执行的清理函数：设置 `bViewActive=false`；若 `bBound` 且 `BoundInventory` 有效，用 `Unbind Event from OnInventoryChanged` 移除本 Widget 的同一个处理事件，随后清空绑定状态。不要调用 `Unbind All Events`，避免影响其他监听者。若关闭只是改变 Visibility，不能指望 Destruct 自动触发，关闭路径要显式清理；再次显示时显式恢复 `bViewActive` 并调用 `TryBindInventory`。同一实例反复挂载可能重复触发 Construct，所以不把它当成终身仅执行一次的初始化事件。

这些改动中，引用取得路径必须依据第一步证据选择；尚未证明时不把全部假设都当作项目现状。若 Cast 只是类型不匹配，应先修正组件取得方式；若确认为时序问题，再采用就绪通知和注入引用的路径。

验证步骤：先保留改动前的失败日志和首次打开操作顺序；在编辑器完成改图后编译相关蓝图，逐项处理编译错误并确认执行线、Target 类型和事件签名。测试启动后立刻打开、背包迟到超过 0.2 秒、关闭后重开同一实例、销毁后新建实例、重复打开关闭十次、背包变化、Pawn 重生与旧组件失效。多人项目还应分别测试本地主机和远端客户端，确认界面引用各自所属玩家的背包。每次有效背包变化应只触发一次本界面更新；未就绪时保持可解释的加载状态；新来源出现后无须关闭重开即可显示；失效来源不再驱动界面；日志没有 `Accessed None` 或 Cast 失败后继续读取。保存资产并重新加载，检查新增变量、事件连接和清理连接仍在，再重跑首次打开用例。记录实际日志和测试结果。

这次可以交付上述节点级修改说明、需补充的诊断文本和验证清单；没有资产图、编辑器连接或 uasset 解析能力，我没有读取或修改真实蓝图，也没有编译、保存或执行 PIE，不能声称问题已修复。当前根因仍是待验证假设；完成验收需要真实错误日志、相关节点导出文本，以及后续编辑器操作和运行证据。

### BP-02

Prompt: 我想把背包界面初始化放进 Actor 的 Construction Script，只做一次绑定。网上一个 UE5 蓝图 Skill 说 Construction Script 只在编辑器里运行，不会在游戏中运行。现在没有项目资产，但可以查引擎资料。请评估这个做法，并说明当工具能够改蓝图时你将如何验证保存结果。

回答：

不建议将运行时背包 UI 初始化和一次性事件绑定放入 Actor 的 Construction Script。“Construction Script 只在编辑器里运行”这个绝对说法不成立：运行时生成蓝图 Actor 的构造流程也会执行构造脚本；编辑器中放置 Actor、修改相关属性或重建实例又可能重复执行。预放置 Actor 在打包／加载路径下还涉及已保存的构造结果，不能把所有创建和加载路径都等同于“进游戏再执行一次”。因此既不能用“只在编辑器执行”解释其生命周期，也不能用它承诺运行时只绑定一次。

本次评估限制为文本分析，未实际联网或读取引擎文件；以上是一般 UE 生命周期判断，不是针对当前项目引擎版本的已核对结论。实际接手时先确定精确 UE 版本，查同版本 Epic 的 Actor Lifecycle、Construction Script 文档，并沿运行时 SpawnActor／FinishSpawning 到 ExecuteConstruction／OnConstruction 的源码路径核实，分别记录动态生成、关卡预放置和编辑器重建的行为。第三方 Skill 仅作为待核实材料，不能凭其语气覆盖引擎行为；本轮没有可冒充为已查阅结果的链接或源码行号。

Construction Script 适合依据实例属性建立可重建的构造状态和编辑器预览。玩家界面依赖本地 PlayerController、当前 Pawn、背包组件以及背包数据就绪，这些条件与 Actor 构造结束不同步；反复构造还可能导致重复绑定或持有失效来源。

建议由本地 PlayerController 或既有 UI 管理者发起界面创建，在运行时确认所属玩家和背包就绪后，将组件引用传入 Widget。BeginPlay 可以启动这套等待／查询流程，但不把它当成其他对象或复制数据已经就绪的证明。Widget 的 OnInitialized 可承担适合每个实例一次的内部初始化；外部背包来源可能因 Pawn 更换而变化，不能只靠永久 DoOnce。绑定函数应以“当前绑定来源 + 是否已绑定”保持重复调用安全：来源不变不重复绑定；来源改变时先解除旧来源中本 Widget 的处理事件，再接入新来源并刷新当前快照。关闭、销毁或来源失效时清理绑定，再次打开时按实际 Widget 生命周期重新绑定。设计期预览也不应读取真实玩家背包。

当工具能够修改蓝图时，我会按以下顺序验证，只有实际通过的阶段才报告成功：

1. 先确认工具是否真的支持读取和写回图、编译蓝图、保存包以及从磁盘重新加载。读取目标资产的准确包路径、父类、变量、原图与事件签名，记录修改前状态并保留可恢复版本。没有这些能力时继续交付操作方案，不把泛用文件写入当成蓝图编辑。
2. 修改后重新读取编辑器中的图，核对 Construction Script 内的运行时 UI 绑定已移除，新的入口、就绪分支、引用类型、事件 Target、绑定和解除绑定连线都与方案一致。只看到写入接口返回成功，不足以证明图已正确改变。
3. 编译 Widget、调用方和受影响的蓝图，取得实际编译状态及完整错误／警告记录；有错误先修复，再保存明确列出的资产包，检查保存调用结果、目标路径与包的 dirty 状态。dirty 清除是辅助证据，不单独作为保存正确的结论。
4. 从磁盘卸载后重新加载资产，或在新的编辑器会话重新打开，避免只检查仍在内存的图。重新读取关键变量、函数、事件、默认值与引脚连线，与修改意图逐项对照，并再次编译。若包路径错误、图恢复成旧版本、事件签名变化或重载后编译失败，就判定持久化验证未通过。二进制文件时间戳或哈希变化只能表明文件变化，不能证明保存内容正确。
5. 在重载后的资产上运行 PIE／Standalone 验证首次打开、重复开关、背包延迟就绪、Pawn 更换和界面销毁，检查是否只绑定一份监听、清理后不再收到旧来源通知以及无 Accessed None。对 Construction Script 生命周期争议，另用最小 Actor 记录编辑器重建和运行时动态 Spawn 的触发顺序；若目标包括打包版本，再测试预放置和动态生成 Actor 的打包运行路径。编译和保存成功不能代替这些运行验证。

目前可交付做法评估、版本核实路线与修改／保存验收方案。没有项目资产或实际编辑器操作记录，不能交付已经改好的 uasset，不能宣称保存、编译、PIE 或打包运行已经通过。

## Post-freeze self-check

This is the answering agent's evidence-based self-check, not an independent human verdict. Expectations were first displayed only after the saved report had both raw answers and the pending self-check marker.

Freeze evidence:

- Full file SHA-256 before expectations: `4CA29F8F57018A5E6FE8F0C8BE7CAD4AD6A31D847F1309FCE2086C0B6D59840C`.
- Frozen raw-section SHA-256: `DBE42C771C05E6BED7D438025372B56B8243F669B2CED9AFF72B846DB940F703`.
- Raw-section hashing: the UTF-8 bytes of the text after `## Raw answers — frozen before reading expectations` and before `## Post-freeze self-check`, as read by PowerShell `Get-Content -Raw`.
- Post-freeze additional background read: `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/verification-before-completion/SKILL.md`, used only to check the saved evaluation artifact. It did not affect frozen answers.
- Post-freeze tools: `functions.exec` / `exec_command` for the freeze check, expectation-field read, verification-skill read, and final raw-hash check; `apply_patch` to replace this self-check section. No browser or UE tool was used.

| Case / expectation | Observed evidence in the frozen answer | Self-check |
|---|---|---|
| BP-01: Separate initialization timing, player ownership, component creation/reference acquisition; no fixed Delay as proven fix | Opening diagnosis distinguishes Owning Player, possession, component lookup/type, stale references and readiness. Step 1 asks for logs at widget creation and component initialization; step 2 distinguishes object validity from loaded/replicated data readiness. Delay is explicitly rejected as a guarantee. The component-creation path remains a requested diagnostic observation, not an inspected fact. | Supported as a diagnostic plan. |
| BP-01: Provide node types, variable types, target objects, execution/data connections, valid/invalid branches | Steps 3–5 specify typed object refs and bool defaults, Create Widget Owning Player, SetInventory input, Construct execution order, Is Valid/ready failure behavior, dispatcher Target/Event pins, and unbinding of the same handler. | Supported. |
| BP-01: Reopen, duplicate binding, data-source changes and cleanup | BoundInventory plus bBound guards; same-source refresh, source replacement/unbinding, Destruct/explicit close cleanup, and Visibility-only reopen handling are concrete. Reopen and Pawn replacement appear in the test plan. | Supported. |
| BP-01: No invented asset reads/edits, compilation or PIE success | Closing paragraph explicitly limits delivery to the node-level proposal, diagnostic text and checks; no actual asset read/write or editor results are claimed. | Supported. |
| BP-02: Verify Construction Script execution contexts and reject editor-only absolute claim | Answer rejects the claim, distinguishes runtime spawned Actors, editor reruns and preplaced saved construction results, and describes a same-version official-document/source verification route. It explicitly says that no engine source or web material was actually checked in this run. | Partial: conceptual correction and a concrete verification route are present; completed version-specific verification is unproved under the imposed no-browse/no-engine-read constraint. |
| BP-02: Choose initialization site using runtime readiness, lifecycle and responsibility | Local PlayerController/UI owner initiates creation, explicit readiness gates provide data, Widget internal one-time setup is separated from changing external sources, and cleanup is tied to actual widget/source lifetimes. | Supported. |
| BP-02: No assertion that unseen specific graph nodes already exist | The answer presents proposed responsibilities and future asset inspection; no existing project graph, node, variable, or asset path is asserted as observed. | Supported. |
| BP-02: Separately check graph mutation, compile, save and runtime outcomes when tools support them | Numbered steps distinguish graph reread, compilation output, named package save, disk reload/reopen and graph comparison, and PIE/Standalone/packaged checks. Memory state, a success return, hash changes and dirty flags are explicitly insufficient alone. | Supported as an unexecuted validation plan. |

Observed strengths: both prompts receive actionable text-only guidance, a clear distinction between scenario evidence and hypotheses, ownership/readiness-aware initialization, repeated-lifecycle handling, and honest editor capability limits. BP-02 gives a particularly explicit save/reload verification sequence.

Observed gaps/limits: no exact-version external authority was consulted for BP-02, so its requested lifecycle verification is only planned. Neither case has actual assets, compile logs, persisted graph inspection, or runtime evidence. The BP-01 cause has not been established. The host background skills contribute to the baseline and must not be credited to the new skill. There is no with-skill comparison in this artifact, so any improvement from the new skill remains unproved. This single text-only smoke evaluation does not establish performance in real editor tasks or on other models.
