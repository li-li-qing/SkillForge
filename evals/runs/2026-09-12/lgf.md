# LGF 新技能基线文本评测

- 日期：2026-09-12。
- 条件：未加载本次新 LGF 技能；仅先读取 `evals/README.md`，六题使用委派消息内嵌题面。
- 模型：继承宿主模型设置；精确后端模型 ID 不可见，不从产品名称推断。
- 污染限制：宿主系统规则、技能名称和目录仍在上下文中，不能声称完全无技能背景。本轮未读取任何技能正文、项目源码、其他评测报告，也未浏览网络或运行工程。
- 前次尝试曾提前看到评分点，已废弃且未产生答案；本次为新的有效上下文。
- 工具记录：冻结前仅用 `exec_command` 读取 `evals/README.md`；用 `apply_patch` 一次写入以下六题原始答案。随后才读取指定行为用例的 expectations，并仅追加自评。
- 评测范围：文字方案；没有编译、编辑器、多人联机或真实项目验证证据。下面的源码核对和测试均为待执行计划。

## 冻结原始答案

### LGF-01

默认返回失败只能说明基类没有完成具体门的执行逻辑，不能证明必须重写交互系统。拿到源码后应从 ALInteractableActorBase 的反射声明、调用链和示例蓝图寻找可覆写事件、接口及执行前检查；核对是否为 BlueprintNativeEvent、谁调用以及蓝图父实现的行为，不凭名称假定存在某个节点。先确定门状态的数据所有者与交互入口，再创建门蓝图并覆写已确认的扩展点，接入交互组件、目标发现、提示与请求链，最后绑定门状态到表现。门通常不是客户端拥有的 Actor，客户端应经自己拥有的 Controller、Pawn 或项目既有交互请求入口向服务器请求；服务器重新检查目标、距离、权限、当前状态及并发条件。请求返回 true 不应直接等同于权威开门成功，永久开门应由服务器改变可复制的持久状态，客户端依据状态更新播放或定位动画，迟加入者也能恢复。验证应包含 Host、远端客户端、不可达或无权限请求、重复点击、两人同时开门、迟加入与相关性恢复；记录请求接收、权威执行、状态复制和表现刷新四个阶段。本轮只有方案，真实扩展点名称与返回值语义仍待源码确认。

### LGF-02

先按职责核对依赖图和接口，而不是按模块名称直接下结论。UINavigation 应集中维护路由栈、返回历史和导航策略，UMG 与 CommonUI Presenter 负责把同一导航状态变成各自控件及输入焦点；双份历史会造成返回和切换不一致。UIContracts 应提供不依赖具体 Widget 的契约，UIExtension 处理扩展点注册与生命周期，WorldUIRuntime 与 WorldUI 的边界要依据实际公开类型确认，避免玩法 Runtime 的 Public 接口拉入客户端 Widget、Slate 或编辑器依赖。摄像机、投影和界面呈现应以本地玩家及客户端世界为前提，Dedicated Server 不应创建这些对象。UI 不更新时沿数据源、订阅、模型映射、Presenter、控件绑定逐段定位：检查权威数据是否已复制、事件是否发出、注册是否发生在对象就绪后、切换 Pawn 或 LocalPlayer 后是否仍绑旧对象、注销与重建是否对称、是否更新了隐藏实例。再分辨导航变化、数据变化和世界投影更新，不用每帧强制刷新掩盖漏订阅。计划以同一导航用例分别验证 UMG/CommonUI、双本地玩家、重开界面、切换 Pawn 及 Dedicated Server 启动；没有源码和环境，无法确认当前模块已经遵守上述边界。

### LGF-03

先分别解释“本地受理请求”“服务器批准启动”“动作完成”三件事。RequestStartActionLock 的 bool 可能只说明参数有效或请求已发出；远端 true 后服务器仍可因状态、竞争或权限拒绝，因此不能据此统一更改返回类型，更不能以 Proxy 的 Ended 发奖励。需要核对 Host 是否走直接权威路径、远端是否排队发送，拒绝和结束各自通过哪个事件通知，Proxy 销毁、取消、失败与权威完成是否共用 Ended。连续 Start 后 Cancel 应追踪每次请求的唯一标识、客户端标识到服务器实例的对应、取消针对哪个实例，以及启动确认前取消是否被保存或丢弃；特别检查旧回调覆盖新句柄、多个锁共用当前实例和事件解绑时机。接入层分别维护 Pending、Active、Rejected、Cancelled、Completed 等语义状态，以关联标识过滤迟到响应，明确再次启动是替换还是并行；启动、取消均沿项目现有拥有者请求通道。奖励只在服务器已确认的完成路径执行，并以实例标识去重。验证方案覆盖 Host/远端、延迟与丢包、Start-Start-Cancel、未确认即取消、拒绝后 Ended、旧实例晚结束、断线和销毁；逐条对照请求及权威事件顺序，尚不能断言是哪处实现缺陷。

### LGF-04

