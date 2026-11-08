# 官方资料索引

核实日期：2026-11-07。以下为本轮检索或打开的原始资料；“官方/标准”表示来源权威，不保证对所有版本适用。代码仍须在目标安装版本运行验证。本文原创概括，不打包第三方文档正文。

| 名称 | 来源与 URL | 版本/可信程度 | 主要用途 |
|---|---|---|---|
| IDAPython 9.0 API | Hex-Rays 官方 https://python.docs.hex-rays.com/9.0/index.html | 9.0，高 | 模块与签名核对 |
| IDAPython 8.x→9.0 migration | Hex-Rays 官方 https://docs.hex-rays.com/9.0/developer-guide/idapython/idapython-porting-guide-ida-9 | 8.x/9.0，高 | ida_struct/ida_enum 移除与 ida_typeinf 迁移，不跨版本直接 import |
| IDAPython README | 官方仓库 https://github.com/HexRaysSA/IDAPython/blob/9.0/README.md | 9.0 分支，高 | 启动时序、脚本运行环境 |
| Hex-Rays interactive | 官方 https://docs.hex-rays.com/8.5/user-guide/decompiler/interactive | 8.5 文档，高 | 伪代码窗口与刷新限制，非新版本统一承诺 |
| PE/COFF | Microsoft https://learn.microsoft.com/en-us/windows/win32/debug/pe-format | 在线版本，高 | 头、节、导入导出、RVA 映射 |
| Windows x64 calling convention | Microsoft https://learn.microsoft.com/en-us/cpp/build/x64-calling-convention?view=msvc-170 | MSVC x64，高 | 参数、栈、寄存器；不用于 SysV x64 |
| Arm64EC ABI | Microsoft https://learn.microsoft.com/en-us/windows/arm/arm64ec-abi | Arm64EC，高 | 混合 ABI 和 thunk |
| ELF specification | Xinuos/gABI https://gabi.xinuos.com/elf/00-foreword.html | 页面标注 4.3 DRAFT，高但需注意草案 | 格式与 gABI/psABI 分工 |
| Itanium C++ ABI | ABI 项目 https://itanium-cxx-abi.github.io/cxx-abi/abi.html | 在线修订，高 | 类布局、RTTI、虚表；平台供应商 ABI 优先 |
| Arm ABI | Arm 官方仓库 https://github.com/ARM-software/abi-aa | 必须固定目标 release，高 | AAPCS32/64、AAELF，不能当 MS ABI |

下一层按目标补查：IDA SDK 同版本头文件、ida_dbg 后端文档、Intel/AMD 指令手册与 Arm 架构手册、Epic 对应 UE 分支源码。没有取得目标源码或相应版本文档时，把该项标记为未核实，不把搜索摘要升格为运行验证。

## 补充知识入口
同一核实日期 2026-11-07。以下按核实层级列出，未读全文的条目不作为具体规则证据。
| 名称 | 来源/原始 URL | 版本与核实层级 | 主要内容/可信程度 |
|---|---|---|---|
| IDA/SDK | Hex-Rays https://docs.hex-rays.com/ | 目标安装版本；SDK 具体头文件待目标环境核实 | loader/processor/插件；官方入口高可信，未验证本机 SDK |
| Hex-Rays Decompiler | https://docs.hex-rays.com/core/decompiler | 当前索引已打开 | 反编译入口与架构授权，官方高 |
| Intel SDM | https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html | 索引已打开，页面列 v093；未通读手册 | x86/x64 指令与机器行为，官方高 |
| ARM A64 | https://developer.arm.com/documentation/ddi0602/latest | 页面无可读正文，未核实具体修订 | ARM64 指令候选入口，具体规则待核 |
| MCP 生命周期 | https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle | 2025-03-26 全文已读 | 初始化与版本协商，官方高 |
| MCP 传输 | https://modelcontextprotocol.io/specification/2025-03-26/basic/transports | 固定协议参考；部署时核对 | Streamable HTTP 边界，官方规范 |

[适配器及固定提交](mcp-adapters.md)；[UE 官方资料与版本限制](unreal-engine.md)；[API 分类及例程](idapython-api.md)。GitHub 调研全文随完整库位于 docs/ida-pro；独立复制本技能不依赖该目录。文档/工具索引不构成 API 兼容或执行通过证明。
