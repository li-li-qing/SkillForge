# 名称与描述匹配、组合冒烟评测

日期：2026-09-12。范围：四个新技能的 24 个触发案例及 5 个组合案例。性质：评测者根据描述手工选择技能的冒烟检查，**不是宿主自动发现或自动激活机制的实测**。

## 方法与已读取资料

- 评测由父任务分派的独立子代理完成；未覆盖模型和推理设置，继承父任务设置。实际后端模型 ID、温度及随机种子在当前工具接口不可见，不根据产品名称推测版本。
- 读取 `D:/Project/Skills/evals/README.md`，按其“先只提供名称和描述，判断案例应如何选择，再揭示期望”的约定执行。
- 必要宿主指令：已注入的系统、开发者与父任务指令，以及宿主技能目录的名称/描述列表；另读取 `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/using-superpowers/SKILL.md`。该文件的 `SUBAGENT-STOP` 明确要求被分派特定任务的子代理忽略此技能，因此未继续加载其流程或参考。
- 检查 `D:/AGENTS.md`、`D:/Project/AGENTS.md`、`D:/Project/Skills/AGENTS.md`、`evals/AGENTS.md`、`evals/runs/AGENTS.md`、`evals/runs/2026-09-12/AGENTS.md`、`skills/AGENTS.md` 与四个技能目录根部的 `AGENTS.md`，均无文件输出，未加载其他仓库指令。
- 四个新技能的 `skills/*/SKILL.md` 采用逐行读取，遇到前言结束分隔符立即停止，只向评测者输出 `name` 和 `description`，未读取正文和参考资料。
- 四个 `skills/*/evals/trigger-cases.json` 经 JSON 解析后仅投影 `id`、`prompt`、`context`；冻结判断前，工具没有输出 `expected` 或 `reason`。原文件在解析器内包含隐藏字段，此处的盲法指评测者收到的工具结果不含这些字段，并非文件层面删去答案。
- 未读取行为案例、其他行为报告、研究文档或总结；未浏览互联网、调用真实工程或 Agent 自动发现机制。
- 实际工具：`functions.exec` 编排 `tools.exec_command`；PowerShell 用于上述限定文件读取、JSON 字段投影及本报告写入。没有运行真实技能、构建、游戏编辑器或外部服务。

宿主背景规则影响：中文/英文理解、一般 UE 与 UI 知识、工具纪律及已注入技能目录描述无法从评测上下文剥离；这些既有背景不归因于新技能。判定仅依据本次四个名称/描述以及案例 prompt/context，不能证明新技能正文改善了行为。用例 context 本身已提供不少边界条件，所以此轮主要检查描述与已给条件是否一致，难度与自然用户输入不同。

## 冻结前可见的新技能元数据

- `skillforge-debugging`：定位和修复代码、蓝图、插件或界面的错误、崩溃、偶发失效与异常结果。Use when debugging failures, regressions, inconsistent behavior or unexplained output. 纯功能设计、正常操作说明和没有故障目标的代码阅读不触发。
- `skillforge-ue-blueprint`：创建、修改、解释和排查 Unreal Engine 5 蓝图、Widget Blueprint、事件图与节点连接。Use when working with Blueprint graphs, variables, functions, interfaces, dispatchers or Accessed None. 纯 C++ 实现、材质图和其他软件节点图不触发。
- `skillforge-ue-cpp`：编写、修改和审查 Unreal Engine 5 C++，涵盖 UObject 反射、所有权、生命周期、模块依赖及蓝图接口。Use when UE C++ work involves UCLASS, UPROPERTY, UFUNCTION, delegates, async callbacks or Build.cs. 普通 C++、MFC 和纯蓝图布局不触发。
- `skillforge-ui-design`：设计、调整或检查游戏 HUD、工具窗口、配置面板的信息结构、布局、交互状态、缩放、焦点与输入层级。Use for UI layout, interaction states, responsive tool panels and HUD design across existing frameworks. 纯业务算法、无界面任务和仅制作图片不触发；已有界面故障可与排障技能组合。

## 第一阶段：24 个触发判断（已冻结，不随期望修改）

冻结时间：2026-09-12T13:27:00.6556585+08:00。此时尚未读取组合案例，也未揭示任何触发期望。

