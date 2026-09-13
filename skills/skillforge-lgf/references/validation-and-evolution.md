# 验证、文档与持续演进

## 事实、规范、决策与执行分开

源码已有不等于客户端已运行正确；设计冻结不等于源码已落地；文件名带 CONFIRMED 不等于本轮获准实施。按当前任务授权处理范围，并核对尚未解决的设计前置。

取材版本 WorldMap 主题入口位于 `重构文档/WorldMapArchitecture/README.md`，P0 已冻结、O3 仍为 P1 前置；当前模块没有 WorldMap。结构重构文档正文写仅记录，未实施。学习/文档/技能维护不应据此新建模块或移动生产类型。

后续用户明确发起实施任务时，以该轮授权和现行决策确定工作；不要重复索要已经给出的授权。真正缺少实施所需的设计决定时，先完成不依赖该决定的可审查工作，再明确指出缺的具体内容。

冻结历史文档保留，现行入口与新反馈在其负责位置更新。不要重建已经移除的旧稿，或复制同义的“最新总览”。

## 验证按改动选择

| 改动 | 适用检查 |
|---|---|
| 技能/说明 | 结构、相对引用、技术来源、触发与行为案例 |
| 反射/C++/模块依赖 | 实际目标的 UHT、编译、链接；依赖变化核对 Client/Server |
| 蓝图/软引用/资产 | Blueprint 编译、Data Validation、加载与相关 Cook/Package |
| Gameplay/复制 | 原失败路径与正常路径，Host/Remote/Proxy，按影响补 Dedicated、JIP、延迟/丢包、重连 |
| 生命周期 | 对象销毁、死亡复活、Pawn/Avatar/Controller 更换、Travel、旧请求迟到 |
| UI 路由/迁移 | 当前迁移扫描、所选 Presenter、Back/Replace、LocalPlayer 与输入恢复 |
| 发布 | BuildPlugin、Cook/Package、实际交付文件与内部文档链接 |

从当前 `.uproject` 和 `Source/*.Target.cs` 获取真实宿主目标，排除 Saved/BuildPlugin 下的临时 HostProject。源文件中有测试声明只证明存在测试；记录本次过滤器、目标、执行数量与输出后才能称通过。

当前实际存在的迁移类为 `ULGameplayUIMigrationCommandlet`，实现位于 UIEditor 的 `LGameplayUIMigrationScanner`，不要求文件名一定含 Commandlet。可在确定宿主与引擎后使用：

```text
UnrealEditor-Cmd.exe <实际Project.uproject> -run=LGameplayUIMigration -unattended -nop4 -nullrhi
```

先核对本轮实现，当前预期报告为 `Saved/LGFUIRefactor/UIMigrationReport.json`。旧 Python UI 拓扑脚本在取材插件树中不存在，不能运行或伪造通过；这不影响 Commandlet 的存在性判断。迁移扫描也不代替完整网络测试。

取材时 `Config/FilterPlugin.ini` 显式附加三份公开文档和 Scripts 规则，却没有显式列出 Docs/Backlog；Scripts 目录不存在。源工作区链接可用不等于发行包包含这些文件，发行任务应检查实际 BuildPlugin 产物。

## 文档维护

- 类型/签名/元数据变化更新 API；资产创建和接线变化更新 Tutorial；模块定位/依赖更新 README。
- 当前代码差异和本轮验证状态放当前维护入口，历史成功报告不替代本轮结果。
- 阅读真实声明判断 BlueprintCallable/BlueprintNativeEvent/C++ virtual/RPC，不能仅凭函数名提供蓝图节点教程。
- 代码修改遵循当前项目维护规则，说明原因、Authority/所有权、数据流及兼容风险；说明不能代替实际实现和验证。

## 从反馈完善技能

一条记录至少能回答：用户预期、实际症状/触发、版本与加载配置、证据、已证实原因或待验证假设、修复、实际验证及剩余问题。先从已有材料补齐，不要求每次小修都写完整审计报告。

能跨 LGF 消费工程复用的结论进入对应主题参考；项目自己的门资产、动画配置、当轮任务进度留在消费工程。通用 UE 规则确认后可提炼到通用技能，但不带入 LGF 的特定返回类型或模块名。

资料量由解决问题所需决定。增加细节时同时给出读取条件、来源和能暴露错误的用例；失效结论原位修正，保持单一现行入口。不能把“有测试”“有接口”或“文本评测通过”写成真实游戏已验证。