死亡禁用移动钩子返回 false 表示默认路径未处理，应核对调用者是否存在回退行为，再在 Pawn/Mover 适配层接入真实移动禁用、输入抑制及复活恢复；不能假设 CharacterMovement 的接口适用于 Mover。AbilitySet 软类 Get() 仅取得已加载对象，空值首先指向未加载或引用无效，不构成同步加载卡顿证据。在 Tick 中 LoadSynchronous 会把等待塞进高频路径，应使用资源准备阶段的异步加载并检查失败。换 Pawn 后旧回调仍授予旧 Avatar 是生命周期和关联校验问题：请求保存弱对象引用、Avatar 身份及加载代次，完成时重新确认拥有者存活、当前 Avatar 和代次匹配，取消旧句柄并清理已授予能力；仅取消不足以替代回调守卫。长期背包和 ASC 的位置应依据跨重生存续需求与框架既有所有权决定，通常考察 PlayerState 等长期拥有者，Pawn 作为 Avatar 并维护 ActorInfo 更新；不要因接 Mover 顺便整体搬迁。验证计划覆盖死亡/复活、快速换 Pawn、加载晚到、引用缺失、断线、Host/远端，检查能力重复授予和旧移动输入残留。本轮不能修改工程，具体钩子签名、Mover 版本及现有 ASC 归属均需后续核实。

### LGF-05

任务只授权学习和整理技能，应产出来源索引、事实与建议的区分、冲突记录及待验证清单，不实现 WorldMap 或改项目。P0 冻结描述阶段范围，O3 是 P1 的前置条件，不能把未完成前置当作已经获准进入 P1；应核对文档版本、状态说明与决策来源。文件名带 CONFIRMED 不覆盖正文“仅记录”的语义，相关拓扑应标为记录或提案；当前没有 WorldMap 模块，不能整理成现存实现。验证工具也要分清历史入口和现场可执行入口：旧 Python 路径不存在就记录为不可执行，不能报告脚本通过。UIEditor Commandlet 可以列作替代验证候选，但须核对其参数、覆盖范围和输出，不能仅凭存在宣称等价。宿主定位依据真实 Game.uproject 与 GameEditor.Target.cs，Saved/BuildPlugin/HostProject 属构建产物，不用它替代项目身份；具体构建和 Commandlet 命令应以实际引擎位置、模块及入口声明确认后再给出。报告分别写明静态阅读结论、可用验证入口、尚未执行的检查及缺失证据。本轮没有运行授权或工程上下文，不把编译、Commandlet、编辑器和联机结果写成已通过，也不借验证之名生成模块或推进开发阶段。

### LGF-06

先分开权威库存、持久化记录、复制增量和 UI 投影。持久化应保存稳定物品或实例 ID、定义引用、数量及业务属性，并做版本迁移和服务端恢复校验；UIData 和 FastArray ReplicationID 是表现或复制机制的数据，不能当永久物品身份。共享仓库可见性应按授权观察者核对复制设计，所有列表统一 OwnerOnly 可能让公会成员失去共享更新。客户端发取物命令，服务器校验成员资格、容量、当前库存及并发版本，原子变更并通过复制或明确权威回执通知；客户端不能直接改复制数组，提交成功只显示处理中，确认后才显示已领取。Quest 重试应保持同一 RequestId 对应相同完整请求语义；更换奖励选项是新请求，服务器也应拒绝同 ID 不同参数，并保证奖励只发一次。对话点击应携带会话或交互实例、节点或版本及 OptionId，让服务器核对当前有效会话、可选集合、前置条件和目标；单传 OptionId 无法排除迟到旧点击。检查路线从存档结构、库存写入口、权限与复制受众，走到事务、幂等账本和界面确认链。验证计划覆盖多人抢最后一件、越权旁观、重连恢复、同 ID 改参数、重复回执、旧对话迟到与写入失败；现有实现是否安全仍需源码和运行证据。

---

以上六题原始回答已冻结。评分期望在此之后才读取；后续内容只能追加。

## 冻结后自评（不是独立审阅或用户验收）

冻结后工具记录：通过 `exec_command` 读取 `skills/skillforge-lgf/evals/behavior-cases.json`，输出包含既有题面与 expectations；未读取其他文件。以 `apply_patch` 仅追加本节。没有根据评分点修改上述原答案。

判定方式：pass 表示原答案实质覆盖本项；partial 表示方向正确但缺少本项的重要具体边界；fail 表示主要要求未覆盖。符号拼写未命中本身不构成失败，也不把泛泛的“待查源码”当作覆盖具体要求。

