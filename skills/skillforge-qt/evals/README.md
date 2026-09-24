# Qt Skill 评测题集

本目录是待运行的评测规范，不是评测成绩。结构脚本只能检查文件/字段/链接与覆盖数量。

[触发题](trigger-cases.json)：18 题，覆盖应触发、不触发与有条件触发。判定应同时看 prompt 与 context；Qt 关键词不是唯一证据。

[行为题](behavior-cases.json)：24 题。每题提供完整情景和至少四项应观察行为。重点是禁止错误迁移、输入覆盖、线程互等、模型身份混淆和假绿报告，同时检查适度实现而非无限加架构。

## 真正运行方法

在具有独立执行/对话能力的评测环境，固定模型、工具、项目材料和题目；建立不提供本 Skill 的基线，再在独立上下文提供本 Skill 与允许按需读取的资源。保留原始输出，不把自评写成独立 Agent 实验。

按 expectation 逐条记录 met / not_met / not_observable，不用单一总体“看起来不错”。严重失误包括：编造工程版本、跨线程改 GUI、误改排序行、假报取消、虚构测试、无授权删除或源码许可保证。遇到这些即使其他项良好也单独标阻断。

要验证真实实现效果，将题目对应到可运行的小工程或当前项目：输入中刷新、代理排序、关闭时忙碌、旧代际响应、IPC 模糊完成。文字方案通过不能替代这类运行证据。

## 当前状态

agent_baseline: not_run
agent_with_skill: not_run
real_qt_project: not_run
windows_ui_ime_dpi: not_run
real_com_dmsoft: not_run

当前环境未提供独立 Agent 评测运行器，也未提供 LCot Qt 工程。没有编造 RED/GREEN 行为分数。仓库新增的结构测试有真实先失败后通过记录，其范围仅是技能包契约。
