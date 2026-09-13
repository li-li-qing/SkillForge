# 行为评测独立 Agent 审阅 — 2026-09-12

这是与原回答者分开的 Agent review，不是人工签署、用户验收或真实工程验证。本次只审阅 debugging 和 UE C++；Blueprint、UI 留待其报告齐备后的后续审阅。

## 方法与范围

- 评分输入为两份 `behavior-cases.json` 的完整 prompt/expectations，以及本目录各技能的 baseline/forward 报告中的冻结原始回答。运行记录仅用于分析背景与边界。遵循 `evals/README.md` 的文字方案评测口径，不运行题目、编译、编辑器或游戏，不联网，不修改原始记录或候选代码。
- 每项使用同一解释比较两臂：**pass** 表示方案对期望的全部实质部分有具体行动、条件或验证依据；**partial** 表示有实质覆盖但遗漏一个必要部分；**fail** 表示没有相关支持或与期望矛盾。题目要求的是方案，因此不会仅因未执行项目操作而扣分，也不会把将来执行的方案记为已经验证。
- 复合期望必须覆盖各部分；提到“目标”“UHT”或某个指针类型本身不构成通过。一个案例没有写明的内容，不借用另一个案例补足。
- 读取报告时可见作者自查，但以下判断不采用其分数或通过声明作为证据。本审阅并非盲审：任务简报提示了 CPP-01 评分一致性及 CPP-02 generated include 的可能差异；实际判定按两份原始回答分别核对。作者报告的冻结顺序与材料隔离没有通过独立执行轨迹审计。
- 本次没有读取或独立核验候选 core/reference 的技术来源。输出覆盖评分与候选资料正确性是不同结论；尤其不能把回答引用资料中的“已核验”转写为本审阅已核验。

## skillforge-debugging

输入：`skills/skillforge-debugging/evals/behavior-cases.json`、`debugging-baseline.md`、`debugging-forward.md`。下表中的 E1–E4 对应 JSON 每题 expectations 的原始顺序。

| 案例 / 期望 | Baseline | Forward | 原始回答证据及同口径判断 |
|---|---|---|---|
| DBG-01 E1：区分现象、旧笔记假设与已知证据，不认定延迟是修复 | pass | pass | Baseline 区分面板现象、订阅变更、间隔配置，明确“0.2 秒不等于已经观测到刷新回调每 0.2 秒执行”，把 1 秒延迟列为未经验证猜想。Forward 把这些事实限定为用户报告、待代码或运行核验，并同样区分调度配置与实际刷新，拒绝用旧笔记认定延迟有效。两者均建立证据边界。 |
| DBG-01 E2：优先检查订阅到刷新链的可观察断点，提出能区分假设的最小诊断 | pass | pass | Baseline 沿注册→事件→数据→请求刷新→实际刷新→控件记录实例、事件序号、版本和跳过原因；事件源有事件而当前实例没回调支持订阅问题，回调进入则转查下一边界。Forward 同样关联事件、实例代次、状态版本和刷新执行，明确只有旧代次收取或当前实例漏收如何支持假设、正确收取如何否定分支。通过依据是可区分的观测与后续动作，不是列出链路名词。 |
| DBG-01 E3：没有游戏执行条件时提供验证步骤并如实保留未验证状态 | pass | pass | Baseline 提供首次打开、重开、打开/关闭时数据变化的采样与游戏内回归，明确未读代码、未加日志、未运行检查，演示稳定性未验证。Forward 提供原失败和正常路径、重开/重建、漏收/重复消费/旧状态覆盖的回归，并明确未读项目、未加诊断、未编译或运行。两者均交付方案而非冒认修复。 |
| DBG-01 E4：不无依据重写架构，不把试过三个补丁当成固定停工阈值 | pass | pass | Baseline 明确三个补丁不足以证明架构问题，在暂停猜测性补丁的同时继续静态排查和诊断准备。Forward 明确三个补丁不构成重写依据，按首个异常边界推进，且“不因为累计失败次数而停止调查”。两者都没有因数字阈值停工。 |
| DBG-02 E1：不采信旧笔记，将可见性语义交给版本匹配的权威证据核验 | pass | pass | Baseline 拒绝两条旧说法，要求先核对准确 UE5 版本，再对照该版本 ESlateVisibility 定义或官方说明，并区分一般语义与项目事实。Forward 将资料中已核验的 UE 5.7.4 与未知项目版本明确分开，要求用项目实际版本的 SlateWrapperTypes.h 和对应文档复核。此项按“提出版本匹配的核验方案”评分；两者都没有现场版本证据，Forward 引用参考核验并不额外构成项目核验。 |
| DBG-02 E2：识别父级命中测试与子按钮输入的关系，避免把加长延迟当作根因修复 | pass | pass | 两者都说明祖先 HitTestInvisible 会阻止子树命中，子按钮 Visible 无法覆盖该限制；都要求根据父容器是否需输入条件化选择 SelfHitTestInvisible 或允许父级命中的配置，并保持延迟不变做对照。两者都拒绝用 500ms 验证持续的祖先命中限制。 |
| DBG-02 E3：在缺少完整层级与日志时保留对实际故障根因的限定 | pass | pass | Baseline 将推论限定为当前运行实例的祖先在点击时确为该值，并保留覆盖、禁用、输入模式、捕获及绑定等分支。Forward 同样限定当前实例祖先与版本语义适用，要求区分设计时/动态/运行时配置，保留覆盖、禁用、几何与捕获等分支。两者均未宣称唯一根因已查明。 |
| DBG-02 E4：提供输入命中及正常子控件交互的回归验证 | pass | pass | Baseline 要求原失败/单一父级修改对照、命中路径包含按钮、Hover/Pressed/Released/Clicked 到达且业务动作一次；覆盖首次打开、重开、动态可见性和穿透需求。Forward 检查命中→派发→按下释放→点击→业务→回显，验收单次动作并回归兄弟按钮、父级交互、隐藏恢复和重开。两者均含正常交互与输入证据。 |

