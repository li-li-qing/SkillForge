# v5 候选：事务边界与返回状态复审

基线为已发布v4（SHA-256 cebc606cce5690336f834aa373976e82f22de9a4e95f80476f974bdbd5c2f881）。本轮只修改独立副本；已冻结为独立v5完整交付快照；ZIP与Library回执另行记录，不循环写入本包。v4及用户安装不变。核实日期2026-11-07。

## 确认并修复

1. 经验库提交/撤回成功后清理锁失败：单独返回lock_cleanup_failed、事务/目标/日志状态及当前哈希，不把已提交当未执行；保留主要业务异常和清理错误。无效UTF-8锁令牌不再掩盖原错误，不删除替换或未知令牌。恢复提示区分prepared、rollback_prepared与committed、rolled_back。
2. 经验库跨工具门禁：promote/rollback持锁后检查同根更新器未完成计划的关联目标与退休目录；已知无关文件允许提交，损坏或未知范围明确拒绝。propose只保存候选，recover只协调自身日志，不被新增门禁误拦。独立技能无跨包import。
3. 更新器成功保存applied后清锁失败：保持applied日志，返回cleanup_required和已应用证据，不降级partial，不建议重复执行或recover。主要失败同时清理失败仍保留两份错误。
4. LGF Modules非法条目、空名、重复名不再静默过滤，错误含文件及精确JSON路径；缺Modules和空数组仍合法。不是完整UE描述符验证器。
5. IDA字符串分页统一解析进制偏移；导出默认仍返回路径，显式return_status=True返回published与cleanup_error，不再因warnings=error把已发布结果变为异常。batch将导出状态与分析ok分开，终端输出失败另记诊断。

## 证据与回归

[更新器复核](updater-review.md)、[经验库复核](experience-review.md)、[LGF复核](lgf-modules.md)、[IDA复核](ida-boundaries.md)。实际跨组件测试使用真实两个模块及临时文件：更新器目标已写后注入最终日志失败；同目标经验晋升被阻止，原目标保持after；无关技能仍能提交。

最终全库单元测试：根库105、索引40、Addon50、LGF30、经验库36、IDA66，合计327个测试方法，所有套件exit0，8条skip记录、无失败/错误。skip包含Windows junction子用例，不能简单把testsRun减skip条数当作精确“通过方法数”；旧v4的269通过是该算术口径，不代表额外失败。跳过原因均在[本轮日志](../../evals/runs/2026-11-07/transaction-review/)中。14技能和14独立副本校验0错误。Python语法检查通过。

独立复核追加发现并修复无效锁编码问题；最终整包结构检查还修正一处glob路径表达触发的可移植性检查。核心路由与习惯不改。

## 补充实际行为证据

保存了父线程提供的[隔离文件修复探针](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/REPORT.md)与原始答案、项目、测试、哈希。重复技能输入副本仅保留逐文件哈希；随后收到的已完成round2另行记录，不与旧新对照合并计分。v3/v4新上下文同题均实际修复Python报告代码，独立复验每版12项通过，且分别重跑9/8项unittest；没有因为未决Qt转Web选型停掉已授权修复。两版都成功，仅支持未见退化，不证明新版更优。其余7场景not_run。原报告日期2026-11-08按来源保留；本候选的执行时钟记录仍为2026-11-07，不把来源日期混同本轮时间。

缺少Qt后端，未进行Qt/MFC/UE/IDA/游戏实机验证。该探针是Python实际执行，不是Qt实测；执行者trace也不是完整宿主审计。

## 保持的限制

保留既有事务协议及旧全局pending规则；新跨工具门禁按目标范围判断，没有重构恢复架构。锁清理需核实所有权后显式处理，绝不自动偷锁。文件系统断电、非协作进程竞争、真实Windows和IDA兼容性未验证。未安装、推送、启动服务或发布新包。


## 第二轮行为证据与阅读预算

[第二轮报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round2/REPORT.md)记录三项v4新上下文任务：真实本地过期基线合并保留他人改动、自编带符号ELF只读静态检查、合成UE版本和MCP合同冲突判断，均在各题范围通过。没有v3对照，没有真实多人竞态、CE/IDA或UE Editor实测。原样保留fixture二进制仅用于证据；本轮集成人未执行它。

