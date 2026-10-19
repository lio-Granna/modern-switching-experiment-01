"""任务3：补全指标统计。"""
def summarize(raw, cfg):
    """返回字典，键名必须保留：
    payload_utilization=delivered_payload_bits/(cfg.ticks*cfg.slot_bits)
    wire_utilization=wire_sent_bits/(cfg.ticks*cfg.slot_bits)
    mean_delay_ms、max_delay_ms：完成记录的delay_ticks乘cfg.tick_ms；
      无完成记录时两者返回None，不能写0掩盖无送达。
    loss_ratio=dropped_payload_bits/generated_payload_bits；无生成数据时为0。
    backlog_payload_bits：所有未完成记录的原始payload总和，直接取raw对应值。
    只用观察窗口[0,ticks)，不追加排空时间；有效载荷按完整交付记录计数。
    raw['completed']元素含payload_bits、delay_ticks、user。
    要检查generated=delivered+dropped+backlog，不相等抛ValueError。
    """
    g = raw['generated_payload_bits']
    d = raw['delivered_payload_bits']
    r = raw['dropped_payload_bits']
    b = raw['backlog_payload_bits']
    w = raw['wire_sent_bits']

    if g != d + r + b:
        raise ValueError(
            f'conservation violated: generated={g} != delivered={d} + '
            f'dropped={r} + backlog={b} = {d + r + b}'
        )

    denom = cfg.ticks * cfg.slot_bits

    completed = raw['completed']
    if completed:
        delays = [rec['delay_ticks'] for rec in completed]
        mean_delay_ms = sum(delays) / len(delays) * cfg.tick_ms
        max_delay_ms = max(delays) * cfg.tick_ms
    else:
        mean_delay_ms = None
        max_delay_ms = None

    loss_ratio = r / g if g != 0 else 0.0

    return dict(
        payload_utilization=d / denom,
        wire_utilization=w / denom,
        mean_delay_ms=mean_delay_ms,
        max_delay_ms=max_delay_ms,
        loss_ratio=loss_ratio,
        backlog_payload_bits=b,
    )
