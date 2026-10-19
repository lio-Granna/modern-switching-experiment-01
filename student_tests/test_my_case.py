"""自拟反例：验证分组交换不会重复添加包头。

若 serve_packet 实现在每次 tick 发送时错误地重新加 header_bits，
会导致 wire_bits 膨胀超出 slot_bits 预算，记录也不会正确完成。

本测试使用 2 用户、1 tick、1 条 96 bit payload 记录：
- 框架已初始化 remaining_wire_bits = 96 + 32 = 128
- 正确实现：单 tick 发送 128 bit 并完成
- 错误实现：发送量超过 128（重复加头），或记录未完成
"""
from collections import deque
from src.models import Config, Pending
from src.part1_circuit import serve_circuit
from src.part2_packet import serve_packet
from src.metrics import summarize


def test_packet_no_double_header():
    """分组包头只计一次：96 payload + 32 header = 128 wire，一 tick 完成。"""
    cfg = Config(users=2, ticks=10, slot_bits=128, header_bits=32,
                 buffer_payload_bits=4096)
    # 模拟框架：remaining_wire_bits 已含包头
    rec = Pending(user=0, arrival_tick=0, payload_bits=96,
                  remaining_wire_bits=96 + 32)
    q = deque([rec])

    wire, done = serve_packet(q, tick=0, cfg=cfg)

    # 断言 1：发送量不超过 slot_bits（重复加头会超过 128）
    assert wire == 128, f'expected 128 wire bits, got {wire}'

    # 断言 2：记录完成且队列清空
    assert len(done) == 1, f'expected 1 completed, got {len(done)}'
    assert done[0].payload_bits == 96
    assert done[0].remaining_wire_bits == 0
    assert len(q) == 0


def test_circuit_no_slot_borrowing():
    """电路交换空时隙不能被其他用户借用。"""
    cfg = Config(users=2, ticks=10, slot_bits=128)
    # 用户 1 有数据，但 tick 0 服务用户 0（空队列）
    q0 = deque()
    q1 = deque([Pending(user=1, arrival_tick=0, payload_bits=64,
                        remaining_wire_bits=64)])
    queues = [q0, q1]

    wire, done = serve_circuit(queues, tick=0, cfg=cfg)

    # 断言：tick 0 属于用户 0，用户 1 的数据不能发送
    assert wire == 0, f'expected 0 wire bits (idle slot), got {wire}'
    assert len(done) == 0, f'expected 0 completed, got {len(done)}'
    assert len(q1) == 1, 'user 1 record should still be waiting'


def test_metrics_none_when_no_completion():
    """无完成记录时平均和最大时延为 None，不为 0。"""
    from src.utils import simulate
    from src.models import Arrival

    cfg = Config(ticks=1, slot_bits=128)
    # 一条 200 bit 记录，wire=232（含包头），窗口仅 1 tick，发不完
    raw = simulate([Arrival(0, 0, 200)], cfg, 'packet')
    m = summarize(raw, cfg)

    assert m['mean_delay_ms'] is None, \
        f'expected None mean_delay, got {m["mean_delay_ms"]}'
    assert m['max_delay_ms'] is None, \
        f'expected None max_delay, got {m["max_delay_ms"]}'
    assert m['payload_utilization'] == 0.0, \
        'no payload delivered in 1-tick window'
    assert m['backlog_payload_bits'] == 200, \
        'all 200 bits should be backlog'