多参考一次性读取截断来自评测调度，不证明技能入口缺失或已完整读取。仅在经验维护的可选评测参考页补充精确路径、按任务章节分段、记录截断并补读的操作提示；不改总入口或动态路由，也不强制全库阅读。


## 第三层清点与校验复核

LGF补充排除同后缀目录、拒绝嵌套JSON重复键、将解析RecursionError/MemoryError转为带文件的受控错误；不引入固定资源预算，也不称全面防耗尽。合法BOM、独立对象同名字段与正常文件保留。外部描述符显示resolved_file及descriptor_outside_project；engine.verified仅确认版本描述字段，source_inspectable仅确认发现候选源码文件，不代表安装、绑定、编译或运行成功。

[校验器复核](validator-report.md)用隔离夹具复现目录symlink隐藏坏链接及FIFO读取阻塞。现在拒绝包内目录链接/reparse point与特殊文件；包内相对常规文件链接仍允许。正式技能目录实扫没有非普通文件/目录项；没有声称正式包存在坏链接或ZIP携带FIFO。未提供抵御并发恶意替换文件的安全沙箱保证。

新增受影响测试已重跑：根库105（2条skip）、LGF30全通过；其他套件代码未变，沿用本轮有效验证。14技能14独立副本再次0错误，当前动态索引保持一致。


## 第三轮行为记录

[第三轮原始报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round3/REPORT.md)保持冻结判定：Qt排序身份通过；Lua远程片段边界行为通过但实施缺输入；经验负证据通过；LGF/UI状态题为部分通过，未明确展示要求的探针正对照。不得称四题全过。该题未给框架身份，执行者使用通用debugging/UI，因此也不能称LGF专项通过。以上是冻结v4的新上下文回答行为，没有源码现场、实际GUI/Lua/LGF运行。

对缺项先保留partial，不直接改技能规则。另已设计本地Python owner/projection模拟夹具，在派发前冻结正对照与修复验收标准，专门区分无日志与未调用；结果单独记录，不回填原题为通过。


校验器并发注入复验确认TOCTOU仍存在：预检后动态替换为FIFO不属于稳定树保证。本轮明确可信固定输入前提（暂停相关写入或固定版本），不是安全沙箱；没有把局部POSIX fd方案外推为跨平台完整防护。


[明确观察链路夹具](../../evals/runs/2026-11-07/transaction-review/observable-fixture/REPORT.md)已完成：冻结v4的新上下文执行者实际展示正对照、定位订阅前事件丢失并做一行最小修复；独立代码/输出复验7组通过。该题直接关注空trace推断，不能与原题等价比较，不能归因技能收益；保留原partial，不机械添加技能规则。


LGF最终输出复验：EngineAssociation保留缺失/null/空字符串，非字符串受控拒绝；全部manifest先完成JSON编码才触碰stdout。其他透传字段的深层编码失败也受控，不仅检查EngineAssociation。ASCII转义保留JSON值，避免孤立surrogate的终端编码异常；真实输出流故障仍可能产生部分字节，不能宣称stdout原子写入。30项LGF回归与13项独立CLI夹具全部通过，结果见lgf-independent-final.json。该独立夹具另外计数，不加入单元测试方法总数；早期快照的308不是当前总数，当前以文首六套件汇总为准。


## 第四轮独立诊断链

父线程提供的[第四轮报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round4/REPORT.md)与冻结原答复、配置、6次执行输出及6次独立复验记录已原样保存。执行者通过error输入确认task.error与tasks.error主题不匹配，仅在隔离work配置修复，并用idle/success作对照；没有修改原fixture。此为冻结v4上的同步Python合成链行为，非LGF/UE/Qt实机，无旧新版本比较；原第三轮partial不变，全库行为不宣称完全通过。原始执行命令保留当时路径，移到其他电脑复验时须显式替换本地证据根目录；未改写原始证据哈希。


真实/dev/full复验得到进程exit120：main已报告JSON输出失败，CPython退出再次flush失败会改变最终码。本轮选择限定合同而非替换调用者stdout：受控输入/编码错误正常为2；输出I/O故障要求非零并视为失败，不能依赖精确2。新真实回归通过，未把已有输出失败称成功，LGF目前30测试。


## 官方长文抽样澄清

[Qt/Lua限定核验](platform-clarifications.md)：Qt当前6.12.0官方文档中的wait平台差异与未启动线程返回值已准确限定；Lua默认5.1.5的200活跃局部限制说明参数、self、兼容arg、for隐藏局部、块退出及其他编译限制。不外推定制运行时或其他Lua版本，未取得可信Lua解释器，未做真实编译。

