# UE 专项与逆向知识库来源调研

核实日期：2026-11-07。范围：只读访问 GitHub 文件/目录、仓库元数据及 Epic 文档。没有运行第三方脚本，没有运行 IDA、UE 或目标二进制，没有验证游戏内偏移。本文可作为整合素材，不代表已修改 SkillForge。所有结论由本报告独立表述，不复制上游技能正文。

## 1. 上游项目审阅结果

仓库活动时间仅为 GitHub `pushed_at` 的观测值，不是代码安全、可用性或持续维护承诺。以下根 LICENSE 均已读取；嵌套依赖仍需单独审查。

| 项目 | 核实内容和版本锚点 | 值得借鉴与适配 | 不直接采用 | License / 活动 |
|---|---|---|---|---|
| [zahidaz/awake](https://github.com/zahidaz/awake) | 目录树、`docs/reversing/frameworks/unreal-engine.md`，文件 blob `309d1c8cc27a61d24117040fb1f504257a859ebb`；树 `d500ada895a9cda4caa4516b94d1e5931ad7c65d` | Android 文件识别；原生二进制与资源/Blueprint 两条分析路径；工具线索索引 | 该仓库实际是 Android Wiki，不是 UE 官方逆向框架。全文的布局/大小/反射完整性断言不能推广；ProcessEvent 不是所有原生调用的总入口；包含占位虚表偏移的片段不是可运行示例。排除反作弊、加密密钥提取、绕过和任意注入流程 | MIT；2026-05-21；未归档 |
| [morluto/awesome-reverse-engineering](https://github.com/morluto/awesome-reverse-engineering) | 目录树、`examples/resource-intake/README.md`、`docs/priority-candidates.md`；树 `36167d66fe97f6d27c4c69c4fde0e6c206000f44` | 最值得采用的是工具准入记录：固定版本和哈希、独立预期结果、实际执行与文档核查分开、平台不适用明确 SKIP、后续复审日期 | 不把索引收录或 README 自述当作已通过本地测试；不批量装入所有工具；该项目的复现结论仅覆盖其具体 fixture | CC0-1.0；2026-10-30；未归档 |
| [rehan-remade/universal-modder](https://github.com/rehan-remade/universal-modder) | 目录树；`.agents/skills/reverse-engineering/SKILL.md`、`game-recon/SKILL.md`、`mod-any-game/references/engines/unreal.md`；树 `3c4ac6c38e411b8c543bce217eae197039516bfc` | 根据引擎/运行时路由；先侦察再定位函数；静态证据驱动动态验证；任务日志与资源格式往返测试 | Mod 制作、资产生成、云服务上传、注入与重打包不是只读逆向的默认步骤；不能将“先 dump 反射”视为所有目标必然可用；不要自动重命名/修改 IDB；反编译结果不是源代码规范 | MIT；2026-11-07（元数据返回）；未归档 |
| [angusdevgo/Seep-Reverse-Lab](https://github.com/angusdevgo/Seep-Reverse-Lab) | 目录树；`Tool/mcp/Tool/safe/ida-pro-mcp/skills/idapython/SKILL.md`，blob `10a0e2db2e7eada1fba393d143b4fece49d2261c`；配套模块 md/rst 索引；树 `e9b6c9e9643f21db082fa4ca918fac82490dc11e` | 小型 SKILL 负责模块路由，详细 API 独立参考；分模块查阅；ctree、类型与 xrefs 分开组织 | 这里是嵌套 vendored 社区 MCP 技能，不是新的官方 API 规范。`@idasync`、`int_convert` 属特定项目设施；不能视为 IDAPython 通用 API。主线程调度不等于长操作不会阻塞 UI。类型大小单位、版本移除项需重新核实。不要直接整体拷贝或采纳软件许可绕过等无关案例 | 根 GPL-3.0；2026-11-04；未归档；嵌套文件许可另查 |
| [gmh5225/awesome-game-security](https://github.com/gmh5225/awesome-game-security) | README blob `fdeb62fe3b58b9890b48705e65fca740a58ef643`、根目录、`wiki/AGENTS.md`、LICENSE；完整递归树过大未取得 | 将原始来源、概念页、实体页、索引、变更日志分离；页面记录来源/日期/置信度；小批增量更新和断链检查 | 大型工具集合不是专业能力证明；不默认吸收作弊、DMA、内核绕过等目录；不能将编译的 Wiki 当官方原始来源。两个猜测技能路径返回 404，未据此宣称读取这些 SKILL | MIT；2026-11-07（元数据返回）；未归档 |

直接阅读入口：

- https://github.com/zahidaz/awake/blob/main/docs/reversing/frameworks/unreal-engine.md
- https://github.com/morluto/awesome-reverse-engineering/blob/main/examples/resource-intake/README.md
- https://github.com/morluto/awesome-reverse-engineering/blob/main/docs/priority-candidates.md
- https://github.com/rehan-remade/universal-modder/blob/main/.agents/skills/reverse-engineering/SKILL.md
- https://github.com/rehan-remade/universal-modder/blob/main/.agents/skills/game-recon/SKILL.md
- https://github.com/rehan-remade/universal-modder/blob/main/.agents/skills/mod-any-game/references/engines/unreal.md
- https://github.com/angusdevgo/Seep-Reverse-Lab/blob/main/Tool/mcp/Tool/safe/ida-pro-mcp/skills/idapython/SKILL.md
- https://github.com/gmh5225/awesome-game-security/blob/main/wiki/AGENTS.md

## 2. Epic 官方参考台账

以下均为官方来源，最后核实 2026-11-07。网页最新版在本次检索被标示为 UE 5.8；不要把未固定版本的网页直接套到 UE4 或旧 UE5 二进制。公开 API 页能确认符号和语义，但不能证明目标程序的字段偏移。需要使用用户有权访问的匹配源码、构建配置和符号文件进一步确认。

| 名称/URL | 核实层级、用途与版本限制 |
|---|---|
| [Unreal Header Tool](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-header-tool-for-unreal-engine) | 已打开正文。UHT 解析相关头文件并生成 UObject 支持代码，之后交给 C++ 编译器。当前文档还包含 C# UHT 说明，不可直接套旧版 UHT 工具实现。可信程度：高，限文档语义 |
| [UFunction 5.5](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/UObject/UFunction?application_version=5.5) | 搜索结果核实 `FunctionFlags`、`FirstPropertyToInit`、`RPCId` 与 `UObject/Class.h`；不能把 RPCId 当所有 RPC 的通用唯一识别器。可信程度：官方摘要，细节需打开并核对匹配源码 |
| [FProperty 5.5](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/UObject/FProperty?application_version=5.5) | 搜索结果核实 `UObject/UnrealType.h` 与链表字段；不提供目标布局保证。可信程度：官方摘要 |
| [UProperty 当前页](https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/CoreUObject/UProperty) | 官方摘要仍包含 UProperty/关联 FField 的兼容性类型，不能说“新版完全没有 UProperty”。`UPROPERTY` 宏和旧 UProperty C++ 类型不可混淆 |
| [UProperties](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-uproperties) | 官方摘要核实宏和属性 specifier 的声明用途；这些不等于 Shipping 保留全部编辑器 metadata |
| [RPC 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-procedure-calls-in-unreal-engine) | 官方摘要说明复制设置、所有权和调用条件。执行表应以目标版本全文为准；新版可能新增 RPC 类型，不能倒推旧版 |
| [RPC 4.27](https://dev.epicgames.com/documentation/en-us/unreal-engine/rpcs?application_version=4.27) | 官方旧版摘要供版本对比；不能将其 `_Validate` 历史规则强制推广到全部 UE5 |
| [Replicate Actor Properties](https://dev.epicgames.com/documentation/en-us/unreal-engine/replicate-actor-properties-in-unreal-engine) | 官方摘要核实 lifetime 注册与条件复制；文档示例也可能保留旧构造写法，不能复制后声称新版编译测试成功 |
| [Replicating Actor Components](https://dev.epicgames.com/documentation/en-us/unreal-engine/replicating-actor-components-in-unreal-engine) | 官方摘要确认组件可以有属性复制和 RPC，具体要求仍需匹配版本 |

未可靠核实：UE4.25 迁移公告原文；精确 FField 历史布局；各版本 Blueprint 字节码指令表；各版本 IoStore 默认配置。因此本文不提供其硬编码偏移、opcode、阈值或未经核实的迁移断言。FField 页面本次直接打开失败，不能记作已阅读官方正文。

## 3. 建议整合的版本安全 UE 工作流

### 3.1 环境与输入记录

1. 保存原文件 SHA-256、大小、平台、架构、端序、位宽、文件格式、加载基址和地址换算规则。区分文件偏移、RVA、IDA EA 与运行时 VA。
2. 记录推定引擎主/次版本、补丁/定制分支、构建配置、编译器/ABI、优化/LTO、PDB 或 ELF debug/build-id 匹配状态、源码可用性。未知就是未知，不能从一个文件名断言版本。
3. Android 的 libUE4.so/libUnreal.so、版本字符串、包目录和注册代码仅是线索。多个独立线索一致才提高版本置信度。
4. Development/Shipping、符号剥离和反射信息保留是不同维度。没有 PDB 不等于没有反射；有类名也不等于所有 C++ 类型/成员可恢复。
5. 静态分析先于执行。只有授权的隔离环境才启动/附加进程。不得默认解密资产、绕过 DRM、反作弊或上传二进制。

### 3.2 类、成员和函数定位

- 从已证实的字符串/导出/符号/注册函数定位候选 UClass、UStruct、UFunction，再追踪注册、引用和调用。函数名、字符串与调用者只有单一证据时保留“候选”。
- 将 UObject 对象谱系与 FField/FProperty 描述体系分开研究，匹配实际版本。不要把每个属性描述对象都当作 UObject，也不要将 `UPROPERTY` 宏当作旧 UProperty 类仍用于所有字段的证据。
- UHT 生成代码、`.gen.cpp` 符号、注册表、native thunk 都是定位线索，优化/合并/裁剪会改变其形态。没有生成符号不能直接否定反射。
- 类型恢复收集构造/析构、vptr 写入、RTTI（若有）、this 调整、读写宽度、继承与对齐证据。多个继承子对象可以有多个 vptr；优化可能消除构造函数实体。
- 偏移必须注明相对哪个对象/子对象、十六进制字节偏移、大小、bitfield mask、平台/构建和指令地址。反编译器显示的数组下标不是自动成立的成员偏移。
- 模块归属使用匹配 PDB/链接信息、注册包路径和调用关系交叉验证；单体链接中“属于一个模块”不代表独立 DLL/段。

### 3.3 RPC、复制、Blueprint 与序列化

- RPC：组合 UFunction flags、注册/生成 thunk、实现函数、调用空间与授权测试中的执行路径。仅看到 `Server`、`Client`、`_Implementation` 名称不能判定 RPC。flags 的具体位值必须查目标版本。
- 属性复制：记录属性 flags、lifetime 注册/条件、对象复制设置和相关运行时代码。区分“声明具备复制资格”和“本次实际复制”。需要进一步辨别目标采用的 legacy/Iris 路径，不能只凭一个宏或 OnRep 名称下结论。
- Blueprint：检查 UFunction/script 相关数据、native thunk 和匹配资产的证据，区分原生实现、Blueprint 实现以及互相调用。不要假设所有调用经过 ProcessEvent，也不要把 ProcessEvent 的一个 xref 当完整业务调用链。
- 序列化：区分内存对象布局、反射属性描述、磁盘包/资源布局和网络数据格式；同一字段在各层并非固定偏移映射。PAK/IoStore 是待核实打包选项，不是简单 UE4/UE5 二分。
- UWorld、ULevel、Actor、ActorComponent 只按版本匹配类型和已验证引用解释。通用扫描特征可以产生候选，不可替代结构约束、边界检查和真实地址证据。

### 3.4 最小证据记录

每条结论记录：目标哈希、平台/架构、引擎版本依据、IDA 版本、分析时间、函数名/EA/RVA、相关 xrefs、类型/成员、汇编/伪代码摘录出处、源文档版本、推理链、置信度、未解决问题。运行时证据额外记录进程/模块基址、断点地址、输入、线程、观测值、复现步骤。

四级状态：已验证（直接证据但明确验证范围）、高可信（独立证据一致）、推测（待验证）、未知。不能以“官方文档有此字段”取代“该目标字段偏移已验证”。

## 4. 整合与验收建议

采用一个 IDA 入口路由到 UE 参考文档和共享脚本，不为每个 UObject 类型再造一个技能。来源台账与现有知识索引整合，保持现有路由。优先独立实现例子，避免复制 GPL 工作台或第三方未核实偏移。

建议授权本地 fixture：一个可自行构建的 UE 项目，含一个 Actor、一个组件、一个原生普通函数、一个 Blueprint 可覆盖事件、一项条件复制属性和一个 RPC；保留准确源码/生成代码/PDB及构建参数。分别在适用 Development/Shipping 配置对照，记录哪些证据仍存在。按地址与实际行为评估类归属、成员偏移、RPC、复制、原生/Blueprint 五项判断，而非只看文档是否写齐。

本次状态：来源与文档检查完成；没有 UE fixture、IDA 实机执行或动态验证。不得将上述验收建议记为测试通过。