| 题目／项 | 判定 | 原答案依据与缺口 |
| --- | --- | --- |
| LGF-01 / 1 | partial | 已要求从反射声明、调用链确认 BlueprintNativeEvent，并反对默认失败即不能蓝图扩展；未虚构门资产。但没有明确提出检查 Authority 扩展本身与 K2 入口的对应关系。 |
| LGF-01 / 2 | partial | 已先建门蓝图再接交互组件与请求链，并明确世界门通常非客户端拥有。缺少先创建交互选项、输入等所有被引用内容的顺序，也未定位既有 Agent 的 Request 入口。 |
| LGF-01 / 3 | partial | 已区分请求 true 与权威开门，服务器复核并写复制状态。没有明确提出 Host 与 Remote 复用业务校验、Host 不必自发 RPC。 |
| LGF-01 / 4 | pass | 明确覆盖 Host、远端、迟加入、相关性恢复、拒绝与并发，并注明真实扩展点名称及编辑器验证均未确认。 |
| LGF-02 / 1 | partial | 明确唯一导航状态与两个 Presenter，禁止双份历史。没有把唯一状态和输入仲裁明确限定为每个 LocalPlayer。 |
| LGF-02 / 2 | partial | 已描述中立契约、扩展点生命周期和客户端表现边界，未把 WorldUI 当 WorldMap；但没有明确 UIExtension 的非页面职责，也未明确界定服务器安全的 WorldUIRuntime。 |
| LGF-02 / 3 | partial | 要求核对依赖图和 Public 类型，禁止 Runtime 拉入客户端 Widget，并排除 Dedicated Server 摄像机。缺少 uplugin、Build.cs 的具体核对及 Authority 与本地 UI 分维度、Listen Host 可以呈现 UI 的说明。 |
| LGF-02 / 4 | partial | 有数据源到 Presenter 的分段排查、LocalPlayer 和旧实例订阅核对、多本地玩家及服务器验证计划。缺少路由 Receipt/Result、Provider、Travel 和返回输入的针对性检查。 |
| LGF-03 / 1 | pass | 开头区分请求受理、服务器批准与完成，解释远端 true 后仍可能拒绝，要求核对 Host/远端路径与事件契约，并明确不为文字统一而改返回类型。没有声称实际 API 已核验。 |
| LGF-03 / 2 | partial | 有 Host 直接路径、远端排队及拥有者请求通道的检查，不声称已修复。没有提出 Start/Cancel 共享预算，也未准确列出 Pawn owner RPC 与 PlayerState 路径及版本范围。 |
| LGF-03 / 3 | partial | 区分取消、替换、拒绝与完成，禁止 Proxy Ended 作为奖励真值，要求服务器去重；但未说明锁状态本身不是完整业务授权。 |
| LGF-03 / 4 | partial | 保持解释和接入方案范围，有分端事件、销毁与清理测试。没有明确锁必须由 CMC/Mover/GAS 消费，也缺少限频取消与 JIP 验证。 |
| LGF-04 / 1 | partial | 指出不能将 CharacterMovement 接口直接套给 Pawn/Mover，默认 false 不代表已处理，须检查回退。没有辨明 Pawn 钩子是 C++ virtual 及不可默认蓝图覆写，也没有确认 Character 已有实现的对照点。 |
| LGF-04 / 2 | partial | 正确解释软类 Get() 和未加载，拒绝 Tick 中 LoadSynchronous，建议异步准备。缺少资产扫描、Cook 和 ASC 就绪的具体检查。 |
| LGF-04 / 3 | partial | 分开长期 PlayerState 候选与 Pawn Avatar，回调检查弱引用、当前 Avatar 及代次，清理授予和旧句柄。没有明确校验当前 ASC 实例，也未把旧输入解绑和授予／撤销成对落实为接入步骤。 |
| LGF-04 / 4 | fail | 未覆盖 Mesh 与 AuthorityTrace 的用途区分，也没有动画接口／Water 与 GASP、通用 Mover 的能力边界。虽有死亡复活和旧回调测试，仍不足以满足本项主要要求。 |
| LGF-05 / 1 | pass | 明确学习整理不实施 WorldMap 或重构，区分阶段前置、文档记录和实际不存在的模块；不以 CONFIRMED 文件名当实现证据。 |
| LGF-05 / 2 | fail | 提出来源索引，但没有要求沿当前 Docs 导航和主题唯一入口，也未说明不复制 API 教程、不修改冻结历史或不把所有模块展开为新技能。 |
| LGF-05 / 3 | pass | 明确以 Game.uproject、GameEditor.Target.cs 定位，排除 Saved/BuildPlugin/HostProject；脚本缺失单独报告，Commandlet 是待核对的可用候选，没有猜宿主名称。 |
| LGF-05 / 4 | partial | 已分开静态阅读、可用入口与未执行检查，不把编译、编辑器或联机写为通过。未细分结构／符号／测试声明与 UHT、Cook、资产验证，也未明确迁移报告无法替代全部网络测试。 |
| LGF-06 / 1 | partial | Authority 校验稳定身份、权限与库存，UI 仅呈现，请求成功先显示处理中。没有明确指定经玩家拥有的请求入口传送仓库命令。 |
| LGF-06 / 2 | partial | 正确排除 ReplicationID 和 UIData 作为存档身份，建议业务记录、版本迁移与恢复校验。未核对条目／容器序列化、Dirty 和复制回调，也未讨论逐 Item OnRep。 |
| LGF-06 / 3 | partial | 反对共享列表全部 OwnerOnly，按授权观察者检查。缺少当前动态复制配置、容器消费者、JIP 和相关性恢复的专项核对。 |
| LGF-06 / 4 | pass | 明确 RequestId 绑定完整业务参数，换选项使用新请求；对话需会话实例、节点或版本及 OptionId，拒绝迟到旧点击。没有虚构具体签名，保留源码待核实范围。 |

汇总：24 项中 **pass 5、partial 17、fail 2**。这是基线回答者的自查，反映本次文字答案覆盖范围；不能推断真实工程能通过测试，也不能把宿主背景知识计为本次新技能效果。

文件完整性核对：最后通过 `exec_command` 只读取本报告并统计，实际得到 6 个答案、24 个评分行、5 pass、17 partial、2 fail；本句由末次 `apply_patch` 追加。未运行项目测试。

<!-- LGF-LOADED-20260912-BEGIN -->
## 独立加载后评测（2026-09-12）

