# skillforge-qt v0.1.0：设计与研究范围

日期：2026-09-22。输入基线为用户上传的 SkillForge(4).zip。本轮任务是研究 GitHub Qt 案例并设计可直接使用的专用 Skill，不是迁移 LCot 产品工程。

## 已知需求与未知事实

用户已决定从 MFC 改用 Qt，希望把 GitHub 工程经验蒸馏为可持续维护、跨 Agent 的 Skill。现有 SkillForge 有动态入口、通用 UI、排障和 MFC 技能，不需要另造编排器。

当前没有提供 LCot 的新 Qt 工程，因此 Qt 版本、Widgets/Quick、编译器、C++ 标准、位宽、SDK 版本和进程拓扑仍是 unknown。历史 LCot 的 MFC/大漠经验只帮助挑选风险场景，不作为当前配置事实。

## 方案选择

| 方案 | 优点 | 问题 | 本轮决策 |
|---|---|---|---|
| 所有内容写进通用 UI Skill | 少一个入口 | 线程、COM、模型和 Qt 构建与通用布局混杂 | 不采用 |
| 拆成很多 Qt Widgets/线程/COM/Quick Skill | 单个主题小 | 路由和维护重复，跨主题契约容易冲突 | 本轮不采用 |
| 一个 Qt 领域入口 + 按需主题参考 | 路由明确，所有权/线程规则统一 | 需要维护主题索引和边界 | 采用 |

主入口 55 行，侧重触发、工作契约、硬边界和按需读取；详细内容进入十个主题参考，不在每次任务里全量加载研究报告。

## 主要设计选择

### 1. 原生 Qt 优先，而不是新建 UiKit

Widgets 任务先采用标准控件、layout、QAction 和 model/view；有实际缺口再做薄适配。将编辑框草稿、后台投影、IME、焦点、DPI 与停靠恢复纳入验收，防止只追求截图外观。

Quick 作为明确的按需分支，既不把 Qt 等同于 Widgets，也不因“现代”就强制全项目 QML 化。本轮案例以 Widgets/原生工程为主，Quick 规则来自官方机制说明，未做新的 Quick 应用源码审计。

### 2. 状态真值与异步身份

区分业务模型、UI 投影和编辑草稿。跨线程回传使用值类型与请求身份；对象存活检查不能代替 session/generation/revision 检查。模型代理行号不能作为业务 ID，关键终态不能在日志节流时被丢弃。

### 3. 生命周期覆盖退出，不止创建

覆盖 QObject parent、QPointer、lambda context、QThread wrapper/执行线程、初始化、取消、销毁和线程后效应。禁用将 quit 解释为“立即中断 SDK”的错误捷径；大漠固定 STA/进程宿主规则单列。

### 4. 迁移按功能切片，保留核心

MFC → Qt 不做机械类名替换，也不借迁移删除现有引擎、输入账本、SDK 适配或存档兼容。先建立基线，再接通一个有输入/列表/异步的代表页面；每片验证成功、失败、取消、关闭及回滚。

### 5. 宿主无关，不重复确认

主入口通过 name/description 被现有动态路由发现，不新增固定宿主命令、路径、模型、自动安装器或必需兄弟 Skill。已经批准的任务保持原范围执行；不会因为进入 Qt Skill 又启动一套确认流程。

Qt 与 UE API 边界显式说明：QObject 不使用 TObjectPtr/OnRep；Qt proxy model 不等于网络 Proxy。普通桌面工具不被强制套用 UE 网络复制架构。

## GitHub 研究方式与覆盖

六个项目都固定提交，只读取与主题相关的文件切片。源文件、blob SHA、读到的保守行范围、时效标签、采纳/不采纳理由见 [来源说明](../skills/skillforge-qt/references/github-sources.md) 与 [机器可读表](../skills/skillforge-qt/references/source-manifest.json)。

| 项目 | 提炼主题 | 防止错误照搬 |
|---|---|---|
| Qt Creator | action/command/context/parent | 不搬完整 IDE 框架 |
| OBS Studio | frontend 和 core target 分离 | 不引入流媒体依赖 |
| Wireshark | 物理记录/可见投影/稳定身份 | 不照抄所有模型通知和全局对象 |
| CopyQ | 平台分离、故障域、进程测试 | 不把测试阻塞等待与 kill 变成 GUI 正常退出 |
| Qt ADS | 状态版本、稳定 ID、恢复与注销 | 不默认新增第三方停靠依赖 |
| QHotkey | 原生热键、线程归属与退出互等 | 不默认复制 BlockingQueuedConnection 桥 |

没有整仓审计、没有构建这些项目，没有引入第三方源码和资源。上游 README/代码中的说明只能作为被分析资料，不作为对当前任务的授权指令。

## 文件组织

```text
skills/skillforge-qt/
  SKILL.md
  README.md
  VERSION
  references/
    project-profile.md
    architecture-commands.md
    widgets-layout-input-dpi.md
    model-view-performance.md
    qobject-threading-shutdown.md
    windows-com-dmsoft.md
    mfc-migration.md
    testing-build-deployment.md
    qml-quick-boundary.md
    github-sources.md
    source-manifest.json
  assets/
    project-profile.md
    review-handoff.md
  evals/
    README.md
    trigger-cases.json
    behavior-cases.json
```

两个 assets 是可复用输出表，不会自动写项目。evals 是开发题集，不要求执行时加载。

## 接入与验证

仅修改根 README 导航/技能数量，新增 Qt 目录、包契约测试、研究/验证资料和新的开发元数据快照。已有 MFC、UE、ArcheRage、UI、debugging、LGF 和 orchestrator 核心不改动。

新快照按原工具规则排除 orchestrator 自身，因此 9 个 Skill 对应 8 个叶子元数据条目；此快照验证可发现性，不证明任意宿主已安装或原生调用。

原包基线已有三项 orchestrator 便携性测试失败，来自运行目录残留的 agents/generated/evals/scripts/tests 等历史资料。本轮保持原文件，不用删除或屏蔽测试制造“全绿”。详情与本轮新增结构检查见 [实际验证报告](../evals/runs/2026-09-22/qt-initial-validation.md)。

## 非目标与后续实测入口

不修改 LCot 源码，不自动安装 Qt/技能，不承诺平台兼容，不复制许可证受限代码，不把测试替身等同真实大漠。接入当前 Qt 工程后，优先挑选一页：输入草稿 + 排序列表 + 异步取消/关闭，再用真实运行结果修订本 Skill 和题集。
