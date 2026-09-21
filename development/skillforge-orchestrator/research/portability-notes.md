# Portability notes

运行时核心只基于能力契约，不按 Agent 品牌分支。不同宿主可能在以下方面不同：技能发现方式、显式调用语法、frontmatter 扩展字段、技能作用域、上下文压缩、权限门禁、附件/文件交付。

这些差异应在安装/打包层解决，并映射成 runtime 的 capability snapshot。任何具体宿主资料都属于可替换研究证据，不进入核心逻辑。