本节只追加，不读取或更改此前基线。模型沿用宿主默认设置，具体后台模型 ID 不可见。宿主已提供通用系统规则与其他技能目录，背景能力可能存在；本节不将其归因于新技能。未加载其他报告、已安装技能正文、真实 LGF 工程，也未联网。未执行工程或编辑器验证。

### 第一阶段：冻结触发原始判断

实际读取：`evals/README.md`；通过 PowerShell 在进程内读取并仅投影 `skills/skillforge-lgf/SKILL.md` YAML 的 name/description；通过 PowerShell 在进程内读取并仅投影 `skills/skillforge-lgf/evals/trigger-cases.json` 的 id/prompt/context。模型未见技能正文及 expected/reason。工具为 functions.exec → exec_command（PowerShell）。原始判断一次性写入后冻结。

| ID | 原始判断 | 判断依据 |
|---|---|---|
| LGF-T01 | trigger | 明确用 LGF 实现交互且工程已启用。 |
| LGF-T02 | trigger | 明确为 LGF 导航及 Presenter 的输入恢复故障。 |
| LGF-T03 | trigger | 明确维护 LGF API 和项目文档。 |
| LGF-T04 | no_trigger | 普通 UE 生命周期解释，没有 LGF 使用证据。 |
| LGF-T05 | no_trigger | 属于 ArcheRage Lua 插件，与 LGF 无关。 |
| LGF-T06 | conditional | CommonUI 本身不足以触发；确认工程使用 LGF 才加载。 |
| LGF-T07 | conditional | LGame 目录名不足以判断；先确认插件及版本。 |
| LGF-T08 | trigger | 明确 LGF 接入，纯 UMG 仍属于其适用范围。 |

冻结计数：8 题；trigger 4、no_trigger 2、conditional 2。上述结果写入时未读取触发期望。

### 触发自查（期望揭示后）

冻结后才以 PowerShell 投影读取同一 trigger-cases.json 的 id/expected/reason。LGF-T01 至 LGF-T08 逐题均与期望一致：8/8。T06、T07 保留有条件触发，没有因 UI 术语或目录名直接加载。这只是描述匹配检查，不是宿主自动发现机制实测；期望揭示后的评判由原回答者完成，非独立盲审。

### 第二阶段：冻结行为原始答案

本阶段实际读取 `skills/skillforge-lgf/SKILL.md` 全文及 `references/project-map.md`、`integration.md`、`network-and-state.md`、`ui-platform.md`、`avatar-and-assets.md`、`validation-and-evolution.md`、`sources.md` 七个参考文件；行为用例只通过 PowerShell 读取 JSON 并投影 id/prompt，模型未见 expectations。仍只使用 functions.exec → exec_command，写报告使用 Add-Content -LiteralPath（UTF-8）。未读取真实源码、项目资产或其他报告。

以下项目事实来自资料所述 2026-09-12 取材、提交 2088589f207ce696b7e73095e2dd7df351f1a0c4、LGF 1.0.0 Beta / UE 5.7 现场，属于有版本范围的参考。本轮没有独立复核该源码。下列六题仅提供分析、接入顺序和待执行验收；准确签名、蓝图显示名、配置与实现仍待实际工程核对。

#### LGF-01 原始答案

默认执行失败只能说明基类没有门的具体业务，不能据此判定必须重写交互系统。参考版本的 ALInteractableActorBase 已有 InteractionComponent、AccessPolicyComponent 和 Actor 复制；应从 API/Tutorial 定位对应头文件和实现，核对 K2_BuildDynamicInteractionOptions、K2_CanHandleInteractionAuthority、K2_HandleInteractionAuthority 的 BlueprintNativeEvent 声明、参数和默认实现。本轮不能把这些参考中的签名当作现场已经检查过的节点。

建议先确认消费工程采用的玩家类栈和交互组件，列出尚待创建的门 Mesh/蓝图、输入资产和提示 Widget。创建 ALInteractableActorBase 的项目蓝图子类后配置 Mesh、基础选项与权限策略；需要动态选项时实现只读的 K2_BuildDynamicInteractionOptions。接着实现 Authority 检查钩子验证钥匙和当前门状态，在 Authority 执行钩子内修改项目定义的门开关真值并返回业务结果。不要重复添加基类已有组件。

输入资产与 Mapping 配置创建后，接拥有侧 InteractionInput/InteractionAgent、Avatar Detector，再接现有 RequestInteract。玩家通常不拥有世界门 Actor，不能把客户端直接在门上 Server RPC 作为路径。Authority 仍应重查距离、目标有效性、权限和门状态。提示 Widget 按 InteractionWidgetInitializer 契约初始化，读取 Detector UIData。输入提交 true 仅能按实际协议表示已提交或相应分支结果，不能直接确立永久开门。永久门状态由 Authority 修改并复制，远端以复制刷新；Host 也应有本地刷新途径，后加入者从状态恢复表现，不能只依赖一次动画或 Multicast。

待验收包括 Host、Remote Owner、非拥有观察者和后加入者；分别执行可开、无钥匙、超距、重复点击、门已开及目标失效，确认只发生允许的权威变更，提交提示与最终结果分开。当前交付是接线方案，未创建资产、编译蓝图或运行游戏。

#### LGF-02 原始答案

