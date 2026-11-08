# 随包工具：执行方法与结论边界

四个工具仅用Python 3.10+标准库，无联网、依赖安装、游戏写入或自动执行Lua载荷。以下命令的工作目录为本文件所在 references 目录；路径包含空格时加引号。所有命令应先`--help`，不要把示例路径原样当真实文件。

## 1. 技能结构检查

```text
python ../scripts/verify_skill.py ..
python -m unittest discover -s ../tests -v
```

检查名称/修订、此包采用的简化YAML、Markdown本地链接、JSON、重复案例ID、必需脚本、新增评测题的未执行标志。它不是通用YAML验证器，不联系网络验证旧来源，不用关键词命中判断Agent正确率。

测试使用临时目录与合成报告，包含失败输入；游戏对象、PVP、Store逻辑没有被这组Python测试执行。涉及真实Lua5.1的两例需要环境变量`RS_TEST_LUA51`指向可信解释器；未提供显示skipped，不能算通过。将该环境变量设置为本机可信解释器实际路径，不把示例路径当作可用安装。

## 2. 分页/HUD接收

```text
python ../scripts/verify_report.py pages.txt
python ../scripts/verify_report.py pages.txt --hud --output verified-layout.txt
```

仅支持当前已核对的`RS-ERROR-PAGE-1`及可选`HUD_TEMPLATE_V2`，其他协议明确拒绝，不猜解码。读取实际声明字节数，检查逐页、全传输、解转义原文；中文、反斜杠与嵌入尾标不会被误拆。顺序可调整，完全相同重复页统计去重；缺页、混ID、冲突、错误偏移与校验拒绝。

当前wire内源换行已编码为`\n/\r`，接收器可去掉复制新增的真实CR/LF；空格和tab在DATA中保持原样，不做“修复丢字”。这是协议特例，不应用于任意文本。资源预算是接收器保护，不是推断RU编辑框的真实上限。

默认stdout只输出校验元信息，不输出报告正文。`--hud`会额外输出布局字段；`--output`仅创建新文件，已存在则拒绝。报告可能含隐私，保持本地、按最小范围分享；工具不执行报告中的代码、不恢复存档、不修改默认值。解析数值不代替当前Store的上下限和语义验证。

## 3. 真Lua5.1语法门禁

```text
python ../scripts/check_lua51.py --lua <trusted-lua51> <changed.lua>
python ../scripts/check_lua51.py --lua <trusted-lua51> <addon-directory>
```

使用可信解释器实际打印`_VERSION`，必须精确为`Lua 5.1`，检测到`jit`变体时阻断而不是冒充标准解释器。记录解释器/源文件摘要；清理LUA_*启动环境；拒绝字节码；编译哈希对应的临时文本副本，调用loadfile但**不调用编译结果**。目录参数递归仅收`.lua`，符号链接拒绝。

退出码0=语法通过，1=语法失败，2=blocked/未完成；空文件集合不是通过。缺解释器、错误版本、超时或读取失败均不降级为5.4成功。无自动下载/安装；可继续其他定位，但不能报告Lua5.1已通过。

语法器抓不住`table.unpack`在5.1标准库不存在、事件参数错位、Native返回单位等运行契约；LuaJIT/定制VM也须单独标注。版本字符串检查不是恶意解释器认证，二进制来源由调用者负责。依据：[Lua5.1手册](https://www.lua.org/manual/5.1/manual.html)。

## 4. 最终增量ZIP核对

```text
python ../scripts/audit_patch.py --base <baseline> --current <current> --zip <patch.zip>
```

base/current是**同一项目相对层级**的两个既有目录，ZIP也必须包含同层级路径；例如两者都含`replicatedsuite/`，不要一边选Addon根、一边选插件根。只有确有删除且获准时重复添加 `--allow-deletion relative/path`，批准列表必须等于实际删除集合。

拒绝多打未修改文件、少打变化文件、错误载荷、重复/大小写冲突、穿越/Windows危险路径、符号链接、文件目录碰撞、加密、超预算、常见私密文件与缓存。对最终ZIP内容核对摘要并验证覆盖后的文件映射一致，输出新增/修改/删除及未改数量。

不解压、不删除、不运行测试、不校验任意内容是否含密钥；文件名筛查后仍需人工内容审阅。不会修TOC，TOC加载顺序/重复依赖应使用已存在的项目检查。还需在干净目录实际应用最终ZIP再跑相关回归，映射相同不等于已经执行。

## 技能包更新与游戏补丁不同

用户本轮更新的是技能，完整包放回原来的技能目录，不覆盖Addon；可选增量仅覆盖同修订基线的技能。元信息与安装方式遵守[Agent Skills格式](https://agentskills.io/specification)，具体发现/启用由宿主决定，不承诺复制文件就跨所有工具热重载。

Lua 语法门禁同时限制单文件 4 MiB、2000 个文件和源码总计 128 MiB；超过总预算返回 blocked，不启动源码解析。总预算约束暂存源码，不能视为解释器进程总内存上限。

## 文件门禁与输出发布边界（2026-11-07）

`verify_skill.py` 对入口、遍历文本和评测JSON均通过同一读取门禁：拒绝符号链接/非常规文件，最大2MiB；打开后再次fstat并限量读取。POSIX可用时使用O_NOFOLLOW/O_NONBLOCK，防止静态FIFO及最终路径被换成FIFO时阻塞。它不是敌对文件系统沙箱：父目录替换、读期间普通文件内容变化、不同平台缺少标志的竞态仍需可信、稳定的包副本；不能由结构通过证明扫描时全包原子一致。

`verify_report.py --output path` 先独占创建同目录`path.partial`，写入长度、flush、fsync和close全部成功后以硬链接无覆盖发布path。写入/关闭/发布失败保留partial，exit=1且正式文件不由本工具发布；发布竞争者的已有文件不覆盖。已有partial也拒绝，不能自动删除或覆盖，应人工核对来源后另选输出名或处理残留。

正常stdout仍为验证元数据，不打印raw；指定output后除原output字段外增加output_state：published、path、partial_path、cleanup_error。发布后partial清理失败仍exit=0，cleanup_error记录残留，不用warnings发出可能变异常的通知。main内捕获到stdout在发布后失效时返回1，并尽力向stderr输出status=published_diagnostic_error、output_state（含published/path）与error；stderr也失效时有限捕获后仍返回1，不回写或重试文件，也不把完整文件称rejected。Python解释器退出时还可能刷新stdout并产生非零进程退出码，本工具不替换全局stdout；这也不表示文件未发布。此时无法保证调用者收到JSON，须直接核对正式文件，不能盲目重试同路径。未指定output的原验证/退出语义不变。

硬链接发布要求文件系统支持；不支持则失败关闭。文件fsync不等于目录项已耐断电，未做目录fsync；不承诺Windows/网络文件系统或恶意并发改目录下的行为。partial和正式路径由调用者控制并位于可信目录；清理只针对本次创建的partial名称，但目录中敌对替换不在安全保证内。测试为本地临时目录故障注入，不是游戏/实机验收。