| ID | 可见 prompt | 可见 context | 冻结判断 | 冻结解释 |
| --- | --- | --- | --- | --- |
| DBG-T01 | 插件面板偶尔不更新，帮我定位并修复。 | 游戏 Lua 插件 | trigger | 明确是插件界面的偶发失效，直接符合错误定位与修复范围。 |
| DBG-T02 | 切换关卡后异步回调崩溃。 | UE5 C++ | trigger | 已给出崩溃及出现条件，属于明确故障目标。 |
| DBG-T03 | 设计一个新的背包界面。 | 没有现有故障 | no_trigger | 是新功能/界面设计，没有排障对象；描述明确排除纯功能设计。 |
| DBG-T04 | 解释这个正常函数的输入输出。 | 无错误或审查要求 | no_trigger | 正常代码说明，没有故障目标，处于明确排除范围。 |
| DBG-T05 | 这个不对。 | 需要由附件或前文确定是否存在异常 | conditional | 当前无法区分实际异常、审美偏好或需求调整；附件/前文确认故障后才触发。 |
| DBG-T06 | 帮我优化。 | 若现有证据是性能回退才触发 | conditional | 泛化优化请求未建立故障目标；存在性能回退证据时符合 regression 排障范围。 |
| BP-T01 | 蓝图里两个 Actor 怎么通过接口通信？ | UE5 Blueprint | trigger | 明确操作 UE5 蓝图接口，属于描述中的图表与 interface 工作。 |
| BP-T02 | Widget Blueprint 首次打开 Accessed None。 | UE5 事件图 | trigger | Widget Blueprint 事件图故障及 Accessed None 都被描述直接覆盖。 |
| BP-T03 | 调整 Maya 节点网络。 | Maya | no_trigger | 属于其他软件节点图，描述明确排除。 |
| BP-T04 | 修复这个纯 C++ UObject 成员声明。 | 没有蓝图资产或图表任务 | no_trigger | 操作目标仅为 C++ 声明，即便是 UObject 也不产生蓝图图表任务。 |
| BP-T05 | 这个节点连不上。 | 需要截图、节点文本或工程确定是否为蓝图而非材质图 | conditional | 节点类型未定；确认是 UE 蓝图才触发，材质图或其他节点图不触发。 |
| BP-T06 | 修改背包初始化。 | 若改动是蓝图节点则触发；只修改 C++ 实现则不触发 | conditional | 名称不能确认实现载体；修改蓝图节点触发，仅 C++ 实现不触发。 |
| CPP-T01 | 把这个 UObject 函数暴露给蓝图，并检查模块依赖。 | UE5 C++ 模块 | trigger | UE5 C++ 的反射暴露与模块依赖都在描述范围内。 |
| CPP-T02 | 异步加载回调切关后崩溃。 | UE5 C++ UserWidget | trigger | UE C++ 回调与跨关卡生命周期问题，符合 async callbacks 与生命周期范围。 |
| CPP-T03 | 用 C++ 写一个控制台计算器。 | 标准 C++ | no_trigger | 标准 C++ 项目没有 UE 上下文，属于明确排除范围。 |
| CPP-T04 | MFC 工具布局需要调整。 | MFC 桌面工具 | no_trigger | MFC 被明确排除，而且本例目标是工具布局。 |
| CPP-T05 | 这个组件初始化有问题。 | 需由代码和工程判断是否为 UE C++ 组件 | conditional | 组件一词不足以定位语言与框架；确认 UE C++ 实现后才触发。 |
| CPP-T06 | 背包接口改一下。 | 如果改动 C++ 的反射接口则触发；纯蓝图连线不触发 | conditional | 需确认改动载体；UE C++ 反射接口符合范围，纯蓝图连线不符合。 |
| UI-T01 | 给战斗 HUD 重新安排团队血量与技能冷却。 | 游戏 UI，沿用当前框架 | trigger | 属于现有游戏 HUD 的信息结构和布局调整。 |
| UI-T02 | MFC 工具窗口增加底部日志，考虑键盘操作和缩放。 | 已有 MFC 左中右布局 | trigger | 工具窗口布局、键盘交互和缩放符合跨现有框架的 UI 设计范围。 |
| UI-T03 | 优化排序算法的时间复杂度。 | 纯后台数据处理，无界面变化 | no_trigger | 纯后台算法且没有界面任务，描述明确排除。 |
| UI-T04 | 用 Photoshop 修去照片背景的电线。 | 图片修整，无界面设计任务 | no_trigger | 修改照片内容不涉及软件界面设计，落入仅制作/处理图片的排除边界。 |
| UI-T05 | 按钮没反应。 | 若涉及命中层级、焦点或不可用状态则触发；若只是服务请求失败则按故障层排查 | conditional | 是否属于 UI 取决于原因；焦点、命中与状态触发，单纯服务失败不由 UI 设计负责。 |
| UI-T06 | 整理这个面板。 | 需要确认是软件界面布局、代码文件还是实体面板 | conditional | 面板所指不明；确认软件界面布局任务才触发。 |