结果：Baseline **8 pass / 0 partial / 0 fail**；Forward **8 pass / 0 partial / 0 fail**。八项均为“保持正确”，没有观察到从缺项到满足的期望级改善。

窄范围差异：Forward 另外提醒先检查日志开关、输出位置和采样，避免把无日志等同于未执行；要求保留偶发问题的触发次数与观测窗口，强调短时间未发生不证明消失；明确回归兄弟按钮。Baseline 则明确提出 Widget Reflector、Hover/Pressed/Released/Clicked 分段计数和仅在已有验证版本存在时考虑演示回退。这些是具体方案内容的不同；原有期望在两臂均已满足，不能据细节增减推断整体更优。

背景混杂：Baseline 报告实际读取了宿主 `systematic-debugging` 和 `ue-ui-umg-slate`，Forward 只读取含 SUBAGENT-STOP 的 `using-superpowers` 加候选 debugging 与两份参考。两臂背景资料不一致，因此并非只改变候选技能一个变量；尤其不能将正确命中测试语义或证据驱动诊断全归因于候选。Forward 关于 UE 5.7.4 已核验的断言来自所给参考，本审阅没有核查该来源内容、版本或验证过程。两臂均无游戏现场、资产、源码或运行结果。

## skillforge-ue-cpp

输入：`skills/skillforge-ue-cpp/evals/behavior-cases.json`、`ue-cpp-baseline.md`、`ue-cpp-forward.md`。E1–E4 仍对应每题 expectations 的原始顺序。

