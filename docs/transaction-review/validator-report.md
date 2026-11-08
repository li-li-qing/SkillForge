# v5 Validator目录链接与特殊文件边界

真实临时fixture：references/linked是指向包内docs的相对目录symlink；SKILL链接linked/hidden.md，其内部链接missing.md。修复前--self-contained报告0错误，因为rglob未遍历链接子树。该RED不表示正式库已有断链。

最小策略：包内目录symlink及目录reparse point明确拒绝，不尝试扩展递归跟随。相对包内常规文件symlink继续支持，原树及独立副本均需符合边界。自循环/逃逸仍由现有解析检查拒绝。

另以本地mkfifo生成references/blocked.md，修复前读取阻塞，测试2秒超时终止进程并RED；不是无限读取，也不声称ZIP含FIFO。现在在读取/复制前stat检查，仅允许目录和常规文件（含符合边界的文件链接），拒绝FIFO/socket/device；链接到特殊文件同样拒绝。检查不提供对抗非协作并发替换的安全沙箱保证。

新增真实fixture三项：目录链接隐藏Markdown拒绝、包内相对文件链接兼容、FIFO拒绝。最终validator38项测试全部通过；14技能及14独立副本检查0错误。当前Linux实测，Windows目录reparse point检查按属性静态实现，未声称Windows运行认证。

只改scripts/validate_skills.py、tests/test_validate_skills.py及本报告，未改动态路由。


## 并发替换边界

独立注入复验表明，在类型预检后、read_text前把常规文件换成FIFO仍可能阻塞。稳定树上的拒绝通过不等于动态替换防御。当前工具用于可信、稳定输入：验收期间暂停相关协作写入或选择固定版本，不要求日常编辑反复复制备份。输入由不可信并发写入者控制时，不应直接用此工具作为安全隔离。

评估过局部fd非阻塞读取：POSIX非阻塞打开加fstat能缩小部分FIFO窗口，但不能单独覆盖目录遍历、JSON读取、复制阶段与Windows语义；只改一处会产生过强保证。本轮选择明确支持边界，不新增未经跨平台验证的安全层，不声称防止恶意并发替换。
