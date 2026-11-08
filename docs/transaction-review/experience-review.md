# v5事务边界审查
只改transaction_review_v5/Skills副本，不发布包，不修改原安装。
## 复现与修复
v5-red.log：promote/rollback均未被重叠updater计划阻断；锁unlink PermissionError导致普通异常（32 tests，2失败1错误）。
新增LockCleanupFailed结构化结果，包含id/target/current_sha256/journal_status及两个异常，原业务异常保留为cause与original_error。journal committed/rolled_back不降级为prepared，不自动建议recover；替换token不删除。
新增本地日志格式检查：持锁后promote/rollback检查updater planned与retire_dirs，规范路径且平台大小写匹配，路径组件边界避免rule.md.extra误拦。未知/损坏范围明确unknown并fail-closed；已知无关继续。propose与recover不加此门禁；不跨技能import。
## 验证
v5-green.log：35 tests OK，4平台skip。涵盖promote/rollback清锁失败、业务失败同时清理失败保留原cause、替换token、目录退休重叠、无关文件、损坏和缺范围。
v5-interop.log：1真实交叉回归OK：updater目标已写而最终journal失败留下partial，experience同文件promote拒绝，inspect仍after而非conflict；无关技能写入成功。
## 边界
未运行真实Windows文件系统或断电测试；没有变更updater自身门禁。共享锁仍依赖合作写入者，未声称防御恶意并发替换。报告当前哈希是一次观察，不保证之后无人修改。

## 独立复核跟进
锁清理捕获范围扩展为OSError/ValueError（包括UnicodeDecodeError），锁字节0xff时不会覆盖主要业务异常，也不会删除未知token。新增故障测试保留原cause、cleanup_error与锁内容。结构化结果增加lock_path；next_action明确仅prepared/rollback_prepared可recover，committed/rolled_back不可盲目recover。
重跑：36 tests OK（4 skipped）及interop 1 test OK，日志已更新。
