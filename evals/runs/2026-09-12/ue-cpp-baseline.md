# UE C++ baseline — 2026-09-12

## Run record

- Condition: baseline; the candidate `skillforge-ue-cpp/SKILL.md` and its references were not read. The candidate skill was not written when this run was assigned.
- Model identity: the host developer instruction describes this agent as Codex, based on GPT-6. An exact serving model ID or backend configuration was not exposed to this evaluator; none is inferred.
- Scope: text analysis using only the two supplied scenarios. No game project files were accessed or edited. No build, editor, runtime, or crash-reproduction experiment was performed.
- Evaluation instructions read: `D:/Project/Skills/evals/README.md`.
- Background host skill actually read: `C:/Users/23118/.codex/plugins/cache/openai-curated-remote/superpowers/6.3.0/skills/using-superpowers/SKILL.md`. Its `SUBAGENT-STOP` instructs dispatched subagents to ignore the skill. No other host skill or host-skill reference was read. Host instructions and the available-skills catalog remain part of the context, so this is not a skill-free model measurement.
- Prompt handling: PowerShell parsed `skills/skillforge-ue-cpp/evals/behavior-cases.json`. An initial inspection returned only collection-property names and types. The next inspection emitted only `id` and `prompt`. The `expectations` values were not shown to the evaluator until after both raw answers below had been saved.
- Tools used before saving raw answers: `functions.exec` for orchestration; `tools.exec_command` for four read-only PowerShell calls (host skill, evaluation README, collection shape, and projected IDs/prompts); `tools.apply_patch` to create this result file. No browser, external reference, game-project tool, or delegated agent was used.
- Assessment: the later per-expectation check is an evaluator self-check, not an independent human review. A single baseline run cannot establish comparative improvement.

## Raw answers (saved before reading expectations)

### CPP-01

当前描述支持一个优先排查方向：异步回调完成时，捕获的对象、缓存的 Widget 或它们所属的关卡环境可能已经失效。但还不能确认根因；也不能确认回调在哪个线程执行。下面是检查与修复方案，没有修改或验证真实工程。

先检查这些内容：

1. 确认 UE5 的具体版本、加载 API、完整回调与发起位置，以及回调所捕获的 `this` 的实际类型。拿到崩溃调用栈、切关时序、对象销毁与回调执行的日志，判断是失效访问、线程问题，还是两者叠加。
2. 追踪加载请求由谁持有，回调是否可能在切关、Widget 移除或所有者销毁后继续执行。检查请求句柄、委托绑定、取消和解绑路径，以及当前对象的相应生命周期清理函数。具体清理位置取决于它是 Actor、组件、Widget、子系统还是普通 C++ 对象，不能直接假定一个通用的销毁钩子。
3. 检查缓存 Widget 指针的声明、存储容器、持有者及预期所有权。它是应当保持 Widget 存活的成员，还是仅观察界面的缓存？对象是否受 GC 跟踪？缓存中的 Widget 即使仍然存在，是否还属于当前关卡、当前界面或当前加载请求？
4. 根据该版本实际使用的加载 API 确认回调线程；检查是否从非游戏线程访问 UObject、缓存或 UI，以及切回游戏线程之前与之后是否存在销毁窗口。还应检查快速切换图标时旧请求覆盖新请求的可能性。

最小修复应针对确认的生命周期问题，而不是批量改指针：

- 如果 `this` 是 UObject，不让可晚到的回调无条件解引用捕获的裸 `this`；使用合适的 UObject 弱绑定或捕获 `TWeakObjectPtr`，在实际执行更新时重新取得并检查对象。若 `this` 不是 UObject，则应依据该类型真实所有权安排生命周期和取消机制，不能套用 UObject 弱指针。
- Widget 缓存只观察外部界面时，优先使用弱引用并在使用前检查；如果成员确实负责保持 Widget 存活，可在合适的 UObject 持有者中采用 GC 可见的强引用，例如 `UPROPERTY()` 标记的 `TObjectPtr<UUserWidget>` 成员。具体修改必须先看成员所在类型与容器。仅将裸指针改为 `TObjectPtr`，并不自动解决回调捕获、GC 可见性、线程或过期界面的问题。
- 在正确的生命周期结束路径取消加载、解绑回调并清除缓存；同时保留回调中的有效性检查，因为取消或解绑未必能阻止已经开始执行或已排队的回调。
- UI 更新放在游戏线程进行。如果该 API 不保证游戏线程回调，就按当前工程支持的机制调度回游戏线程，传递弱引用及请求标识，并在真正更新时再次检查。用请求序号、界面实例或关卡上下文识别旧结果，避免存活对象接收已经过期的加载结果。
- 不将 `AddToRoot` 当成常规修复。它可能让本应销毁的对象被长期保留，而且不能证明旧关卡的 UI 仍适合更新，也不能修复线程错误。只有真实所有权设计明确需要这类手工管理时，才考虑成对、完整的释放责任。

