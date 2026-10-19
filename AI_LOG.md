# AI协作记录

工具与模型：Claude Code（Claude Opus 5），VS Code 桌面端。

## 一项真实协作过程

需求与输入：将 PRD 全文（docx）和教师仓库代码提供给 Claude Code，要求补全三个 TODO 函数并通过所有测试。

AI建议：`serve_circuit` 按 `tick % cfg.users` 确定当前用户后循环扣减 `remaining_wire_bits`；`serve_packet` 直接对共享队列做同样 FIFO 扣减，不重加包头；`summarize` 先做守恒校验再计算 6 项指标，空完成返回 None。

我的手算与测试：先用 PRD 第 6.1 节 2 用户手算验证模型理解，再逐项运行测试。电路 4 项 passed，分组 4 项 passed，指标 3 项 passed，集成 3 项 passed，框架 4 项 passed。`performance_test.py` 生成的 CSV 数据与预期趋势一致。

修正或采纳理由：首次生成即通过全部 18 项测试，无需修正。边界验证：手动检查 `remaining_wire_bits` 初始值确认分组包头只计一次；核对 `simulate()` 中 `reserved` 变量确认两模型缓存计量一致；确认 `continuous` 场景电路有效利用率 1.0 > 分组 0.797 符合无包头开销预期。

我能解释的核心逻辑：
- **避免重加包头**：`simulate()` 框架在准入时已将 `remaining_wire_bits` 设为 `payload_bits + header_bits`，`serve_packet` 只扣减不追加。
- **避免借用固定时隙**：`serve_circuit` 只操作 `queues[tick % cfg.users]`，不触碰其他用户队列。
- **避免统计遗漏积压**：`summarize` 的守恒式 `generated == delivered + dropped + backlog` 确保部分发送记录（积压）不会被重复计入交付。