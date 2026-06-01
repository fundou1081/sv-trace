"""signal_tracer 公开 API 测试 — 锁定 P0 bug fix

测试 trace_signal() 在常见 SV 结构上的追踪能力。
每个测试是独立的 (import → trace → assert)，不依赖 shared state。
"""

import os
import sys
from pathlib import Path

# 加 src/ 到 path
SRC = Path(__file__).resolve().parents[2] / 'src'
sys.path.insert(0, str(SRC))

from signal_tracer import trace_signal  # noqa: E402


# ---------- helpers ----------

def _bench(name: str) -> str:
    """读 benchmark 文件"""
    p = Path(__file__).resolve().parents[2] / 'benchmarks' / name
    return p.read_text()


# ---------- 基础场景 ----------

class TestBasic:
    """P0 fix: 基础 always_ff / always_comb / assign 都要能追踪到"""

    def test_always_ff_registers(self):
        """01_basic_registers.sv: 最简 always_ff 寄存器"""
        code = _bench('01_basic_registers.sv')
        r = trace_signal('data_out', code, '01.sv')

        # 关键断言：能拿到 2 个 driver (rst 分支 + 正常分支)
        assert len(r.drivers) >= 2, f"expected >=2 drivers, got {len(r.drivers)}"
        exprs = {d.source_expr for d in r.drivers}
        assert "8'h00" in exprs or '8\'h00' in exprs, f"rst 路径没找到: {exprs}"
        assert "data_in" in exprs, f"data_in 路径没找到: {exprs}"

    def test_always_combinational(self):
        """02_combinational.sv: 基础 always_comb"""
        code = _bench('02_combinational.sv')
        r = trace_signal('result1', code, '02.sv')

        # 至少 1 个 driver
        assert len(r.drivers) >= 1, f"expected >=1 driver, got {len(r.drivers)}"

    def test_continuous_assign(self):
        """02_combinational.sv: continuous assign 也能追踪"""
        code = _bench('02_combinational.sv')
        # 03_bit_operations.sv 有更多 assign
        code3 = _bench('03_bit_operations.sv')
        # 在 03 里 find 一个被 assign 的 signal
        import re
        m = re.search(r'assign\s+(\w+)\s*=', code3)
        assert m, "找不到 assign"
        sig = m.group(1)
        r = trace_signal(sig, code3, '03.sv')
        assert len(r.drivers) >= 1


# ---------- 控制流 ----------

class TestControlFlow:
    """if/else、case、嵌套条件、task 调用都要处理"""

    def test_case_statement(self):
        """06_case_decoding.sv: case 语句里的赋值要能追踪"""
        code = _bench('06_case_decoding.sv')
        # 06 里是 instruction_decoder, casez (instruction[6:0])
        # instruction 应该被追踪到 (作为 case 的 load)
        r = trace_signal('instruction', code, '06.sv')
        assert len(r.loads) >= 1 or len(r.drivers) >= 1, \
            f"instruction 应该被追踪到 (case 表达式)"

    def test_nested_if(self):
        """08_complex_fsm.sv: 嵌套 if 条件"""
        code = _bench('08_complex_fsm.sv')
        # 08 里是 complex_fsm, 有 state_q / state_d
        # state_q 在 case(state_q) 里被读 + 在 if/else 里被赋值
        r = trace_signal('state_q', code, '08.sv')
        # state_q 应该被 case 读为 load 或者在 always_comb 里被赋值
        assert len(r.loads) >= 1 or len(r.drivers) >= 1, \
            f"state_q 完全空: drivers={len(r.drivers)} loads={len(r.loads)}"

    def test_condition_stack_populated(self):
        """条件栈: if 内部的赋值应该带回 condition_stack"""
        code = _bench('01_basic_registers.sv')
        r = trace_signal('data_out', code, '01.sv')
        # 至少 1 个 driver 的 condition_stack 包含 "!rst_n"
        found = False
        for d in r.drivers:
            if any('rst_n' in c for c in d.condition_stack):
                found = True
                break
        assert found, f"condition_stack 应该有 rst_n 相关条件: {[d.condition_stack for d in r.drivers]}"


# ---------- 数组 & 循环 ----------