参考版本由每个 LocalPlayer 的 UINavigation 统一拥有 Route Stack、Back History、Presentation 选择和 Input Arbiter。UMG 与 CommonUI 是可替换的 Presenter Provider，应把实际呈现及 Ready/Failed 完成结果回交给同一导航所有者，分别维护历史会造成关闭、返回与输入恢复分叉。UIContracts 保持中立合同；UIExtension 用于非页面 HUD 扩展；WorldUIRuntime 提供服务器可用的 Source/Registry，WorldUI 管客户端摄像机、LOD、遮挡、预算和 Widget。Dedicated Server 不为此创建摄像机。

应核对实际 .uplugin Module Type 与 Build.cs，Runtime 玩法模块 Public 不应通过依赖客户端 Widget 来取得 UI 能力。客户端 Presenter 依赖中立合同，并在客户端装配。CommonUI 插件被启用也不能推出服务器应执行表现代码；Provider 注册还可能需要项目 C++，不能宣称所有注册函数都有蓝图节点。

UI 不更新时沿一条请求链检查：正确 LocalPlayer/Controller → Route 注册及标签/Payload → Request Receipt → 实际选中的 Provider/Presentation → Ready/Failed → 精确 InstanceId → 当前 Widget 的绑定和刷新。记录 RequestId、InstanceId、拥有者与代次，可区分请求尚未完成、注册缺失、旧实例回调和界面未消费数据。Receipt 不是呈现完成，应关联 OnNavigationRequestCompleted 的最终结果。Close 必须使用精确实例，不能用失效 ID 回退关闭别的页面；Replace 在新表现就绪前保留旧表现。统一 Input Arbiter 应处理输入策略，避免每个 Widget 独立 SetInputMode/抢焦点导致返回后仍锁输入。

异步加载完成、Controller 替换和 Travel 时，要验证 Provider Handle、实例身份、当前代次及注销，不能只判断 UObject 仍有效。待验证 UMG/CommonUI 两条路线的 Back、Close、Replace、加载失败、旧 InstanceId、多 LocalPlayer、HUD 共存及焦点和游戏输入恢复；模块依赖变化另需 Server 构建。以上均未在本轮执行。

#### LGF-03 原始答案

保留现有 bool API；解释或接入不授权统一修改返回类型。参考版本的远端 RequestStartActionLock true 表示已发起，Authority 直调分支可返回实际执行结果，因此同一个布尔值必须结合分支解释。UI 应区分提交、权威状态/结果和本地表现结束，不能据 true 发奖励。

Start 后 Cancel 偶尔无效需要查共享 RequestBudget：参考版本 Start/Cancel 使用同一预算，高频 Start 可能影响 Cancel，这只是待复核候选原因。还需核对 RPC 预算分支检查玩家 Pawn owner 的条件，组件 owner 为 Pawn 或 PlayerState 时怎样处理；Host 在 Request 内直接走 Authority 是允许的，不必强制给自己发 RPC，但要逐项对照 Remote 的预算、业务校验、结果与本地通知，才能定位差异，不能仅凭 Host 成功断言远端网络有故障。

事件也不能合并成“结束即完成”：参考中的自然完成在 Authority 广播 StateChanged 与 CompletedAuthority；Proxy OnRep 在序号改变且 active→inactive 时发 Ended，自然完成也可能触发它。替换旧锁时 Authority 会广播旧锁 Ended，而 Proxy 的 active→active 不满足同一条件，所以两端 Ended 次数未必一致。奖励应由 Authority 上明确的成功完成语义及去重身份决定，不能由 Proxy Ended 结算；取消和替换按业务各自处理。

接入前列出 consumer 是移动、动画、UI 还是奖励；状态或移动输入比例存在不代表 CMC/Mover/GAS 已接好。待验证矩阵包含 Host/Remote、Pawn/PlayerState owner、Start 连发后 Cancel、自然完成/取消/替换、JIP、死亡和销毁。日志应关联请求或锁序号、提交返回、预算拒绝、权威状态和各端事件，以权威完成及实际消费结果验收。本轮仅解释差异与接入边界，不改代码、不声称复现或验证成功。

#### LGF-04 原始答案

Pawn 死亡移动钩子默认 false 表示该路线没有替项目实现移动后端，不能推导 Mover 已自动接好。参考中的 AuthorityDisableAvatarMovementForDeath 与 AuthorityRestoreAvatarMovementAfterDeath 是 C++ virtual，不是 BlueprintNativeEvent；先查项目派生类是否已有覆盖。Character/CMC 路线有模式保存恢复，Pawn/Mover 应在项目派生类按实际后端实现成对禁用和恢复，记录恢复所需状态，并处理重复死亡/复活、Possess、Travel、销毁与网络纠正。Water 专用适配不能证明通用 Mover 生命周期已覆盖。

软类 Get() 只读取已加载对象，不是加载操作。参考中的 ServerGiveAbilitySet 在组件中先校验 Authority、配置与稳定身份，再访问已加载软类，未加载可返回 AssetNotLoaded；函数名带 Server 也不证明是 RPC。应先查 Definition/软引用、PrimaryAssetId 扫描和 Cook、预加载结果、ASC/Avatar ActorInfo 就绪、Tag 冲突与具体操作结果。不能把未就绪错误直接称同步加载卡顿，更不应在 Tick 中 LoadSynchronous 掩盖缺失流程。

