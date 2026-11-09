# UE / Blueprint / LGF 定向审查报告

审查日期：2026-11-07。基线为 ida_delivery_work/Skills；实施仅在 overnight_review_20261107/Skills 副本。旧库未写入，未推送、安装、部署或运行未知外部脚本。

## 范围与证据强度

三份SKILL入口、全部54份references及六份eval JSON纳入文件清单、结构读取、章节索引和定向主题搜索；蓝图全部参考、C++生命周期/复制/构建/MCP、LGF清点器/测试/来源/接入/验证等重点全文阅读。大型Graph/Quest/Dialogue/Mass资料采用章节及相关段落抽查，**没有逐行审计每份大型参考的全部技术断言**。全量文件哈希和行数见file-manifest.json；不能把结构扫描等同全面语义通过。

基线行为规格为C++121、Blueprint9、LGF78；触发规格6/7/10。它们是评测规格，并非本次真实agent执行结果。新增3行为规格、2负触发规格；本次没有独立agent with/without-skill基准，故不声明行为评分提升。

## 已证实问题与处理

| ID / 优先级 | 基线位置与证据 | 建议与副本结果 |
|---|---|---|
| UE-01 / P1 | ue-cpp/references/replication-review.md:7-11、container-transactions-and-subobjects.md:23-46讲注册/清理；三技能全文搜索无RegisterReplicationFragments。Epic Object Replication明确Iris对非Actor/ActorComponent UObject的额外注册要求。 | 新增版本化Iris合同与容器入口、LGF独立提示；CPP-122覆盖registered list与fragment注册区别。没有UE环境，网络未测。 |
| UE-02 / P1 | ue-blueprint/references/unreal-mcp-editor-workflow.md:5-12仅连接/工具发现，未分proxy session与Editor reachability；C++并发句为笼统依次发起。官方Epic固定技能明确缓存catalog/status不足以证明可达，并允许受支持独立请求重叠；5.8网页仍为串行措辞。 | 蓝图新增只读恢复探针、同包/依赖协调和版本条件化并发；C++同步。保留用户PIE、动态能力发现与独立工作继续。BP-09覆盖。 |
| UE-03 / P1 | 现有MCP资料集中Editor，缺cook/shipping服务生命周期。Epic5.8文档说明Runtime服务模块可显式启动。 | 补实际StartServer、注册工具、配置/监听证据门，避免“模块存在=公网服务”与“Cook必移除”两种结论。BP-09覆盖。 |
| UE-04 / P2 | C++与Blueprint描述含UFUNCTION/蓝图等术语，未显式覆盖仅Shipping EXE分析；触发规格无此负例。 | 两入口新增无源码二进制任务边界，各补no_trigger；仅背景解释不获得源码/资产写权限。 |
| UE-05 / P2 | StateTree/Mass/GAS大型参考有版本性断言，但缺就地官方链接或主要锚定旧社区提交。 | 各加已读取Epic来源、读取日期与5.8页面范围；LGF对应三参考自包含版本入口。未重写架构或把当前页当5.7兼容证据。 |
| LGF-01 / P1 | scripts/inspect_workspace.py:97起：Plugins=null/字符串返回{}，无效条目被跳过，缺Enabled默认false，重复同名最后覆盖。内存探针与4新增负例实际复现。 | 严格验证容器/条目/Name/Enabled；重复声明报conflict，Enabled缺失保留null。所有条目验证，不只白名单；结果仍为声明而非运行启用。 |
| LGF-02 / P2 | 同脚本find_lgf_plugin仅搜索Project/Plugins，输出status=missing未携带范围。即使传engine-root也只查Mover，不会查engine LGF。 | 状态改not_found_in_project；新增project_plugins_only及runtime_enabled_verified=false和limitations。未扩展全盘扫描。LGF-76覆盖说明合同。 |