class TestArrays:
    """数组位选、for 循环内的赋值"""

    def test_array_element_assignment(self):
        """for 循环内 a[i] = ... 形式的赋值"""
        code = '''
        module m;
            logic [7:0] a [16];
            logic [7:0] b;
            always_comb begin
                for (int i = 0; i < 8; i++)
                    a[i] = i ^ b;
            end
        endmodule
        '''
        r_b = trace_signal('b', code, 'arr.sv')
        # b 在 RHS, 应该是 load
        assert len(r_b.loads) >= 1, f"b 在 for 循环内被读，应有 load, got {len(r_b.loads)}"

    def test_array_driver_stored_under_base(self):
        """a[i] 的 driver 同时存到基名 'a' 下"""
        code = '''
        module m;
            logic [7:0] a [16];
            logic [7:0] b;
            always_comb a[0] = b;
        endmodule
        '''
        r = trace_signal('a', code, 'arr.sv')
        # 至少 1 个 driver
        assert len(r.drivers) >= 1, "数组元素 a[0] 的 driver 应该能在 'a' 查找到"


# ---------- 回归保护 ----------

class TestNoCrashes:
    """P0 fix: 跑所有 benchmark 不能 crash 也不能 throw exception"""

    BENCHMARKS = [
        '01_basic_registers.sv',
        '02_combinational.sv',
        '03_bit_operations.sv',
        '04_generate_for.sv',
        '05_priority_encoder.sv',
        '06_case_decoding.sv',
        '07_fsm.sv',
        '08_complex_fsm.sv',
        '09_reset_strategies.sv',
        '10_pipeline.sv',
        'comprehensive_driver_load_test.sv',
    ]

    def test_all_benchmarks_no_exception(self):
        """11 个 benchmark 全部 trace 不能抛异常"""
        import re
        for name in self.BENCHMARKS:
            code = _bench(name)
            # 提取候选信号
            sigs = set()
            for pat in [
                r'output\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)',
                r'input\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)',
                r'(?:logic|wire|reg)\s+(?:\[\d+:\d+\]\s+)?(\w+)',
            ]:
                sigs.update(re.findall(pat, code))
            sigs = sorted(sigs)[:10]

            for sig in sigs:
                # 只断言不抛异常
                trace_signal(sig, code, name)

    def test_all_benchmarks_produce_results(self):
        """11 个 benchmark 至少 1 个能产生 driver 或 load"""
        import re
        for name in self.BENCHMARKS:
            code = _bench(name)
            sigs = set()
            for pat in [
                r'output\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)',
                r'input\s+(?:logic\s+)?(?:\[\d+:\d+\]\s+)?(\w+)',
            ]:
                sigs.update(re.findall(pat, code))
            sigs = sorted(sigs)[:5]

            total = 0
            for sig in sigs:
                r = trace_signal(sig, code, name)
                total += len(r.drivers) + len(r.loads)

            assert total > 0, f"{name} 完全没追踪到任何东西"


# ---------- TraceResult 字段 ----------

class TestTraceResultFields:
    """TraceResult 字段必须正确填充 (scope_text / clock / reset / 等)"""

    def test_scope_text_present(self):
        """scope_text 应该有整个 always 块的源码"""
        code = _bench('01_basic_registers.sv')
        r = trace_signal('data_out', code, '01.sv')
        assert len(r.drivers) >= 1
        d = r.drivers[0]
        # 不强求完美，但至少有 always_ff 关键字
        assert 'always_ff' in d.scope_text, f"scope_text 应含 always_ff: {d.scope_text[:80]!r}"

    def test_scope_kind_correct(self):
        """scope_kind 应该是 ALWAYS_FF"""
        code = _bench('01_basic_registers.sv')
        r = trace_signal('data_out', code, '01.sv')
        from signal_tracer import ScopeKind
        assert all(d.scope_kind == ScopeKind.ALWAYS_FF for d in r.drivers), \
            f"scope_kind 应都是 ALWAYS_FF: {[d.scope_kind for d in r.drivers]}"

    def test_continuous_assign_scope_kind(self):
        """continuous assign 的 scope_kind 应该是 CONTINUOUS_ASSIGN"""
        code = _bench('02_combinational.sv')
        import re
        m = re.search(r'assign\s+(\w+)\s*=', code)
        sig = m.group(1)
        r = trace_signal(sig, code, '02.sv')
        from signal_tracer import ScopeKind
        assert any(d.scope_kind == ScopeKind.CONTINUOUS_ASSIGN for d in r.drivers), \
            f"应有 CONTINUOUS_ASSIGN 类型的 driver: {[d.scope_kind for d in r.drivers]}"