旧异步加载晚到是身份和生命周期问题。用请求/授予代次、当前 ASC 与当前 Avatar 联合校验完成回调；对象仍有效不足以说明请求仍有效。换 Pawn 时取消或作废旧加载、解绑旧输入和 Delegate、清理 Timer，按实际 GrantHandle 撤销旧授予，更新 Owner/Avatar ActorInfo，待新资产与输入就绪后只接受当前代次授予。缺少异步就绪编排时明确列为项目接入待实现项。

保留 PlayerState 的长期 ASC、属性和背包等状态，PlayerController 负责拥有侧 Agent/输入，Pawn 负责当前 Avatar 与世界表现；把长期状态搬到 Pawn 会把替身生命周期混入持久真值。待验证已加载/未加载/错误资产、旧回调迟到、连续换 Pawn、重复授予、死亡复活、Host/Remote/Dedicated 和 Travel，确认只有当前 Avatar 获得当次能力且长期状态保留。本轮没有加载资产或执行工程。

#### LGF-05 原始答案

本轮只整理技能，记录事实、规范和设计前置，不创建 WorldMap 模块或搬迁生产类型。P0 冻结不等于 P1 已获准或已实现，O3 仍是前置；应沿当前 Docs/Decisions 导航及 WorldMap 主题入口整理其状态。文件名 CONFIRMED 不能覆盖正文“仅记录”，现有模块无 WorldMap 时应标为方案；WorldUI 也不是 WorldMap。冻结历史保留，新的反馈写入现行入口，避免复制另一个同义总览。

以题面 Game.uproject 与 GameEditor.Target.cs 确定真实宿主和 Editor Target，Saved/BuildPlugin/HostProject 是临时打包宿主，不拿它替代消费工程。未来执行时还需发现引擎路径、工程实际位置和配置；本题没有这些完整信息，不生成假定绝对路径的执行记录。

Scripts 不存在意味着旧 Python 拓扑命令不可用，报告该差异，不能假装跑过或为了满足旧文档重建脚本。已有 UIEditor Commandlet 仍是候选迁移验证路径；参考中是 ULGameplayUIMigrationCommandlet，实现文件可名为 LGameplayUIMigrationScanner。复核当前实现后可计划使用 UnrealEditor-Cmd.exe <实际 Game.uproject 路径> -run=LGameplayUIMigration -unattended -nop4 -nullrhi，检查退出码及预期 Saved/LGFUIRefactor/UIMigrationReport.json。扫描结果不能代替页面操作或网络回归。

技能维护应检查结构、相对链接、版本来源及触发/行为用例；没有修改反射/C++/模块或资产，不借此安排生产重构。本轮报告必须写明只有题面及参考分析，Commandlet、UHT/UBT、蓝图编译、PIE、网络、Cook/Package 均未执行。测试宏数量只能说明有声明；未来声称通过需记录目标、过滤器、实际执行数与输出。工作区链接可用不证明发布包包含 Docs/Backlog，发行任务另核对 FilterPlugin 与实际产物。

#### LGF-06 原始答案

先辨认公会仓库的稳定容器身份、物品业务身份、成员访问策略与保存边界，然后追踪 UI 查询 → 拥有侧 Agent Request → Authority 重新解析目标及权限 → 库存变更 → FastArray/结果事件 → 当前 UI 实例。UIData/ViewData 是呈现快照，不作为保存真值；FastArray ReplicationID/Key 是运行期同步身份，也不能持久化作物品 ID。保存模块支持的业务数据与身份，恢复走正式重建流程，并验证存取前后数量、实例身份和权限一致。

客户端不得直接改复制数组来完成领取。Authority 应检查当前权限、数量、目标和资源状态，处理竞争后修改真值；UI 提交成功先进入 Pending，等相关最终结果与复制确认才显示已领取。若有预测显示，必须可撤回且与请求关联。Host 的本地刷新和 JIP 恢复也应覆盖。

参考中 Inventory 使用动态复制条件，应按个人库存、世界容器、公会仓库分别检查实际 owner、消费者和相关性，统一 OwnerOnly 可能让其他授权查看者看不到共享仓库。检查 Item/Serializer、NetDeltaSerialize/Traits、Dirty 标记、OwnerComponent、增删改回调和清理；回调更新呈现或缓存，不能在客户端再提交库存变更，也不机械为每个 FastArray Item 增加 OnRep。

Quest 重试要同时核对 RequestId、QuestId、OperationType、PayloadId：同一逻辑请求重复应遵守缓存和幂等协议，换奖励选项已经改变业务参数，不能复用原 RequestId 冒充重试。限频拒绝与已执行业务结果分开，超时也不能证明未执行，须按结果关联和当前缓存合同处理。Dialogue 迟到点击需要 SessionId、ExpectedNodeId、OptionId 的会话和节点语境；通过公开 Agent Request 入口处理节点指纹，不仅传 OptionId，也不绕开门面拼内部 RPC。

待验证共享查看者和无权限者、并发领取、权限中途变化、重复请求、参数变更、超时重试、过期会话/节点、保存恢复及 JIP。分别记录 Authority 变更次数、结果归属、UI 呈现次数和最终保存数据，确认不重复奖励、不把迟到点击应用到新节点。当前仅是检查路线，未证明真实实现已满足这些性质。

