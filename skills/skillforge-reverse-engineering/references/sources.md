# 取材依据与边界

核对日期：2026-11-08。社区技能只提供工作流候选；具体机制对照原始输出、官方规范或实际源码。未安装或执行上游脚本，不把项目名、星数或体量当正确性依据。正文为独立整理，没有打包上游技能、二进制或代码。

## 固定提交的社区切片

| 来源 | 读取与采用 | 不采用/限制 |
|---|---|---|
| [cellebrite-labs/ghidra-rpc](https://github.com/cellebrite-labs/ghidra-rpc/blob/fa3866243dcfcbc876baa7b13ae0deac2c443cd8/SKILL.md)；Current | 读取入口/项目与分页部分，并检索类型和重命名条目；采用正确工程身份、截断查询覆盖、类型重分析后的局部变量身份意识 | 不引入 daemon/uv 的硬依赖，不承诺已连接 Ghidra，不自动启动后台服务；本轮未审计其全部实现/许可 |
| [juank115/reverse-engineerskill](https://github.com/juank115/reverse-engineerskill/blob/02a29545cc16599b5f181f082a9d96dbce82791f/skills/reverse-engineering/SKILL.md)；Current | 读取入口/初筛及后部报告部分；采用按任务选择分析深度、未知样本执行与静态读取分离 | 不把面向恶意样本的固定实验室确认流程套到所有正常自有软件，不复制固定长报告和宿主变量；该快照声明 MIT |
| [PyModel/reverse-engineering-skill](https://github.com/PyModel/reverse-engineering-skill/blob/d531c4fdfec68171f0b9f0da7a3db2710fcd9a6a/SKILL.md)；Current | 读取完整短入口；采用确定性计算交给工具、事实与推测分开、重要伪代码回看指令 | 明确拒绝其忽略授权的措辞、强制 MCP/全阶段与一律双工具要求；未读取全部链接参考；该快照声明 MIT |

Current 是本次可获取且主题仍适用的材料分类，不代表已实测该项目或所有命令。API 和能力仍以实际安装版本为准。许可声明只用于来源记录；复制源码/分发上游包前需另核对文件级许可，本轮未复制。

## 技术依据

- [Microsoft PE Format](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format)：区分 file pointer、RVA、VA 和节内布局；只读核验工具验证合成文件的换算与损坏输入，不宣称 Windows 加载器兼容验证。
- [JNI Functions](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/functions.html#global-and-local-references) 与 [JNI Design](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/design.html#referencing-java-objects)：引用的种类、配对与对象访问；具体 collector 故障不外推为 JVM 普遍错误。

下载文本指纹、精确读取范围见 [source-manifest.json](source-manifest.json)。范围说明是保守记录；下载完整文件不等于已完整审读。未把网页检索摘要作为实现验证。
