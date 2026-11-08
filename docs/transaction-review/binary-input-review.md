# v5 binary probe输入边界

仅改probe_binary.py、根test_reverse_binary_probe.py、本技能tools-and-validation.md及本报告；未改Addon。

FIFO无writer与/dev/zero真实子进程fixture修复前均2秒超时RED，subprocess.run自动终止并等待子进程。修复后在open前stat拒绝特殊文件，使用只读+可用O_NONBLOCK+Windows二进制标志打开，再fstat验证实际描述符是常规文件；异常关闭拥有的fd。未承诺阻止任意并发替换、所有平台非阻塞打开或网络文件系统延迟。

哈希按初始大小有限读取，短读拒绝，额外一字节检测增长，并保持末尾size/mtime核验。无任意文件大小上限；不是内容原子快照，不抵御恶意恢复mtime。合法普通文件CLI及大写SHA-256合同不变。

最终20测试通过，包括真实FIFO/设备拒绝（超时保护）、合法CLI哈希、实际打开的设备fd复查与关闭、读取期间增长拒绝及原PE测试。Windows设备/命名管道未实测；平台不具备fixture能力时测试明确skip。

## IDA sha256_file补记

同一特殊文件缺陷在ida_evidence.sha256_file中独立修复，未跨技能import。合法常规文件/指向常规文件的symlink允许，保留小写SHA-256；前置stat、可用O_NONBLOCK打开、fd类型复查/异常关闭、初始大小预算和末尾size/mtime核验。错误使用OSError，保留context.hash_error处理与备份提交失败关闭合同。

真实FIFO及/dev/zero在2秒保护下RED；修复后GREEN。6MiB多块常规文件与合法相对symlink哈希一致；注入读取增长及打开后设备描述符复查/关闭通过。整合时IDA离线套件66项通过（包括其他并行修订已有用例），未执行真实IDA；无Windows实测或任意并发替换安全保证。未发布交付包。
