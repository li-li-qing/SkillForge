# 最新 4 文件独立复验

结果：40 项独立检查全部通过；正式树未修改。29 项主矩阵、4 项额外输出事实、7 项定向竞态/增长缩短测试。原有 3 类缺陷在对应修订位置均未复现。注意旧 `reproduce.py` 写故障 hook 绑定旧最终路径，不适用于新 `.partial` 实现；本次已将注入目标准确移到 partial，不能用旧 hook 没触发当通过。

## 实测范围

- probe/hash/独立 verifier reader：稳定 FIFO、/dev/zero、指向 FIFO 的软链接全部快速拒绝。
- probe/hash：普通文件正常，指向普通文件的软链接可读，哈希一致。verifier 按原规则拒绝文件软链接。
- verifier 正常整个包 CLI exit 0；复制包 eval JSON 换 FIFO 后 exit 1，不再阻塞；2 MiB+1 文件拒绝。
- 定向 stat 后、open 前换 FIFO：3 个读取入口都拒绝、不阻塞（Linux）。probe/hash 初始长度采集后增长/缩短均拒绝。
- 输出正常写入、移除 partial；已有普通文件/软链接/悬空软链接/FIFO 不覆盖。
- write 半写后抛错、短写、flush、fsync、close、link 故障：最终路径不存在，保留 partial。
- unlink 清理失败：最终完整文件存在，published=true，cleanup_error 非空，partial 残留。
- 发布前竞争者创建最终目标：保留竞争者内容，候选保留 partial，不覆盖。
- 既存 partial 软链接：拒绝，不改目标。
- 真实构造 RS-ERROR-PAGE-1 wire，经 CLI 完整解析后发布 hello，exit 0、published=true。
- 发布成功后 stdout 故障：exit 1，stderr status=published_diagnostic_error，最终文件仍完整，未把已发生发布称 rejected。

## 当前四文件 SHA-256

- probe_binary.py: `ffa10b049e608a9907a17f3560a1abb3b7a7fe5c4c9d04959afa720c7c50c349`
- ida_evidence.py: `31fdcadb994518e20fbe2797af24f93646aad93cf95da4bf4d37af62a0681f68`
- verify_skill.py: `8a3cc11f25c389c26286d1d344ee2f162779e5edf6e66b3a29eec4ac62cbce15`
- verify_report.py: `f5715dae80f413e5551ecc0451bd61440a4433282a6c0d5e6915ed4338e38fa2`

## 残余风险和明确限制

- 无真实 IDA、Windows 特殊文件/junction 或网络文件系统执行；不能把 Linux O_NONBLOCK 结果推广为所有主机。
- size+mtime 检查不是原子快照，恶意同长度并恢复 mtime 的并发改写仍可能生成混合证据；应使用冻结工作副本。正常大文件 hash 仍可耗时，无任意大小硬上限。
- partial 发布要求同目录硬链接支持；不支持时保留 partial 并报错，无隐式覆盖 fallback。没有 directory fsync 的掉电持久性保证。
- 父目录并发替换、partial 被非合作写者替换不属于此次安全边界；依赖用户控制的稳定输出目录。
- 失败 partial 下次同名运行会拒绝，而不是自动删掉重试，需显式核对后处理。这是保留证据策略，不是恢复失败。
- 异常 I/O 检查采用 mock 故障注入，但读取/输出与文件存在事实由真实临时文件核实；未制造真实磁盘满/掉电。

证据：reverify.py / reverify-results.json、reverify_extra.py / reverify-extra-results.txt、reverify_races.py / reverify-race-results.txt。
