# 最终独立内容审查

日期：2026-09-12。审查者：独立审查子任务 `early_review`，未编写四个技能正文或校验器实现。

范围：四个技能的 `SKILL.md`、`references/`、触发与行为用例，校验器、测试、README 及 docs。正在编写的最终 summary 和实施进度收尾不作为缺陷。本记录不是模型行为评分，也不是用户或真实 UE 项目的验收。

## 发现

### FCR-01 — [P2] 单段绝对 POSIX 路径未被可移植性检查识别

- 位置：[scripts/validate_skills.py](../../../scripts/validate_skills.py) 第 43 行的 `UNIX_PATH`，由第 138 行的正文检查使用。
- 状态：主任务已接受，等待修复复核。
- 原因：正则要求根目录下首段之后至少再有一个非空路径段，因此只能识别诸如 `/etc/config.json` 的多段路径，遗漏明确的 `/tmp`、`/config.json` 和 `/opt/`。
- 复现：使用现有测试辅助方法创建有效临时技能包，在 `SKILL.md` 正文分别追加 `Use /tmp as the required working directory.`、`Read the configuration from /config.json.`、`Use /opt/ as the required working directory.`，其中路径均包在 Markdown 反引号内。每次运行 CLI 并传入 `--self-contained`，三例退出码均为 0，输出均为 `Validated 1 skill(s): 0 error(s); 1 standalone copies validated.`。
- 影响：包含明确宿主绝对路径依赖的后续技能仍可能被复制校验判为通过，超出脚本文档所描述的绝对路径检查边界。当前四个正式技能没有这些路径，未发现由此导致的现有技能内容问题。
- 建议：识别单段及带结尾斜杠的绝对路径，并增加相应回归；同时保留 HTTPS、包内相对路径与 Unreal 虚拟对象路径的有效用例。若有意不覆盖这些形式，应明确缩小文档中的检查范围。

## 其余审查结论

未发现其他可操作问题。四个技能的触发说明与当前用例一致；组合技能为可选补充，包内参考没有要求读取其他技能、本机历史目录或固定宿主 API。UE 规则没有被强加到 MFC/通用 UI 任务。案例分别标明源码/文档核验、方法候选及尚未运行的场景，没有把技能方案或结构通过写成资产已修改、编译通过或故障已修复。

早期审查发现的 YAML 名称类型歧义已有针对性修复：名称支持 JSON 双引号形式，plain 名称拒绝保留标量及数字开头形式；当前代码、四项新增测试与 research.md 对写作子集的说明一致。本轮未重复运行全部 26 项测试；26 项通过为主任务提供的已有验证结果。

## 本轮实际检查及边界

- 执行 `python scripts/validate_skills.py --self-contained`：退出码 0，输出 `Validated 4 skill(s): 0 error(s); 4 standalone copies validated.`。另外执行了 FCR-01 的三个临时包复现；未修改正式技能或测试文件。
- 读取本机 `Engine/Build/Build.version`，确认 UE 5.7.4、CL 51494982。核对 `SlateWrapperTypes.h` 的可见性注释；其 SHA-256 与 research.md 一致。
- 核对 `WidgetTree.cpp` 第 191、234 行附近的普通容器递归，以及 `WidgetBlueprintGeneratedClass.cpp` 第 270–275 行的同名属性赋值；`WidgetTree.cpp` 的 SHA-256 与 research.md 一致。现有说明正确区分普通 Panel 嵌套和另一 UserWidget 内部树。
- 核对 `SConstraintCanvas.cpp` 第 246–280 行的拉伸、AutoSize 和远侧 Offset 分支，及 `CanvasPanelSlot.cpp` 第 182–186 行的 `SetSize` 赋值。现有 Canvas 条件说明与源码相符。
- 核对 `Actor.cpp` 第 4388 行的 `ExecuteConstruction` 调用，以及 `ActorConstruction.cpp` 第 937、997、1014 行的用户构造脚本路径。该证据支持“不能概括为只在编辑器执行”，没有证明某个具体项目的构造/初始化行为已经验收。
- 查看 [Epic Actor Lifecycle 当前页](https://dev.epicgames.com/documentation/en-us/unreal-engine/unreal-engine-actor-lifecycle) 与 [UMG Optimization 5.7 页](https://dev.epicgames.com/documentation/en-us/unreal-engine/optimization-guidelines-for-umg-in-unreal-engine?application_version=5.7)，并沿用早期审查已读取的 [Object Pointers 5.7 页](https://dev.epicgames.com/documentation/en-us/unreal-engine/object-pointers-in-unreal-engine?application_version=5.7)核对引用边界。当前页与版本化证据在文档中有区分。

本轮没有启动 Unreal Editor，没有创建或修改资产，没有运行 UHT、项目构建、PIE、打包、真实 UI 输入回归或性能测量。原始本机资料的六份溯源快照由主任务记录；本轮未重新读取这些原始资料来认证其全部内容或 Git 状态。

## FCR-01 修复复核追加

状态：**已修复，定向复核通过**。以上原始发现及当时状态保留为审查历史。

只读核对修复后，`UNIX_PATH` 已允许零个后续路径段及结尾斜杠；正文检查同时保留 `/Game`、`/Engine`、`/Script` 虚拟根与各自子路径。新增回归覆盖正文/参考资料 × 三种单段路径 × 普通/独立复制两种模式，共 12 个拒绝子例；另一测试保留 Unreal 虚拟根、对象路径和有效临时包原有 HTTPS/相对资源引用。

独立执行：

```text
python -m unittest -v tests.test_validate_skills.ValidateSkillsTests.test_single_segment_absolute_posix_paths_are_rejected tests.test_validate_skills.ValidateSkillsTests.test_unreal_virtual_roots_and_paths_remain_portable
```

实际结果：退出码 0，`Ran 2 tests in 1.421s`，`OK`。本追加只认证补丁及上述定向回归；新增测试在修复前失败的记录、修复后的四包复制结果由主任务提供，未在本追加阶段重复执行。完整测试由主任务另行运行。

本审查所发现的问题现已全部关闭；未修改技能、校验器、测试或原始评测回答。