# ---------- M1.5: 多驱动检测 ----------

class TestMultiDriver:
    """M1.5 任务 1: 多驱动信号检测

    find_multi_drivers() / is_multi_driver() / get_driver_count()
    """

    def test_single_driver_not_multi(self):
        """单 driver 信号不会被报告为多驱动"""
        code = '''
        module m;
            logic [7:0] q;
            logic clk, rst_n;
            logic [7:0] d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 8'h0;
                else q <= d;
            end
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 't.sv').build()
        multi = t.find_multi_drivers()
        assert 'q' not in multi, f"q 只有 1 个 always_ff 驱动, 不应报告: {list(multi.keys())}"

    def test_two_always_blocks_multi_driver(self):
        """两个 always 块写同一信号 -> 是多驱动"""
        code = '''
        module m;
            logic [7:0] count;
            logic clk1, clk2, rst_n;
            logic en;
            always_ff @(posedge clk1 or negedge rst_n) begin
                if (en) count <= count + 1;
            end
            always_ff @(posedge clk2 or negedge rst_n) begin
                if (!en) count <= 0;
            end
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 't.sv').build()
        multi = t.find_multi_drivers()
        assert 'count' in multi, f"count 被 2 个 always_ff 驱动, 应在 multi 里: {list(multi.keys())}"
        assert len(multi['count']) >= 2

    def test_always_and_assign_multi_driver(self):
        """always + assign 写同一信号 -> 是多驱动 (典型 bug)"""
        code = '''
        module m;
            logic [7:0] x;
            logic [7:0] a, b, sel;
            assign x = sel ? a : b;
            always_comb x = 0;  // 覆盖 assign (多 driver bug)
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 't.sv').build()
        multi = t.find_multi_drivers()
        assert 'x' in multi, f"x 被 assign + always_comb 写, 应在 multi 里"

    def test_if_else_in_same_always_not_multi(self):
        """同一 always 块内的 if/else 多分支不视为多驱动"""
        code = '''
        module m;
            logic [7:0] q;
            logic clk, rst_n;
            logic [7:0] d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    q <= 8'h0;
                else
                    q <= d;
            end
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 't.sv').build()
        multi = t.find_multi_drivers()
        assert 'q' not in multi, f"if/else 同一 scope 算 1 个, 不应报告: {list(multi.keys())}"

    def test_get_driver_count(self):
        """get_driver_count 返回不同 scope 数"""
        code = '''
        module m;
            logic [7:0] x;
            logic a, b, c;
            assign x = a;
            assign x = b;  // second assign
            assign x = c;  // third
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 't.sv').build()
        cnt = t.get_driver_count('x')
        assert cnt == 3, f"3 个 assign 算 3 个 scope, got {cnt}"

    def test_is_multi_driver_method(self):
        """TraceSummary.is_multi_driver() 与 find_multi_drivers() 一致"""
        from signal_tracer import SignalTracer
        # Case 1: 多驱动
        code1 = '''
        module m;
            logic x;
            logic a, b, c1, c2, r;
            always_ff @(posedge c1 or negedge r) x <= a;
            always_ff @(posedge c2 or negedge r) x <= b;
        endmodule
        '''
        t1 = SignalTracer(code1, 'm1.sv').build()
        r1 = t1.trace('x')
        assert r1.is_multi_driver() is True
        # Case 2: 单驱动
        code2 = '''
        module m;
            logic x;
            logic a, c, r;
            always_ff @(posedge c or negedge r) x <= a;
        endmodule
        '''
        t2 = SignalTracer(code2, 'm2.sv').build()
        r2 = t2.trace('x')
        assert r2.is_multi_driver() is False