冻结分布：trigger 8、no_trigger 8、conditional 8。该分布只是实际判断统计，不表示已与期望比较。
## 第二阶段：5 个组合选择与分工（已冻结，不随期望修改）

冻结时间：2026-09-12T13:27:51.4595744+08:00。读取 `D:/Project/Skills/evals/composition-cases.json` 时只输出 `id`、`prompt`、`context`。截至本节写入，尚未揭示 `expected_skills`、`expectations` 或任何触发案例的 `expected`、`reason`。

| ID | 可见 prompt | 可见 context | 冻结技能选择 | 冻结分工与边界 |
| --- | --- | --- | --- | --- |
| COM-01 | 用蓝图做一个背包界面，给出数据更新和布局方案。 | UE5，现有项目，尚无故障；本轮只做说明，没有资产工具 | skillforge-ue-blueprint; skillforge-ui-design | 蓝图技能负责数据、变量、事件与函数之间的更新路径说明；UI 技能负责背包信息结构、布局与交互状态。当前只输出方案，没有资产工具，不声称已创建或修改资产；无故障，不选 debugging；未要求 C++ 实现，不选 ue-cpp。 |
| COM-02 | C++ UserWidget 的按钮看得见但点不到，怀疑被 Overlay 遮挡，帮我排查。 | UE5，明确包含控件祖先层级与 C++ 回调 | skillforge-debugging; skillforge-ue-cpp; skillforge-ui-design | debugging 负责复现、区分假设并验证故障原因，不能把“怀疑遮挡”当作定论；ui-design 负责祖先层级、命中、焦点和可交互状态检查；ue-cpp 负责 UserWidget 回调、事件绑定及相关生命周期代码。没有蓝图图表任务，不因 UserWidget 一词额外选 ue-blueprint。 |
| COM-03 | 现有 MFC 工具增加底部日志面板，调整缩小窗口时的布局。 | Windows MFC，没有 UE 或故障 | skillforge-ui-design | UI 技能负责现有框架内日志面板的信息层次、空间分配、缩放与操作可达性。MFC 不属于 UE C++；当前是新增和布局调整，没有故障目标，不选 debugging。 |
| COM-04 | MFC 日志列表滚动时不断回到顶部，定位并修复。 | MFC，实时更新导致界面交互异常 | skillforge-debugging; skillforge-ui-design | debugging 负责复现实时更新与滚动复位的关系，定位刷新或状态更新原因并验证修复；ui-design 负责滚动位置、用户正在浏览历史内容时的状态与新日志交互策略。UI 交互故障可以组合排障；MFC 不选两个 UE 技能。 |
| COM-05 | 写一个普通 C++ 命令行程序输出 hello。 | 没有 UE、UI 或故障 | 无（空集合） | 四个描述均不匹配：普通 C++ 不是 UE C++，命令行 hello 没有蓝图、界面布局或故障目标。交由通用编程能力完成，不强行套用本次四技能。 |

以上共 29 个判断已先后写入并冻结。后续只追加期望对比，不更改本节或上一节的答案与解释。组合选择只是基于元数据的分工提案，没有读取正文、执行技能流程或检验产物。

## 第三阶段：揭示期望后追加比较

比较记录时间：2026-09-12T13:29:51.9879002+08:00。前两阶段冻结稿 SHA-256：`21A623155A0030BBBC02172A80F8E95EC033A4AA1BB27CDC1B97AD6CEB36F65B`。本阶段读取指定案例的期望字段，仅追加比较，不修改冻结判断。

### 触发逐例比较