验证应先建立可观察证据，再检查修复是否覆盖故障时序：在开发环境记录请求 ID、发起与完成时间、执行线程、所有者与 Widget 的生命周期和关卡身份；人为延迟加载，在完成前切关、关闭界面或销毁所有者，重复快速切换请求，并在适当的测试环境加入 GC 压力。检查没有崩溃、没有非游戏线程 UI 更新、旧结果没有写入新界面、正常加载仍能显示图标，且反复切关后对象和请求不会持续滞留。最后按实际版本和目标执行相关编译与运行回归。这里尚未取得代码、调用栈或执行结果，因此不能宣布根因已确认或问题已修复。

### CPP-02

先从当前工具项目的配置和接口用途确定方案。现有描述没有证明它采用 LGame 的目标名称、模块结构或联网架构，因此同事的编译命令和 Listen Server 要求都不能直接作为当前项目的约束。这里没有提供工程内容，我只能说明检查与验证步骤，不能给出已经核实的依赖清单或构建命令。

我会先读取当前项目的 `.uproject` 和相关 `Build.cs`，确认启用的模块与插件、模块类型和已有依赖；再定位声明 `UFUNCTION` 的类、头文件和实现，检查它实际使用的类型与 API。还需查看实际存在的 `Target.cs`、引擎关联与安装位置、目标平台和项目的构建说明。`.uproject` 的关联信息需要对应到本机真实引擎，不能只凭一个 UE5 标签猜版本和路径。

模块依赖按该函数真正引用的类型及符号所属模块确定。公共接口向其他模块暴露的依赖通常进入 `PublicDependencyModuleNames`；仅实现文件内部使用的依赖通常进入 `PrivateDependencyModuleNames`，并结合前置声明、包含关系和实际编译需求判断。只添加实际需要的模块，不因为“给蓝图用”就添加一组模板依赖。若函数调用编辑器 API，要确认它应属于 Editor 模块，并检查边界，避免将编辑器专用依赖带入需要运行时构建的模块。插件是否启用和模块依赖声明也是两个需要分别核实的条件。

蓝图暴露方式先由函数语义决定：有副作用的操作通常采用 `BlueprintCallable`；只读查询才考虑 `BlueprintPure`，并确认成本与重复求值是否适合蓝图使用。检查类本身是否具备相应的 UObject 反射声明、访问范围和蓝图使用条件，以及参数、返回值、输出参数和对象引用是否能被 UHT 正确处理。根据使用者选择清楚的分类和必要元数据，检查空对象、错误反馈和编辑器适用范围。若它是独立的工具函数，是否需要函数库应由现有设计与状态依赖决定，而不是为加一个节点重构项目。只有需求确实涉及联网权限时才设计 authority 限制或 RPC；普通工具项目没有理由自动继承 Listen Server 架构。

构建命令必须从实际目标派生。先确认引擎提供的构建入口、当前项目的目标名称、平台与配置；例如 Windows 的 Editor 构建可能使用相应引擎目录下的 `Build.bat`，传入查明的 Editor Target、`Win64`、选定配置和当前 `.uproject` 的绝对路径。这里这些值尚未给出，所以不把模板当成可以直接运行的命令。选择 `Development Editor` 或 `DebugGame Editor` 应服从本项目目标和调试需要，不照搬 LGame 名称、路径或配置。对于 `UFUNCTION` 等反射声明变化，要通过会运行 UHT 的正常构建验证；不能只凭 Live Coding 成功判定反射接口已经正确更新。