[FastArray删除语义](fastarray-clarification.md)：按页面显示UE5.8，补删除前身份/缓存失效与删除应用后重建或增量修正，覆盖纯删除批次和临时索引寿命；目标版本支持时才用PostReplicatedReceive。不是声称消费项目有bug，也未做UE网络实测。新增三条行为规格均not_run。受影响根库/Addon测试及14技能独立检查已再次通过，未改动态入口。


## 后台事实边界窄澄清

[持久执行澄清](persistence-clarification.md)仅修改collaboration-policy中的后台承诺条件：无核实机制不得承诺，有真实机制、授权及成功回执时如实报告。独立语义复核确认其余A/B/C、待决和长期习惯不变；没有创建任何后台任务。总入口SKILL、routing-policy和user-workstyle三个受保护文件仍字节一致；不能把这项条件澄清表述成所有协作参考都未修改。新增正负案例not_run。


## 二进制与Addon文件安全复核

[二进制输入审查](binary-input-review.md)：通用probe与IDA哈希均拒绝稳定FIFO/设备，按普通文件初始大小读取并检查增长/缩小、末尾元数据；打开后复核实际描述符。合法普通文件及文件链接支持，不加任意大小上限。多块6MiB夹具用于验证分块，不冒充大型生产样本实测；不是原子快照，不保证对恶意恢复mtime或任意文件系统并发的防护。

[Addon文件安全](addon-file-safety.md)：独立校验器统一常规文本读取，特殊eval JSON不再进入阻塞读取；verify_report将raw输出完整写入/同步/关闭partial后无覆盖发布。失败时不留下半成品正式文件；partial保留用于调查，重试需先核查或选择新输出，不自动覆盖。发布后清理错误单列，stdout失败仍非零并尽力报告published_diagnostic_error，双诊断流失效也不重写文件。进程非零不能据此推断未发布；不支持硬链接的文件系统安全失败，未称Windows实测。

受影响整合套件最终为根库105、Addon50、IDA66；连同索引40、LGF30、经验库36共327方法，8条skip记录，全部无失败。14技能及14独立副本再次通过。新增持久机制正负题未执行，原真实行为partial不变。


持久规则的后续[独立场景证据](../../evals/runs/2026-11-07/transaction-review/persistence-scenarios/report.md)已纳入，冻结policy哈希与当前版本一致。两名真实隔离Agent在模拟能力/回执情景下均符合预期；这是行为场景验证，不是实际持久执行创建或九小时耐久测试，不改变原第三轮partial或批量not_run规格。


四脚本的[独立40项复验](../../evals/runs/2026-11-07/transaction-review/script-safety/reverification.md)已收录，四文件SHA256与当前候选逐一匹配。包含Linux特殊文件与定向替换、增长缩短、发布故障及发布后诊断状态；故障注入位置已从旧最终路径调整到新partial，未把未命中旧hook当通过。40项另计，不混入文首327个单元测试方法。保留非原子快照、受控输出目录、同目录硬链接、无目录fsync掉电保证及未真实Windows/IDA限制；失败partial需显式核查，不自动删除重试。


## 第五轮高风险边界

[第五轮原始报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round5/REPORT.md)与冻结回答、判定及审阅者objdump证据已收录。三题分别统计：无IDA时真实binutils静态分析自写ELF，人工伪代码与Hex-Rays输出、静态预测与运行结果明确分开；未认证远程MCP只做离线信任分析，不连接或上传；Qt合成片段做真实工具可用性检查和静态审查，识别parent阻止迁移及修正后的跨线程/UI寿命风险。

只有ELF题执行了替代静态分析。IDA/Hex-Rays、远程MCP认证/拦截、Qt构建运行均not_run；任务已禁网络，不把未连接全归因于技能。三题使用冻结v4，没有版本收益对照；无新确定缺陷，不据此修改技能。原第三轮partial仍不变。


## 深层网络、状态与所有权事实修正

[GAS方向与效果生命周期](replication-direction.md)修正客户端赋值replicated CurrentTarget的错误解释：标准属性复制不自动上传客户端赋值，先证真实RPC/TargetData/激活载荷路径，再谈顺序；同时保留LocalPredicted event-triggered activation-with-event-data可能联网的例外，不概括GameplayEvent永不联网。装备效果区分独立Duration/Infinite、聚合堆叠及Instant，active handle不自动证明逐装备独占，来源贡献建议不是引擎保证。

