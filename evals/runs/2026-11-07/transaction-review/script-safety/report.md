# v5 运行时 Python 静态安全复核

审查对象：`/workspace/scratch/54a565457947/transaction_review_v5/Skills`。仅只读正式树；复现使用临时目录，子进程超时主动杀死。

## 基线与范围

`baseline.json` 逐文件记录 SHA-256、行数和顶层函数。清单 SHA-256：`cadcdcb85c83e37d1e736bba421a11a2c4ed62cfcdaeed6ab3bf16101f2bfc47`。覆盖全部 15 个运行时/开发工具 Python 文件，3385 行；全树 37 个 Python，排除测试和历史 eval fixtures 22 个。扫描所有运行文件的入口、读写、执行、网络、循环、重试；逐项读文件并重点深审安全相关路径。不是逐分支执行覆盖。

## 新发现（已复现）

### S1：二进制探针/IDA 哈希接受非普通流，可永久阻塞

`skills/skillforge-reverse-engineering/scripts/probe_binary.py:104-109` 无输入类型检查直接打开并读到 EOF。稳定 FIFO 在 open 阻塞；`/dev/zero` 不会 EOF、持续占 CPU。两者真实子进程运行 0.5 秒后超时杀死。`ida_evidence.py:55-60 sha256_file` 有同一问题（独立 helper 的 /dev/zero 实跑同样超时），被 context 的磁盘源文件路径调用，可能占用 IDA 主线程。

这不是针对并发攻击的 TOCTOU，而是稳定输入即可触发。建议非阻塞打开后 fstat 验证 regular file，并将哈希读取限定初始长度，检查实际读取总量及前后 stat，拒绝特殊文件。大文件本身可流式处理，不必任意限制正常 DLL 大小。POSIX O_NONBLOCK 与 Windows 需分别说明。

### S2：独立 Archerage 验证器对 eval FIFO 二次读取绕开前序拒绝

`skills/skillforge-archerage-addon/scripts/verify_skill.py:83-85` 可记录非普通 `.json` 错误，但 `:102` 再次不受保护地 `read_text` eval 文件。复制完整 skill 到临时目录，把 `evals/behavior-cases.json` 换为 FIFO，无并发修改，真实 CLI 运行 0.5 秒后超时杀死。与总 `validate_skills.py` 已披露的并发 TOCTOU **不是同一个缺陷**。

建议一个统一 bounded regular-file reader，主入口 SKILL 和 eval 重读都调用它；发现结构边界错误不继续解析。顺带确保二次 eval 读取不能绕过 2 MiB 限制。

### S3：verified report 输出失败留下最终名称半成品

`skills/skillforge-archerage-addon/scripts/verify_report.py:166-169` 直接 `open('xb')` 最终输出。对 write 注入先真实写入 `abc` 再磁盘满异常，CLI 返回 1/rejected，但最终 `verified.txt` 存在且仅 3 字节；下一次同路径因排他创建不能重试。没有误报 exit 0，但文件名本身未区分半成品。

建议沿用 IDA 导出 `.partial`、flush/fsync/close 后无覆盖发布，返回明确 `published` / cleanup 状态。此复现 decode_pages 使用已验证结果替身，仅测试真实输出失败路径，不宣称重新验证 wire parser。

## 实际入口与副作用清单

| 文件 | 入口 | 副作用/边界 |
|---|---|---|
| scripts/apply_skillforge_update.py | main；apply_update | 默认 check/read；--apply 写备份、共享锁、日志、替换/删除清单目标、移除指定空目录；不自动重试，残留要求人工协调 |
| scripts/validate_skills.py | main；validate_packages | 只读扫描；self-contained 临时复制并清理；不执行包内 Python |
| development/.../build_skill_index.py | main；build_index/write_atomic | 默认 stdout/check 只读；显式 output 同目录 temp/fsync/replace；拒绝链接；非 OS 沙箱 |
| archerage/audit_patch.py | main；audit_patch | 只读两个目录和 ZIP，不解压、不执行；文件16MiB/总256MiB/条目20000预算 |
| archerage/check_lua51.py | main；check_lua | 唯一子进程调用：argv 数组、shell=False 默认、每次5秒；调用用户选定可信解释器；临时暂存源码/驱动后清理；不执行目标 chunk；128MiB源码总量 |
| archerage/verify_report.py | main；decode_pages/parse_hud | 默认只读；--output 排他写；S3 |
| archerage/verify_skill.py | main；validate | 只读结构/AST/JSON，不执行脚本；S2 |
| experience/experience_store.py | main；propose/promote/rollback/recover | propose 写候选；其余显式锁/日志；promote/rollback 可替换/删除规则；recover 只改日志；无自动重放 |
| ida/gui_strings_export.py | start/cancel/status | IDA timer，每批数量/时间预算；写 partial 后无覆盖发布；cancel 下次 tick 生效；不保存 IDB |
| ida/ida_evidence.py | report/export/on_main_thread 等库函数 | 查询通常只读；wait_for_analysis 明确处理分析队列可修改 IDB；export 写磁盘；主线程执行桥；sha256 S1 |
| ida/ida_mutations.py | run_plan | 默认 dry-run；commit 至多100操作，修改名称/类型/结构，排他审计日志；验证独立备份；不自动保存 IDB/回滚/重试 |
| ida/mcp_function_query.py | main；Client | 唯一网络出口：loopback HTTP POST；禁 proxy/redirect/远端 DNS；默认 initialize/list；显式经审查白名单 query；8MiB响应、30秒 socket timeout，不重试 |
| ida/run_ida_batch.py | __main__；run | JSON config，不 eval；可显式 auto_wait；report+磁盘导出；不 qexit/save；sys.path 添加脚本路径 |
| lgf/inspect_workspace.py | main；collect_manifest | 只读项目/引擎描述和文件清点；允许文件链接且披露真实来源；无进程/网络 |
| reverse/probe_binary.py | main；inspect_file | 只读原始文件，不装载或运行二进制；S1 |

## 未提升为新缺陷的边界

- updater/experience 的 shared lock、atomic replacement、审计故障恢复问题已有专门事务审查，本轮未重复报告。
- 全库没有 `shell=True`、`os.system` 或动态执行外部 Python 的运行入口；MCP 不启动服务。
- MCP socket timeout 不是整个响应的绝对截止时间，有限 SSE 示例并非完整流客户端；没有用恶意慢流占满 30 秒来复现。
- LGF JSON read_text 和树 glob、validator/indexer 条目数量、update manifest/文件读取没有全局硬预算；面向受信任冻结工作区，不能声称支持任意恶意超大输入。本轮未制造内存耗尽。
- 目录祖先 symlink/并发替换的 OS 级隔离不在大多数工具契约中；此轮未复报总 validator 已知 TOCTOU。
- 各 CLI stdout 可在操作完成后失效，不能把 nonzero 等同无副作用；必须核对日志和文件，现有事务模块有独立持久证据。

## 验证限制

没有真实 IDA/Hex-Rays/MCP 服务/Windows reparse point/游戏运行环境测试；未测试掉电、恶意内核、NFS 原子性；不将静态检查当运行通过。复现见 `reproduce.py`；无正式树写入。