LGF输出兼容影响：消费者若硬编码status='missing'或要求relevant_plugins所有值为bool，需适配新状态/null；found布尔仍保留，但明确只表示搜索范围内发现。不存在运行启用判定。本轮未引入任何自动安装行为。

## 外部技能具体文件调研

1. quodsoler/unreal-engine-skills，固定f3742d7b688690810df369802b90430324e380b9，2026-09-28提交，未归档，MIT（下载LICENSE核对）。读取networking SKILL及replication-patterns、blueprint-node-patterns具体文件。可取点：subobject移除与远端destroy/tear-off不同、异步节点工厂/Activate与完成释放时机明确。拒绝整套搬用：networking正文/Pattern5没有Iris UObject RegisterReplicationFragments；其“全部示例编译5.8”属上游声明，本次未验证。它是有用参考候选，不能仅由README自证全面正确。
2. anthropics/skills，固定2c5958ecac7cee2b583967a2c4981d0f4a75c579，2026-11-06提交，未归档；仓库API license=null，因此单独核对skill-creator/LICENSE.txt为Apache2.0。读取agents/grader.md及aggregate_benchmark.py相关实现，后者按run收集grading并统计with/without配置，前者要求对输出与声明分别找证据。可吸收的是评测证据方法；没有运行脚本，没有用结构通过代替行为通过。
3. Epic官方unreal-engine-skills-for-claude-code-plugin，固定0e27bde2b55c5d3f6948532f4296aaa3654d8f4b，提交2026-10-23，仓库pushed_at 2026-10-27，未归档，MIT；正文与operations.md已下载核对。用于恢复/并发资料差异分析；其中全量保存或停止PIE建议未照抄，保留用户既有协作习惯。

具体文件下载清单、SHA256与上游树在external/。未把外部源码复制到SkillForge，只用独立表述补充已核实合同。

## 来源

- Epic Object Replication：https://dev.epicgames.com/documentation/en-us/unreal-engine/replicating-uobjects-in-unreal-engine
- Epic MCP 5.8：https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-mcp-in-unreal-editor?application_version=5.8
- Epic Plugins：https://dev.epicgames.com/documentation/en-us/unreal-engine/plugins-in-unreal-engine （engine/project两搜索域，支持LGF范围结论）
- StateTree：https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-state-tree-in-unreal-engine
- Utility API：https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/StateTreeModule/FStateTreeConsiderationBase
- Mass：https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-mass-entity-in-unreal-engine
- 5.8 release notes：https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes
- GAS：https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/GameplayAbilities/FPredictionKey

部分带application_version的官方URL首次抓取失败；改用成功读取且标题显示5.8的页面，未把URL参数本身当版本验证。

## 验证

- 原LGF12项测试通过。首次在全只读沙箱因无可写临时目录产生19个errors，属于夹具环境问题；在授权独立临时目录能力下重跑全绿。
- 新增4项测试后，旧实现16测试中出现11个失败子场景（范围状态、格式、重复、缺Enabled），实现修正后16测试全部通过。详见verification-1.txt。
- 三技能validate_skills及--self-contained均0 errors，3个独立副本通过。详见verification-2.txt。
- 没有发现可用UE工程/Build.version；没有运行UHT/UBT、Editor/MCP、资产编译保存、PIE、Iris网络、Cook/Shipping或真实性能检查。
- 外部脚本仅阅读未执行。新增文本行为规格未实际驱动agent，反向审查可继续运行。

## 审批记录与剩余限制

批量副本文档写入第一次被auto-review拒绝，理由是初始只读委派与后续助手授权不足。该拒绝动作未执行。按要求读取user_message_read取得用户2026-11-07 22:11原始消息，明确允许继续检查其他Skills并加入合适内容；基于新证据重试一次后获准。当前无待审批动作。旧库未修改，根索引未修改。大篇参考的全面语义审计和真实UE验收仍未完成，不能宣称整个UE技能域已无缺口。
