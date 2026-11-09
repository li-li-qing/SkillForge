# StateTree All失败语义澄清

2026-11-07文档核查，未连接或运行UE。原参考“ALL=所有participating tasks完成”漏了成功/失败分支，容易让读者在一任务失败时仍等待其他任务。

官方来源：
- https://dev.epicgames.com/community/learning/tutorials/lwnR/unreal-engine-your-first-60-minutes-with-statetree ：James Keeling，页面UE5.4标签，2024-06-20发布、2025-08-28更新；StateTree Transition Selection段明确说明5.6变化。All成功需所有被计入任务成功，失败仍触发失败转换。
- https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/StateTreeModule/EStateTreeTaskCompletionType ：当前5.8，C++名称All/Any，StateTreeTasksStatus.h；简短枚举注释本身未详述失败分支，不能单凭此注释推断失败也等待。
- https://dev.epicgames.com/documentation/unreal-engine/API/Plugins/StateTreeModule/FStateTreeTaskBase?lang=en-US ：当前5.8，bConsideredForCompletion及编辑能力字段。
- https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/StateTreeTaskCompletionType.html ：当前5.8实验Python API使用ALL/ANY大写。

最小修改ue-cpp参考、LGF自包含参考及一条not_run行为规格。只澄清成功合取/失败路径和版本证据，不改架构或脚本。失败退出取消/解绑/迟到回调是待验证工程检查项，不假装官方证明项目实现正确；无可用transition时回退/重选/终止须目标版本源码和资产验证，未泛化教程默认行为。