[StateTree失败合同](statetree-failure-clarification.md)区分All成功合取与参与任务失败路径，版本分别锚定教程5.6更新和当前5.8 API；退出清理及无可用transition行为须目标实现验证。并行新增GAS/StateTree案例已逐ID核对均存在且唯一，全部not_run。

[桌面与请求合同](desktop-request-clarifications.md)修正MFC虚拟列表“仅可见项”表述；无ID同路线R1/R2不能仅凭本地代次归因；取消共享询价限owner/lease且保留其他消费者。Qt区分已安装layout自动reparent与未安装layout；输入清理只对后端支持且可证明归属的会话操作，SendInput合同不外推未知大漠后端。没有认定游戏/UE/桌面项目实际存在这些bug，没有执行实机输入。受影响测试与14独立副本检查已通过。

## 最后一轮文档一致性补充

Addon评测README已同步63行为题、35触发题、AR-01～AR-63；新增数量/首尾ID一致性测试先复现旧文失败，再验证修订。GAS周期GE移除不等于回滚过去execution，依据同页Epic lifetime周期执行合同作限定；Qt同进程SDK关闭也遵守现有输入账本及未知状态边界。父线程对前轮GAS/StateTree与MFC/Qt的独立静态复核通过；这两处补充未做UE或Windows平台执行测试。

## 第六轮GAS新旧对照

已收录[冻结快照对照报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round6/REPORT.md)、原答复、trace、题面及来源哈希。两题×两快照四次推理符合题内标准，旧版也正确，未证明候选性能提升，亦不能撤销已确认的源文档错误。所有UE编译/PIE/联机运行not_run。执行快照按内容manifest标识，并非本次再补充文档后的当前树；重复技能内容未复制，原manifest保留，导入文件另有哈希清单。

## 发布前数字一致性复核

最终重新执行六套件后，以suite-results.json及final-*.log为当前计数依据；历史早期308仅属当时快照。327为testsRun之和，8为skip记录数（含子测试），不以相减推导精确通过方法数。独立夹具与行为评测另计。打包清单必须排除__pycache__目录及.pyc/.pyo测试生成物。

变更清单entries不包含清单自身；实际非缓存变更总数应为entries数量加1。完整行为与故障证据保留，原始/workspace和/tmp路径用于溯源；若未来公开，应另行脱敏，不改写本次原始证据。

## Linux真实多进程补充

已收录[多进程证据与版本哈希](../../evals/runs/2026-11-07/transaction-review/multiprocess/verification.json)。原始JSON未内嵌执行源码哈希，因此未推断原执行版本；本轮审阅夹具后在当前候选重跑两份脚本，均exit0，更新器与经验脚本执行前后哈希一致。真实spawn进程、受控事件交错和SIGTERM验证持锁互斥、旧候选stale、未完成日志门禁及显式recover，未见静默覆盖。夹具中的手动清锁只发生在临时目录、已确认所有写入进程结束之后，不是用户恢复指南；不得盲目清锁。结果限Linux x86_64本地文件系统，不推广Windows、网络盘、断电耐久或所有并发交错。这些另计，不增加327个单元测试方法。

## 第七轮ArcheRage隔离推理

收录[第七轮报告](../../evals/runs/2026-11-07/transaction-review/isolated-behavior/round7/REPORT.md)及原答复、trace、冻结标准和哈希。快照manifest所有列出文件与当前候选逐项匹配，详情见同目录import-verification.json。两题满足归因和多消费者取消的题内推理标准；RU游戏、Native及离线回放均not_run。没有新旧对照，不声称改进，不加入327单元测试方法。

## IDA权限行动计划探针

收录[权限探针结果](../../evals/runs/2026-11-07/transaction-review/ida-authority/results.json)、冻结题面/标准、答复与导入哈希。23个冻结文件完整，相关20个技能文件与当前候选一致。两道fresh-context合成题共10条评分通过，覆盖第三方schema伪授权、只读范围、错IDB/输入哈希及硬链接备份。仅检查拟采取行动，不是实际OS沙箱、MCP写入/上传拦截、备份恢复或IDA运行。答复由最终消息手工转录，缺完整内部读工具trace；不把此证据等同执行审计，也不加入327单元测试方法。