原始行为答案冻结计数：6 题（LGF-01 至 LGF-06），在读取 expectations 前一次性追加，之后仅另增评分，不回改答案。

### 行为自查（期望揭示后）

六题原始答案冻结后，才用 PowerShell 投影读取 behavior-cases.json 的 id/expectations。下面逐项以已冻结文字为依据；未写出的关键边界不因参考文件中存在就计入答案。本轮是回答者自查，并非独立验收或盲审。

冻结后收到主任务通知并重读 project-map.md 与 sources.md：前者将“各自 UI”改为明确的五个适配模块，后者补了 Mesh/动画装配来源。这两处补正未改题面和期望；原始答案保持冻结，没有利用补正追加答案内容。原始回答所依赖的是先前读取版本；本次重读只记录资料修订。

| 项目 | 结果 | 已冻结答案证据与不足 |
|---|---|---|
| LGF-01.1 | pass | 指出默认失败只是未实现具体业务，列三个 K2 BlueprintNativeEvent 待核对，并明确门资产待创建。 |
| LGF-01.2 | pass | 明确先建门蓝图、配置和输入资产，再经拥有侧 Agent/RequestInteract；指出世界门一般不归玩家拥有。 |
| LGF-01.3 | partial | 已区分提交与业务结果，Authority 重查并修改复制真值；该题未明确说明 Host 与 Remote 校验等价且 Host 无需自发 RPC。LGF-03 的说明不补算本题覆盖。 |
| LGF-01.4 | pass | 列 Host 本地刷新、Remote、观察者、JIP 和权限/距离拒绝路径，注明节点待核对且编辑器未执行。 |
| LGF-02.1 | pass | 每 LocalPlayer 唯一导航/历史/输入所有者，双 Presenter 只呈现并反馈完成。 |
| LGF-02.2 | partial | 区分 UIContracts、UIExtension、WorldUIRuntime 和 WorldUI 的数据及运行端职责；该题未明确 WorldUI 不等于 WorldMap。 |
| LGF-02.3 | partial | 指出真实描述符/Build.cs、Runtime Public 客户端依赖错误及 Dedicated Server 无摄像机；未明确 Authority 与本地表现是独立维度、Listen Host 可以有 UI。 |
| LGF-02.4 | pass | 以 LocalPlayer→注册→Receipt→Provider→完成→实例→Widget 排查，并列多玩家、Travel、输入恢复和待执行 Server 构建。 |
| LGF-03.1 | pass | 区分远端提交与 Authority 执行 bool，不改 API；统一前言要求准确签名与实现待工程核对。 |
| LGF-03.2 | pass | 将共享预算及 Pawn/PlayerState owner、Host 直调差异写成参考版本的待复核候选原因，没有宣称复现或修复。 |
| LGF-03.3 | pass | 解释自然完成、取消、替换的 Authority/Proxy 事件差异，奖励由 Authority 明确完成语义及去重身份决定。 |
| LGF-03.4 | pass | 明确锁状态不表示移动/GAS 已装配，要求显式确认消费者并验收限频取消、分端、JIP 与死亡销毁。 |
| LGF-04.1 | pass | 区分 Character/CMC 已有逻辑与 Pawn C++ virtual，不当作蓝图事件；要求项目 Mover 成对处理。 |
| LGF-04.2 | pass | Get 只读取已加载类，列 AssetNotLoaded、扫描/Cook/预加载与 ASC 就绪，拒绝 Tick 同步加载方案。 |
| LGF-04.3 | pass | PlayerState 长期状态和 Pawn Avatar 分离，校验 ASC/Avatar/代次，解绑及 GrantHandle 撤销授予成对。 |
| LGF-04.4 | partial | 已说明 Water 适配不证明通用 Mover，并列死亡复活/Possess/Travel/迟到回调验证；未展开 Presentation/AuthorityTrace Mesh 与动画接口/GASP 边界。 |
| LGF-05.1 | pass | 以 P0/P1/O3、正文仅记录及模块缺失区分冻结设计与落地，学习范围不实施重构。 |
| LGF-05.2 | pass | 沿当前 Docs/Decisions 和主题入口组织，保留冻结历史、避免同义总览；方案没有复制 API 教程或展开新技能群。 |
| LGF-05.3 | pass | 明确 Game/GameEditor 与临时 HostProject 区别，旧脚本缺失不否定 UIEditor Commandlet。 |
| LGF-05.4 | pass | 技能结构、测试声明、构建/资产/PIE/Cook 等分开记录，明确迁移扫描不代替网络验证且均未执行。 |
| LGF-06.1 | pass | 拥有侧 Request 到 Authority 重解析身份/权限，UIData 仅呈现，最终结果前 Pending。 |
| LGF-06.2 | pass | 区分业务保存身份与 ReplicationID/Key，覆盖序列化、Dirty、回调及正式恢复，反对逐 Item 机械 OnRep。 |
| LGF-06.3 | pass | 根据动态条件、owner、消费者和相关性区分仓库，不统一 OwnerOnly；列授权共享、无权限与 JIP 验证。 |
| LGF-06.4 | pass | Quest 关联四类请求/业务字段，变更选项不能复用身份；Dialogue 保留会话/预期节点语境并检查迟到请求。前言与正文明确当前实现仍待核对。 |

