# 来源与适用范围

核对日期：2026-11-08。本技能独立整理，未打包 Cheat Engine、MCP 插件、游戏文件或上游代码；不默认安装它们。

## 当前核对

- [CheatEngineNet/CheatEngine.Mcp README](https://github.com/CheatEngineNet/CheatEngine.Mcp/blob/bcce6ca79cb578123ea32a8c419348a9067ce8ed/README.md)：固定提交 `bcce6ca79cb578123ea32a8c419348a9067ce8ed`，Current；读取行 1–175。采用实例发现、显式路由、目标与宿主 PID 区分、源码与发行能力分开。下载 SHA-256 `A706F50DAA17631A602B97DABD891D37ED7CCAED7C57D7726B25A20252293270`。未据此宣称当前发行具有源码中全部工具；该仓库声明 MIT。
- 本会话实际安装并运行过的包：CE 7.7.0.10621、CheatEngine.Mcp 2.0.0-beta.4。现场 collector/包装源码有版本相关问题，不能把其它分支或 README 当该包的准确实现。入口、命令、释放分支及验证摘要的本机切片在本轮重新读取；指纹和条件见 [已核实案例](minecraft-case.md)。Classification：本机版本观察，不是上游通用缺陷声明。
- [JNI 21 引用规范](https://docs.oracle.com/en/java/javase/21/docs/specs/jni/functions.html#global-and-local-references)：用于判断 local/global 引用配对；不提供任意 HotSpot 堆布局或通用对象指针解码保证。

## 社区取材裁剪

同时审读三个逆向技能入口：[ghidra-rpc](https://github.com/cellebrite-labs/ghidra-rpc/blob/fa3866243dcfcbc876baa7b13ae0deac2c443cd8/SKILL.md)、[reverse-engineerskill](https://github.com/juank115/reverse-engineerskill/blob/02a29545cc16599b5f181f082a9d96dbce82791f/skills/reverse-engineering/SKILL.md)、[PyModel](https://github.com/PyModel/reverse-engineering-skill/blob/d531c4fdfec68171f0b9f0da7a3db2710fcd9a6a/SKILL.md)。这里只采用事实/推测区分、范围明确的工具查询与按问题选深度；CE 特有结论来自现场，不冒称这些社区技能验证过本次 JVM 错误。

不采用忽略授权、默认上传文件、强制远程平台、批量安装整套工具或将所有样本当恶意代码的做法。没有发现可直接替代本次 CE/JNI 现场经验的已验证社区包，不为凑数量添加同义技能。

## 验证层级

本轮结构校验、触发题和行为冒烟单独记录；历史游戏/fixture 结果仅保留已有证据。没有本轮真实进程操作，就不报告已重新修改游戏。技能新增不自动使其他 Agent 宿主发现它，也不修改已有 MCP 权限配置。
