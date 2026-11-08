# 独立审查处理记录
2026-11-07；只读审查，没有真实IDA。
1. 发现context只hash磁盘文件，旧IDB/替换输入可能匹配错误目标。已加入IDB存储SHA-256、IDB路径和image_base，commit比较审核计划；缺失/不符拒绝。新增离线拒绝场景。
2. GUI字符串iterator创建失败可能留下已打开文件。已将iterator提前，首条写入失败显式close。
3. report每页重复hash大文件。增加显式任务context_snapshot；文档要求期间冻结数据库、结束重新核身份；修改操作仍现读身份。
4. 集成过程发现函数/结构体写入缺读回，已用ida_nalt.get_tinfo、get_named_type和equals_to核对。
5. 提交阶段复查失败需纳入部分成功日志；采用来源作者修复并保留本轮读回，真实状态fake测试覆盖前项成功后旧值变化。
审查的AST/链接检查与本轮实际回归均不构成IDA兼容保证。没有独立模型行为A/B实验。
