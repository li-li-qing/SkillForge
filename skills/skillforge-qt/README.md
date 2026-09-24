# skillforge-qt v0.1.0

面向 C++ Qt 桌面工具的第一版工程 Skill。主入口见 [SKILL.md](SKILL.md)，不是把 GitHub 示例代码拼成应用模板。

## 面向当前使用方式

用户已决定从 MFC 转向 Qt；本包不重复劝迁移，也不把仍未知的 Qt 工程配置写死。LCot 的实际 Qt 版本、位宽、编译器、Widgets/Quick 选择、COM 宿主形式都应在首次接入时从当前工程核实。迁移规则单列，完成迁移后的普通 Qt 任务不反复读取旧 MFC 资料。

主入口短，主题参考按需读取；既覆盖工具型 Widgets，也覆盖真实存在的 Quick 分支，不要求所有任务混用两套 UI。没有大漠 Skill 也能读取本包的 COM/STA 规则；具体大漠函数仍以用户实际版本接口文档为准，禁止猜 API。

## 使用

使用宿主真正支持的技能安装/读取方式；本包没有固定安装路径、专用命令、宿主 metadata 或自动安装脚本。复制整个 skillforge-qt 目录而不是只复制 SKILL.md。只读文件的宿主可以按文件执行规则，但不能报告“已原生安装”。

```text
使用 skillforge-qt。先读取当前工程和项目指令，再处理下面的 Qt 任务：
<本次需求>
请按需读取参考资料，保留现有业务功能，列出所有权与线程边界，
最后交付改动文件、实际验证结果以及未运行项目。
```

```text
使用 skillforge-orchestrator，结合可发现的 skillforge-qt 处理：
<本次需求>
当前项目已经决定采用 Qt，请以当前工程核实版本和架构，
不要根据旧 MFC 记录重新选择框架或重复要求确认已批准的范围。
```

这些是自然语言示例，不假定某个快捷命令一定存在。只设计时写“仅设计，不改产品代码”；已经决定执行时写清本次允许的范围。

## 内容和验证含义

- [项目事实表](assets/project-profile.md)防止把其他项目配置当当前事实。
- [审查与交接表](assets/review-handoff.md)记录根因、线程、影响面和证据。
- [来源研究](references/github-sources.md)及 [机器可读来源表](references/source-manifest.json)列出六个项目的固定提交和本轮已读切片；并非完整仓库审计。
- [评测说明](evals/README.md)含触发与行为题集。题集存在不表示模型已答对；未运行真实 Agent A/B 评测。

本版不附第三方代码、字体、Qt SDK、二进制依赖或 LCot 源码。未构建 LCot，未在 Windows 上测试 Qt UI、IME、DPI 或大漠。
