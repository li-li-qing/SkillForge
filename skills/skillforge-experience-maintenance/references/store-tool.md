# 可选本地记录工具

工具：[experience_store.py](../scripts/experience_store.py)，Python 3.10+，仅标准库。

## 使用前

确认共享根是用户指定的真实SkillForge目录；所有规则写入者遵守同一协议；文件系统支持本地独占创建和单文件原子替换。本轮只在隔离的本地Linux环境运行测试，Windows、网络盘、同步盘、多机和断电耐久性未验证。

工具只接受 skills/<技能名> 下的SKILL.md、README.md、VERSION、references/或assets/中的Markdown；拒绝越界、脚本/配置和符号链接。内容必须UTF-8，候选正文不超过1MiB。

工具目录读取与命令执行是两回事。没有命令权限就仅给候选文本，不用直接覆盖替代协议。

## 记录与晋升

从本技能的 references 目录调用；共享根、example技能名、目标文档与候选文件由实际环境填写，不照抄示例路径：

```text
python ../scripts/experience_store.py --root <共享根> propose --target skills/example/references/rule.md --content <候选正文文件> --actor <本次执行者标识> --kind technical --evidence <可定位证据> --conditions <适用条件>
python ../scripts/experience_store.py --root <共享根> promote <返回的ID> --reviewed
```

`propose` 读取当前规则并保存独立候选；没有修改正式规则。个人偏好使用kind=preference，技术经验使用technical。`--reviewed` 表示调用者已完成证据/语义/授权审查，不是工具自动审查，也不是权限凭证。

`promote` 在共享根的独占锁内重读哈希；基线不同就拒绝，须重新阅读和语义合并成新候选。锁忙立即拒绝，不等待、不抢锁；原候选保留，可继续独立任务。重复已完成ID只报告历史已提交及当前是否仍匹配，不把后来内容覆盖回去。

## 事务记录

共享根下 `.skillforge-memory/proposals/` 保存独立候选，`transactions/` 保存前后内容/哈希、来源与状态，`write.lock` 是协作写锁。
先写prepared记录，再原子替换规则，再写committed记录。这不是多文件原子事务；命令中断可能留prepared和锁，不能据此宣称已完成。候选/事务含原文，写入前必须脱敏；禁止复制凭据或无关私人信息。

## 撤回和恢复

```text
python ../scripts/experience_store.py --root <共享根> rollback <ID> --reviewed
python ../scripts/experience_store.py --root <共享根> recover <ID>
```

撤回只在当前内容仍等于该事务写入值时进行；后来已改动则拒绝，需审查新的反向补丁。新增文件的撤回会删除该文件，需当前明确的撤回授权。recover只根据前后哈希修正事务状态，不修改正式规则；既不匹配则拒绝猜测。

崩溃锁不自动过期。先确认没有存活写入者并获得恢复许可，再人工处理遗留锁并执行recover；不能仅凭时间或陌生PID删除锁。

退出码0表示指定机械操作完成，2表示拒绝/错误。它不证明技术结论真实、所有引用正确、实际Agent行为通过，或任意非协作程序无法改文件。正式更新后仍要做范围相应的结构/引用/行为检查。