行为汇总：24 项，pass 20、partial 4、fail 0。按题分别为 LGF-01 3/1/0，LGF-02 2/2/0，LGF-03 4/0/0，LGF-04 3/1/0，LGF-05 4/0/0，LGF-06 4/0/0（顺序 pass/partial/fail）。不折算为实际工程成功率。

限制：没有读取此前基线，因此本节不计算改善或更改基线评分。触发匹配只是描述层检查；单次文字行为自查不能证明其他模型、宿主发现机制或真实编辑器任务通过。四项 partial 表示原始答案对复合验收点覆盖不足，不从其他题或技能参考补记为通过。

<!-- LGF-LOADED-20260912-END -->

计数复核记录：使用 PowerShell 在进程内读取报告，按本次唯一 BEGIN/END 标记提取新增节，仅向模型输出计数；没有输出、阅读或使用基线内容。实际结果为触发行 8、冻结答案 6、评分行 24、pass 20、partial 4、fail 0，与汇总一致。上述核对只验证报告新增节的计数，不是工程测试。


## 维护者复核与本轮交付

本节由技能作者在读取两组冻结答案后复核，属于非盲维护者审阅，不冒充独立评审或用户验收。两组使用相同六个题面、继承模型设置和方案任务限制；基线没有新技能，加载组增加本包资料。精确模型 ID 不可见，已有宿主规则无法排除，因此只能报告本次样本的覆盖变化。

基线的通用 UE 方向多数正确，不能把缺少本项目信息解释成模型能力差。加载组增加了实际 K2 扩展、LocalPlayer 导航、ActionLock 预算与分端事件、Pawn C++ 钩子和请求身份等具体定位依据；这些提升来自有版本范围的项目材料，没有证明游戏修复成功。

对自评分作一项保守修正：加载组 LGF-03.3 应由 pass 记为 partial。原答案正确拒绝 Proxy Ended 发奖励，但没有明确锁状态本身不是完整业务授权，与基线同一项的缺口一致。保留原自评表和答案，不回改历史。其他逐项判断维持原记录。

| 条件 | pass | partial | fail | 口径 |
|---|---:|---:|---:|---|
| 未加载新技能 | 5 | 17 | 2 | 冻结后自评，维护者复核维持 |
| 加载本技能 | 19 | 5 | 0 | 自评20/4/0，经上述一项修正 |

仍有遗漏：门交互答案没有说明 Host/Remote 等价校验；UI 答案没有完整交代 Listen Host 本地 UI 与 WorldMap 区别；ActionLock 的业务授权条件不完整；Mover 回答未覆盖 Mesh 用途与 GASP 装配。对应参考已经提供这些边界，单次回答仍未完整采用。保留为后续实际任务复测点，不为了满分强制每次复述全部参考。

结构验证已通过：6 个技能包、0 错误、6 份独立临时复制验证通过；README 与 LGF 八份 Markdown 的 29 个本地链接均可解析。LGF 包含 1 个入口、7 份主题参考、8 个触发用例和6个行为用例。两处模块索引/来源补正不改变行为题面或期望，加载组已记录其读取时序。报告仅统一换行及行尾空白，不修改冻结文字。

真实 LGF 仓库只读，结束时工作树仍干净，8 个关键文件指纹与取材记录一致。本轮没有编译插件、运行 Commandlet、打开/修改资产、运行 PIE 或多人联机，也没有安装技能、提交或推送仓库。

### 最终技能输入指纹

以下 SHA-256 对应交付文件；加载组原答案的资料修订时序见其工具记录。这是可追溯清单，不声称每个文件均由两组加载。

| 文件 | SHA-256 |
|---|---|
| `skills/skillforge-lgf/evals/behavior-cases.json` | `10003d556e01877e5011e0323d0e3982daaf4d0c5ec4f63387e5dda2a8adfcfc` |
| `skills/skillforge-lgf/evals/trigger-cases.json` | `917efe109fe29139911b1f23bdaab10def9a3508bf58eb9264842ecf00f2657e` |
| `skills/skillforge-lgf/references/avatar-and-assets.md` | `4e421d2889fd714c0cc5e4528a3986a610b9808b2c7b60209c45b8176dd0396d` |
| `skills/skillforge-lgf/references/integration.md` | `a5906a8c8d4f7f96782dff97d0771596db723e2b08cf6e9a436a6727e18bc47b` |
| `skills/skillforge-lgf/references/network-and-state.md` | `7cba8827a8c0ca28334aff12097e3b5e9da00b909997e6f3a648337a7b2238c9` |
| `skills/skillforge-lgf/references/project-map.md` | `370c5f12a0de9706c8c0b1f9adbe09c7c285dec2fc41366a3c157a7749bcfd70` |
| `skills/skillforge-lgf/references/sources.md` | `f837f204a8ace23d796b11248dce4dd25dd1724239380c82d502aa4e609886af` |
| `skills/skillforge-lgf/references/ui-platform.md` | `e9c84bfcce3280a44f10ddeac86323e3ec1ed2b2e771aa3164a8eb2f3203a8cc` |
| `skills/skillforge-lgf/references/validation-and-evolution.md` | `e5be729fa3ff67818ca97bb69e598fe29d075d5cd8f2f25c693f2cb49d29b386` |
| `skills/skillforge-lgf/SKILL.md` | `ea387a396ad3d71e7e8a76940b564180354aeeddeeb6bbe661da2c63648b94d8` |