| 案例 / 期望 | Baseline | Forward | 原始回答证据及同口径判断 |
|---|---|---|---|
| CPP-01 E1：区分对象所有权、GC 可达性与非拥有观察引用，不把 TObjectPtr 当万能保活或线程保证 | pass | pass | Baseline 先查缓存的持有者、容器与拥有/观察责任，观察缓存用弱引用；需要保活时才在合适 UObject 持有者中使用 GC 可见的 UPROPERTY/TObjectPtr，并否定单纯替换解决线程、捕获或旧界面问题。Forward 同样区分观察与成员持有责任，明确外层持有者可达及 GC 反射链，否定类型替换的线程和业务归属保证。两者都说明 AddToRoot 的长期滞留与手动释放责任。 |
| CPP-01 E2：检查对象生命周期、回调线程以及加载请求是否仍属于当前界面或关卡 | pass | pass | Baseline 分别检查 this 的真实类型、发起/完成/清理、加载 API 的线程约定和切回游戏线程窗口，并核对当前关卡、界面、请求及旧请求覆盖。Forward 逐项检查发起者与 Widget 生命周期、已入队取消窗口、回调与 UI 访问线程、界面复用及世界/请求归属。两者都不把仍存活当成仍属于当前业务场景。 |
| CPP-01 E3：给出弱引用重新校验、失效请求处理和必要时游戏线程派发的有条件方案 | pass | pass | Baseline 根据 this 是否为 UObject 选择弱绑定/弱指针，非 UObject 不硬套；实际更新时重新校验，API 不保证游戏线程才派发，携带请求标识拒绝旧结果，并保留取消后回调保护。Forward 在派发后实际写入点重取弱对象并核对代次/会话/世界，过期丢弃，清理使会话失效且不信任取消能阻止入队回调，非 UObject 使用相应生命周期协议。均给出条件与执行位置。 |
| CPP-01 E4：根据实际工程识别构建目标与版本，区分源码建议、编译和切关回归状态 | partial | partial | Baseline 开始要求“确认 UE5 的具体版本”，末尾仅说“按实际版本和目标执行相关编译与运行回归”；未说明如何发现该工程的目标。Forward 开始列出工程说明、.uproject、相关插件与模块配置以确认版本，但目标只在末尾“取得实际工程版本、目标和代码后”出现，没有明确从何识别构建目标。两者都详细列出切关/销毁/GC/旧请求回归并诚实声明未执行，因此属于部分覆盖。Forward 增加版本资料来源，不足以补齐同一项中的目标发现方法；不借 CPP-02 的 Target.cs 步骤替任何一臂补分。 |
| CPP-02 E1：从当前项目而非旧项目路径推断模块、Target 和构建配置 | pass | pass | Baseline 明确读取本项目 .uproject、Build.cs、实际 Target.cs、引擎关联与本机安装、平台和构建说明，按真实目标/配置派生构建入口参数，拒绝复用 LGame。Forward 同样读取当前配置与实际 Target.cs，进一步把 EngineAssociation 映射到引擎位置并必要时查 Build.version，按目标、平台和调试需求选择命令。两者都有目标发现材料和派生命令的方法。 |
| CPP-02 E2：检查 reflected declaration、generated include、跨模块符号与蓝图使用契约 | partial | pass | Baseline 检查 UObject 反射声明、UHT 参数/返回值、类型与符号所属模块及 Public/Private 依赖，区分 Callable/Pure、副作用、成本、空值与错误反馈；没有检查 generated include，亦未明确检查 API 导出。Forward 保留这些契约检查，并具体检查 UCLASS、GENERATED_BODY()、头文件对应的 .generated.h 且为最后一个 include，以及跨模块 API 导出。通过差异在于新增可执行的头文件一致性/顺序及导出检查，不是仅出现 generated.h 单词。 |
| CPP-02 E3：仅在任务实际涉及多人状态时引入网络权限检查 | pass | pass | Baseline 仅在真实联网权限需求时设计 authority/RPC，验证也只在函数确有联网行为时增加。Forward 仅在需求和调用链涉及多人共享状态、复制或远端调用时补权限、RPC 及网络角色验证。两者均拒绝把 Listen Server 设成所有普通工具项目的前提。 |
| CPP-02 E4：提出 C++ 构建与受影响蓝图编译/调用验证，未执行时不声称通过 | pass | pass | Baseline 要求运行 UHT 的正常构建而非只依赖 Live Coding，检查节点、分类/引脚、调用方蓝图编译及正常/边界输入，仅对实际相关运行时目标补验证；明确没有读工程或执行测试。Forward 同样区分 UHT/构建、节点发现/签名/兼容、蓝图编译及正常/无效/失败调用，并明确未读工程、未修改、未构建或运行。两者都给出验证对象和诚实执行状态。 |

结果：Baseline **6 pass / 2 partial / 0 fail**；Forward **7 pass / 1 partial / 0 fail**。CPP-01 E4 在两臂保持 partial；CPP-02 E2 出现一次从 partial 到 pass 的可观察覆盖增加。其他六项保持正确。不能复用 Forward 作者自查的 8/8 结论。

窄范围差异：Forward 在 CPP-01 更明确点出 Widget 关闭后重用、A/B 逆序完成和取消时回调已排队的验证场景，但 Baseline 已覆盖生命周期、旧请求与取消后防护，对应期望均已通过。CPP-02 的 generated include/顺序和 API 导出检查是上述唯一改变整项判断的增量。二者都未提供真实目标、成功构建、蓝图调用结果或崩溃消失证据。

背景混杂：两臂都报告只读取宿主 `using-superpowers` 并遵循 SUBAGENT-STOP；Forward 另外读取候选技能及 `ownership-lifecycle.md`、`reflection-build.md`。这比 debugging 的额外背景差异更少，但仍只有每题每条件一次、精确后端模型 ID/推理设置不可核验、同一臂两题共用上下文以及宿主指令和模型既有能力等限制。此次输出差异与候选技能因果增益不能等同；稳定改善、其他 Agent 适用性和真实 UE 项目成功率均未证明。

## 本次审阅结论

四个案例共 16 个期望：Baseline 14 pass、2 partial、0 fail；Forward 15 pass、1 partial、0 fail。这是本次文本覆盖的计数，不是成功率估计。Debugging 保持正确；UE C++ 仅 CPP-02 的完整声明/头文件/符号检查覆盖增加，CPP-01 的目标发现缺项两臂均保留。候选资料正确性、结构/触发能力与真实工具执行效果需由各自证据另行判断，本审阅不替代它们。