验证范围包括：先检查 UHT 和目标模块编译结果，再在匹配版本的编辑器中确认节点可以找到、分类和引脚正确、调用方蓝图能编译，并实际调用正常输入和有意义的边界输入，观察返回值与副作用。如果声明仅面向编辑器，就验证相应编辑器使用场景；如果会进入运行时目标，则补充该项目实际支持的运行时目标编译，检查没有混入编辑器依赖。仅当函数确有联网行为时才添加适当的多人验证。构建命令、执行环境和结果都应据实记录。当前没有读取工程配置，也没有执行编译或编辑器测试，以上是待执行方案。

## Per-expectation self-check

The expectations were first displayed after the raw answers above had been written. Those answers have not been revised in response to scoring.

| Case | Expectation | Self-check | Evidence and limitation |
| --- | --- | --- | --- |
| CPP-01 | 区分对象所有权、GC 可达性与非拥有观察引用，不把 TObjectPtr 当万能保活或线程保证 | Pass | Separates an observing cache from a GC-visible owning member; conditions `UPROPERTY`/`TObjectPtr` on the actual holder and explains why pointer replacement cannot resolve captured-owner, thread, or stale-interface problems. |
| CPP-01 | 检查对象生命周期、回调线程以及加载请求是否仍属于当前界面或关卡 | Pass | Requests lifecycle and callback timing evidence, the API's thread guarantee, and identification of the current interface, world, and request before accepting results. |
| CPP-01 | 给出弱引用重新校验、失效请求处理和必要时游戏线程派发的有条件方案 | Pass | Conditions UObject weak capture on the actual owner type; revalidates at the update point, handles queued callbacks despite cancellation, rejects old request results, and dispatches only if game-thread execution is not guaranteed. |
| CPP-01 | 根据实际工程识别构建目标与版本，区分源码建议、编译和切关回归状态 | Partial | Explicitly asks for the exact UE5 version and calls for compilation against the actual version and target, with concrete travel/GC regression scenarios and no claim of execution. It does not explain how to discover the current project's build target; this part remains under-specified. |
| CPP-02 | 从当前项目而非旧项目路径推断模块、Target 和构建配置 | Pass | Uses the current `.uproject`, `Build.cs`, `Target.cs`, engine association and installation, platform, and build instructions to derive dependencies and command arguments; rejects direct reuse of LGame's paths, target, and configuration. |
| CPP-02 | 检查 reflected declaration、generated include、跨模块符号与蓝图使用契约 | Partial | Covers reflection declarations and UHT-compatible parameters, module ownership of types/symbols and public/private dependency placement, plus node semantics and caller expectations. It never explicitly checks the generated header include or its ordering, so the full expectation is not met. |
| CPP-02 | 仅在任务实际涉及多人状态时引入网络权限检查 | Pass | Makes authority/RPC design and multiplayer validation conditional on actual networking requirements, with no universal Listen Server constraint on the tool project. |
| CPP-02 | 提出 C++ 构建与受影响蓝图编译/调用验证，未执行时不声称通过 | Pass | Specifies UHT/module builds followed by node discovery, pin checks, affected Blueprint compilation, and normal/boundary calls. Explicitly states that project reads, builds, and editor tests have not happened. |

Self-check totals: 6 pass, 2 partial, 0 fail. These are per-expectation qualitative judgments; no independent assessor has reviewed them. The baseline already addresses the major ownership, asynchronous lifetime, project-specific build, and networking-scope issues. Comparative improvement is not established by this run.

## Completion record

- After the answers were saved, `functions.exec` / `tools.exec_command` displayed only case IDs and expectations. `tools.apply_patch` then replaced the pending self-check with the assessment above; it did not change either raw answer.
- Final verification uses a read-only PowerShell inspection of this artifact's presence, raw-answer headings, and assessment rows. That artifact check is not a C++ build or runtime validation.
- Only `evals/runs/2026-09-12/ue-cpp-baseline.md` was written by this evaluator. No candidate skill, reference, game project, or other result file was edited. No commit or further delegation was performed.
