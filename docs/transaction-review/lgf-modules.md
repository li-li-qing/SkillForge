# v5 LGF Modules 清点修复

仅修改 transaction_review_v5/Skills/skills/skillforge-lgf 的脚本、测试与migration-evidence.md。没有发布包、安装或改旧库。

证据：descriptor_modules 原先用列表推导过滤，Modules:[null]、[{Name:7}]被静默跳过；空字符串与重复字符串被当合法模块列出。新增CLI测试覆盖project/plugin两种描述符，各9个反例；修改前18子场景失败，修改后18测试方法全部通过。

实现：Modules必须数组；每条必须对象；Name必须非空、非纯空白字符串；完全同名重复拒绝并指出首条。错误带完整文件、$.Modules[index]或$.Modules[index].Name；CLI返回2，无Traceback，无部分成功stdout。缺Modules/空数组合法，名称及顺序原样保留，未读取字段不变。

兼容边界：这只是清点器名字合同，不是完整UE描述符解析器。Epic插件文档要求Name与Type并定义唯一模块名；本轮没有扩展Type/平台条件/大小写别名等校验，也未将这些资料当作当前引擎源码验证。现有合法输入结果形状不变；过去静默接受的坏条目现在显式失败。大小写变体未自动归一化，保持有限范围。

来源（2026-11-07读取，页面显示5.8）：
- https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Projects/FModuleDescriptor/Read

验证：PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s skills/skillforge-lgf/tests -v：18 tests OK。
PYTHONDONTWRITEBYTECODE=1 python scripts/validate_skills.py skills/skillforge-lgf --self-contained：0 errors，1 standalone通过。
真实UE/UHT/UBT/Editor均未运行。工作副本无Git元数据，git diff尝试不适用；改用文件清单哈希记录。

最终文件SHA256：
- scripts/inspect_workspace.py: 2864d217e7e05b12b0724f5d2b0df3a2ae16883c49f9b4b10e6f490dd62fd775
- tests/test_inspect_workspace.py: 9ad411796f35c09ee0ce07f179b12ebe25a941461f2efa929e5b866f6cb9c04a
- references/migration-evidence.md: 3a7cc9876f1365124ab306fca94a46062f87921524e9dfbfb6cd7f480a2647b8

## 第二层复核补充（2026-11-07）

父线程lgf_runtime_audit/probe.py及results.json已全文阅读。三类实际缺陷：同后缀目录污染源码计数并使source_inspectable=true；JSON重复键覆盖Plugins/Enabled；深JSON直接泄出RecursionError。先新增反例，21测试旧实现结果为7失败+3错误；修复及来源边界回归后24测试全绿，1技能及1 standalone校验0错误。原父探针重跑见v5-runtime-probe-after.json：目录不再计为源码，duplicate/deep均CLI 2无Traceback。

修复仅LGF脚本/测试/migration-evidence.md：Build.cs/.h/.cpp均is_file过滤；object_pairs_hook拒绝任意对象内重复键（文件和重复键名入诊断，未宣称JSON完整路径）；仅在读取/解析阶段转换RecursionError/MemoryError及既有读取/解码异常，不catch BaseException。KeyboardInterrupt传播测试通过。没有新增大小/深度固定阈值；read_text仍整文件读取，不宣称全面防资源耗尽。

合法对照：UTF-8 BOM、不同对象中的同名字段、真实Build.cs与.cpp、已存在缺Modules/空数组保持通过。外部文件符号链接fixture实际运行通过、未skip：保留lgf.file，新增resolved_file和descriptor_outside_project；missing时null。Source仍按发现位置查找，不扩大搜索。实际路径字段只是现场说明，不提供并发替换/TOCTOU保护。

engine.status/verified旧接口保留；limitations明确仅验证提供Build.version字段，不证明完整安装、项目EngineAssociation绑定、可运行或当前Editor。仅Build.version fixture通过该有限语义测试。source_inspectable也明确仅候选源码存在，不证明能构建。

没有运行真实UE，不发布包，不修改其他技能。本节哈希替代上节旧阶段哈希：
- scripts/inspect_workspace.py: 884aa6b49826ccdebd728031555159f8539a92e361bc2ae3b954906fdb44fa5a
- tests/test_inspect_workspace.py: e2710a77833e0929f3df953ec42dc456d90d6e89054835b74a81850fc128eef6
- references/migration-evidence.md: fa09be48415f8b7a49ea3c76c56055c6cf73c0f0e233914fe6599a99dbe506b0

## 最终JSON输出边界补充（2026-11-07）

父复验发现约994层EngineAssociation数组解析可成功、输出缩进编码却RecursionError。本轮核对FProjectDescriptor官方API：EngineAssociation为FString。兼容已有缺失/null/空字符串和自定义GUID，不把空值猜为默认引擎；非字符串用文件+$.EngineAssociation拒绝。官方链接：https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/Projects/FProjectDescriptor （读取页面显示5.8，未运行引擎读取器）。

最终json.dumps单独进入受控边界，ValueError/RecursionError/MemoryError返回2；完整编码后才print，编码失败stdout为空。VersionName、Changelist、CompatibleChangelist、BranchName四个透传字段用独立CLI进程搜索980–1000层，实际找到解码成功而编码失败的边界，修复后全部exit2无Traceback/无正文。这验证输出兜底，不将这些元数据宣称为UE类型已验证。

ensure_ascii改为True，中文/Unicode呈现为转义但json.loads后的值不变；孤立surrogate也可安全round-trip。未对任意Unicode做有损替换。输出流OSError/ValueError受控报告可能不完整，不保证已写字节原子撤回；KeyboardInterrupt仍传播，不catch BaseException。未新增大小/深度上限，仍不声称全面防资源耗尽。

先RED：28测试旧实现10失败+3错误，包含五类非法EngineAssociation、四个真实透传编码边界、surrogate和三种编码异常。修复后补900层EngineAssociation真实CLI及输出流OSError，最终29 tests OK；1技能/1 standalone零错误。没有真实UE/UHT/UBT/MCP测试，没有发布包。父独立probe已读取，未覆盖它的results文件，由父线程继续独立复验。

最终三文件SHA256（替代上节阶段哈希）：
- scripts/inspect_workspace.py: 02056e3f3b777d4647f48e946aafb882907b280d9add3959dbf29aaa04ea63d8
- tests/test_inspect_workspace.py: cd03d525538860e776c463b9b6efcf9d93835b9e98e6ca783e66ac35c1761221
- references/migration-evidence.md: f5a378e09d44c680810672a9b6059ea92872d027f048413a0beef35d15c135c3


后续集成复验：/dev/full输出故障在CPython shutdown flush后得到exit120。未更改stdout全局资源；文档和脚本帮助明确输出I/O只保证非零失败，不保证进程码2，输入/编码受控错误仍为2。新增真实Linux回归后30测试通过。此前文件哈希属于该阶段快照，最新哈希以transaction-review/change-manifest.json为准。