| ID | 冻结判断 | 期望 expected | 一致 | 原始 reason |
| --- | --- | --- | --- | --- |
| DBG-T01 | trigger | trigger | 是 | 明确异常及诊断目标，不限语言。 |
| DBG-T02 | trigger | trigger | 是 | 运行故障，可组合 UE C++。 |
| DBG-T03 | no_trigger | no_trigger | 是 | 功能与布局设计不自动启动排障。 |
| DBG-T04 | no_trigger | no_trigger | 是 | 普通代码阅读。 |
| DBG-T05 | conditional | conditional | 是 | 先确定用户指的是故障还是审美偏好。 |
| DBG-T06 | conditional | conditional | 是 | 没有问题指标时不能推断故障。 |
| BP-T01 | trigger | trigger | 是 | 蓝图通信设计。 |
| BP-T02 | trigger | trigger | 是 | 蓝图初始化故障，可组合排障。 |
| BP-T03 | no_trigger | no_trigger | 是 | 其他软件节点图不是 Unreal Blueprint。 |
| BP-T04 | no_trigger | no_trigger | 是 | 交由 UE C++，不重复加载蓝图图表流程。 |
| BP-T05 | conditional | conditional | 是 | 以实际图类型确定边界。 |
| BP-T06 | conditional | conditional | 是 | 按实际修改层选择。 |
| CPP-T01 | trigger | trigger | 是 | 反射与跨模块接口。 |
| CPP-T02 | trigger | trigger | 是 | 对象与回调生命周期，可组合排障。 |
| CPP-T03 | no_trigger | no_trigger | 是 | 没有 Unreal 工程。 |
| CPP-T04 | no_trigger | no_trigger | 是 | 同为 C++ 不代表适用 UE 规则。 |
| CPP-T05 | conditional | conditional | 是 | 组件一词跨框架，不能单靠词语匹配。 |
| CPP-T06 | conditional | conditional | 是 | 以实际修改层确定技能。 |
| UI-T01 | trigger | trigger | 是 | HUD 信息层级和布局。 |
| UI-T02 | trigger | trigger | 是 | 通用工具界面设计，不触发 UE 专属流程。 |
| UI-T03 | no_trigger | no_trigger | 是 | 不涉及 UI 设计。 |
| UI-T04 | no_trigger | no_trigger | 是 | 仅制作图片不在边界内。 |
| UI-T05 | conditional | conditional | 是 | 先确定故障层，不能只按按钮一词加载布局流程。 |
| UI-T06 | conditional | conditional | 是 | 需要任务对象才能判断。 |

触发匹配：24/24；每个技能 6/6。正例 8/8、反例 8/8、条件例 8/8。未发现标签偏差。

### 组合集合比较（忽略选择顺序）

| ID | 冻结集合 | 期望 expected_skills | 一致 |
| --- | --- | --- | --- |
| COM-01 | skillforge-ue-blueprint; skillforge-ui-design | skillforge-ue-blueprint; skillforge-ui-design | 是 |
| COM-02 | skillforge-debugging; skillforge-ue-cpp; skillforge-ui-design | skillforge-debugging; skillforge-ue-cpp; skillforge-ui-design | 是 |
| COM-03 | skillforge-ui-design | skillforge-ui-design | 是 |
| COM-04 | skillforge-debugging; skillforge-ui-design | skillforge-debugging; skillforge-ui-design | 是 |
| COM-05 | 无（空集合） | 无（空集合） | 是 |

组合技能集合匹配：5/5。未发现遗漏或多选。

### 组合分工对 expectations 的逐项覆盖

以下是同一评测者对冻结简短分工的揭示后自查。“覆盖”只表示冻结文本明确表达了分工或边界，不表示真实执行通过；“部分覆盖/未证明”保留原答案中的欠缺，不补写后倒算通过。

