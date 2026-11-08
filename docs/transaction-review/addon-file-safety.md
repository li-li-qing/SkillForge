# Addon文件安全修复

2026-11-07，仅v5副本，未发布。原复现见/workspace/shared/script_safety_v5/reproduce.py。

verify_skill曾在通用扫描拒绝FIFO后，评测schema阶段直接read_text同一路径并阻塞。现在入口、通用扫描、评测读取统一走read_regular_text，lstat先拒绝、os.open使用可用NONBLOCK/NOFOLLOW、fstat核对、2MiB+1有界读取。并非完整TOCTOU或敌对目录沙箱，见verification-tools。

verify_report原--output直接xb正式文件，写失败使半文件占用正式名。现在独占partial、校验短写、flush/fsync/close后硬链接无覆盖发布；不支持硬链接失败关闭。发布后cleanup状态结构化，不以warnings或输出错误掩盖发布。stdout原verified_copy元数据与退出码约定保留；--output新增output_state。输出通道失败后不能保证JSON到达，main诊断流失败返回1并尽力stderr报告published_diagnostic_error及output_state/path/error；stderr也失效仍返回1，不重试、不称rejected；解释器退出flush仍可能改变非零退出码，不据此断言未发布，需直接核验正式文件。

RED新增测试首次6项12 errors，含FIFO子进程两秒超时杀止及旧接口缺失。故障覆盖：写异常/短写、flush、fsync、close、发布失败、正式文件/partial已存在、发布竞争、发布后cleanup失败且warnings=error、CLI元数据不含raw、发布后stdout断开。无未知脚本、Lua/游戏执行；所有夹具由测试生成。最终结果由下文追加。

最终：48 tests in 0.525s，OK (skipped=2)，即46通过、2真实Lua未配置而跳过。脚本未加载Lua载荷；包结构测试包含本次新增文档/测试的语法与本地引用检查。

诊断契约修订：拒绝空stdout+exit0的静默成功。RED：文件安全9项中3个子场景失败；补stdout断开与同时stderr断开回归。清理失败本身仍为已发布成功，只有诊断流失败返回1；正式文件不回写或重复发布。

修订后完整验证：49 tests in 0.612s，OK (skipped=2)，即47通过、2真实Lua跳过。