| ID / 项 | 原始 expectation | 冻结文本的具体依据与欠缺 | 覆盖判断 |
| --- | --- | --- | --- |
| COM-01 / 1 | 蓝图负责对象、节点和数据流，UI 负责布局与交互，复用同一份任务目标 | 已分配蓝图更新路径与 UI 布局/交互，但未明确对象职责及复用同一份任务目标。 | 部分覆盖 |
| COM-01 / 2 | 没有故障时不额外启动排障 | 明确“无故障，不选 debugging”。 | 覆盖 |
| COM-01 / 3 | 准确交付说明，不声称已经修改或保存蓝图 | 明确“只输出方案，没有资产工具，不声称已创建或修改资产”。 | 覆盖 |
| COM-02 / 1 | 先共享一条输入到业务回调的证据链，不重复三遍启动流程 | 按三个技能划分领域，但没有明确一条输入至业务回调的共享证据链，也没有声明只启动一次。 | 未证明 |
| COM-02 / 2 | 既检查命中路径，也检查绑定、生命周期和业务回显 | 明确祖先层级、命中、焦点、回调、绑定和生命周期；未提业务回显。 | 部分覆盖 |
| COM-02 / 3 | 按当前运行实例与版本验证，不把单一属性建议当成所有根因 | 明确不把 Overlay 猜测当定论；未要求当前运行实例与版本验证。 | 部分覆盖 |
| COM-03 / 1 | 保留 MFC 和既有工作台布局 | 明确现有框架内调整并识别 MFC；未明确保留既有工作台布局结构。 | 部分覆盖 |
| COM-03 / 2 | 不触发 UE 技能或引入 UMG/Slate | 只选择 UI 技能，明确 MFC 不属于 UE C++，没有引入 UMG/Slate。 | 覆盖 |
| COM-03 / 3 | 给出空间不足、键盘焦点和日志更新的相关验证 | 提到空间分配、缩放、操作可达性，但没有给出空间不足、键盘焦点与日志更新的验证方案。 | 未证明 |
| COM-04 / 1 | 按更新与滚动状态边界查原因 | 明确复现实时更新与滚动复位的关系，并定位刷新或状态更新原因。 | 覆盖 |
| COM-04 / 2 | 区分跟随最新和用户手动浏览状态 | 提到用户浏览历史内容及新日志交互策略，但未明确区分跟随最新与手动浏览两种状态。 | 部分覆盖 |
| COM-04 / 3 | 不触发 UE 技能 | 明确 MFC 不选两个 UE 技能。 | 覆盖 |
| COM-05 / 1 | 四个技能均不应触发 | 冻结技能集合为空，并解释四个描述均不匹配。 | 覆盖 |
| COM-05 / 2 | 不因为 C++ 字样推断 Unreal 工程 | 明确普通 C++ 不是 UE C++。 | 覆盖 |

14 项分工文本检查中，覆盖 7、部分覆盖 5、未证明 2。这不是 14 项行为测试的通过率；本阶段有意只使用名称与描述，没有完整方案、技能正文或项目运行证据。

## 读取清单与结论边界

四技能读取路径如下；SKILL.md 只读前言的名称/描述。案例在冻结前只输出输入字段，冻结后才输出及比较期望。

| 技能 | 元数据文件 | 触发案例文件 |
| --- | --- | --- |
| skillforge-debugging | `D:/Project/Skills/skills/skillforge-debugging/SKILL.md` | `D:/Project/Skills/skills/skillforge-debugging/evals/trigger-cases.json` |
| skillforge-ue-blueprint | `D:/Project/Skills/skills/skillforge-ue-blueprint/SKILL.md` | `D:/Project/Skills/skills/skillforge-ue-blueprint/evals/trigger-cases.json` |
| skillforge-ue-cpp | `D:/Project/Skills/skills/skillforge-ue-cpp/SKILL.md` | `D:/Project/Skills/skills/skillforge-ue-cpp/evals/trigger-cases.json` |
| skillforge-ui-design | `D:/Project/Skills/skills/skillforge-ui-design/SKILL.md` | `D:/Project/Skills/skills/skillforge-ui-design/evals/trigger-cases.json` |

另读取 `D:/Project/Skills/evals/README.md`、`D:/Project/Skills/evals/composition-cases.json`、上述宿主 using-superpowers 指令及本报告自身用于提取冻结答案和校验。仅写入本报告，没有改动案例、描述、其他报告或真实工程。

本轮能支持：给定这 29 个 prompt/context，评测者仅根据四个描述作出的标签和技能集合选择与案例期望一致。不能支持：宿主能自动激活这些技能、正文组合不存在冲突、真实工程修复或资产编辑成功，或对其他模型、Agent、无提示上下文同样有效。组合分工的行为要求仍有上述欠缺；它们未被包装为选择失败，也未因选择正确被包装为行为成功。

结果为单次描述匹配冒烟与评测者自查，不是独立验收者评分或用户验收。后续若读取正文进行组合方案检查，应另存为已见期望的非盲检查，不能回写或改变这里的冻结判断。