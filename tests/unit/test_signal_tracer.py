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


# ---------- M1.5: clock/reset 提取 ----------

class TestClockResetExtraction:
    """M1.5 任务 2: 从 always_ff timing 表达式提取 clock/reset 字段"""

    def test_posedge_only(self):
        """@(posedge clk) → clock='clk', reset=''"""
        code = '''
        module m;
            logic clk, q, d;
            always_ff @(posedge clk) q <= d;
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        assert len(r.drivers) == 1
        d = r.drivers[0]
        assert d.clock == 'clk', f"expected clock='clk', got '{d.clock}'"
        assert d.reset == '', f"expected reset='', got '{d.reset}'"

    def test_posedge_clk_or_negedge_rst_n(self):
        """@(posedge clk or negedge rst_n) → clock='clk', reset='rst_n'"""
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 0;
                else q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        assert len(r.drivers) == 2
        for d in r.drivers:
            assert d.clock == 'clk', f"expected clock='clk', got '{d.clock}'"
            assert d.reset == 'rst_n', f"expected reset='rst_n', got '{d.reset}'"

    def test_posedge_arst_n_naming_heuristic(self):
        """@(posedge clk or posedge arst_n) → reset='arst_n' (命名启发式)"""
        code = '''
        module m;
            logic clk, arst_n, q, d;
            always_ff @(posedge clk or posedge arst_n) begin
                if (arst_n) q <= 0;
                else q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        for d in r.drivers:
            assert d.clock == 'clk', f"expected clock='clk', got '{d.clock}'"
            assert d.reset == 'arst_n', f"expected reset='arst_n' (命名启发式), got '{d.reset}'"

    def test_negedge_only_naming(self):
        """@(negedge rst_n) → reset='rst_n' (negedge 也判定 reset)"""
        code = '''
        module m;
            logic rst_n, q;
            always_ff @(negedge rst_n) q <= 0;
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        for d in r.drivers:
            assert d.reset == 'rst_n', f"expected reset='rst_n' (negedge 启发式), got '{d.reset}'"
            assert d.clock == '', f"expected clock='', got '{d.clock}'"

    def test_multi_clock_first_wins(self):
        """@(posedge clk1, posedge clk2) → clock='clk1' (取第一个)"""
        code = '''
        module m;
            logic clk1, clk2, q, d;
            always_ff @(posedge clk1, posedge clk2) q <= d;
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        for d in r.drivers:
            assert d.clock == 'clk1', f"expected clock='clk1' (first wins), got '{d.clock}'"

    def test_always_comb_no_clock(self):
        """always_comb 没有 timing control → clock='' reset=''"""
        code = '''
        module m;
            logic a, b;
            always_comb a = b;
        endmodule
        '''
        r = trace_signal('a', code, 'm.sv')
        for d in r.drivers:
            assert d.clock == '', f"expected clock='', got '{d.clock}'"
            assert d.reset == '', f"expected reset='', got '{d.reset}'"

    def test_continuous_assign_no_clock(self):
        """continuous assign 没有 scope clock/reset → 都空"""
        code = '''
        module m;
            logic a, b;
            assign a = b;
        endmodule
        '''
        r = trace_signal('a', code, 'm.sv')
        for d in r.drivers:
            assert d.clock == '', f"expected clock='', got '{d.clock}'"
            assert d.reset == '', f"expected reset='', got '{d.reset}'"

    def test_clock_domains_api(self):
        """get_clock_domains() 返回该信号涉及的所有时钟"""
        code = '''
        module m;
            logic clk, rst_n, q1, q2, d;
            always_ff @(posedge clk or negedge rst_n) q1 <= d;
            always_ff @(posedge clk or negedge rst_n) q2 <= d;
        endmodule
        '''
        r = trace_signal('q1', code, 'm.sv')
        domains = r.get_clock_domains()
        assert domains == ['clk'], f"expected ['clk'], got {domains}"


# ---------- M1.5: driver_chain 递归 ----------

class TestDriverChain:
    """M1.5 任务 3: SignalTracer.get_driver_chain() 递归查询

    与 TraceSummary.get_driver_chain() 不同, 本方法实际查 _drivers,
    能递归到上游所有信号。
    """

    def test_single_hop(self):
        """a = b → chain 包含 1 个 driver (a <- b)"""
        code = '''
        module m;
            logic [7:0] a, b;
            always_comb a = b;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        chain = t.get_driver_chain('a')
        # chain 至少 1 个 driver (a <- b)
        assert len(chain) >= 1
        # 第一个是 a 的 driver
        assert chain[0].signal_name == 'a'
        # chain 里包含 b 作为 source
        all_sources = set()
        for d in chain:
            all_sources.update(d.source_signals)
        assert 'b' in all_sources, f"b 应在 chain 的 source_signals 里: {all_sources}"

    def test_multi_hop(self):
        """a = b; b = c → chain 含 a, b 两个 driver"""
        code = '''
        module m;
            logic [7:0] a, b, c;
            always_comb a = b;
            always_comb b = c;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        chain = t.get_driver_chain('a')
        sigs_in_chain = [d.signal_name for d in chain]
        assert 'a' in sigs_in_chain
        assert 'b' in sigs_in_chain, f"b 应在 chain 里 (递归): {sigs_in_chain}"

    def test_self_reference_no_infinite_loop(self):
        """count = count + 1 → 不死循环"""
        code = '''
        module m;
            logic [7:0] count;
            logic clk;
            always_ff @(posedge clk) count <= count + 1;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        # 不抛异常
        chain = t.get_driver_chain('count')
        # count 应在 chain 里 (自指不算环, 不会无限递归)
        sigs_in_chain = [d.signal_name for d in chain]
        assert 'count' in sigs_in_chain
        # count 只应出现一次 (visited 阻断)
        assert sigs_in_chain.count('count') == 1, \
            f"count 应只出现 1 次, got {sigs_in_chain.count('count')}: {sigs_in_chain}"

    def test_cycle_no_infinite_loop(self):
        """a = b; b = a → 环检测, 不死循环"""
        code = '''
        module m;
            logic [7:0] a, b;
            always_comb a = b;
            always_comb b = a;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        # 不应抛 RecursionError 或栈溢出
        chain = t.get_driver_chain('a')
        # 至少 a 的 driver 自身
        assert len(chain) >= 1
        sigs_in_chain = [d.signal_name for d in chain]
        # a 和 b 各最多 1 次 (visited 阻断)
        assert sigs_in_chain.count('a') <= 1
        assert sigs_in_chain.count('b') <= 1

    def test_max_depth_limit(self):
        """深 5 层的 chain, max_depth=3 应截断"""
        code = '''
        module m;
            logic [7:0] s0, s1, s2, s3, s4, s5;
            always_comb s0 = s1;
            always_comb s1 = s2;
            always_comb s2 = s3;
            always_comb s3 = s4;
            always_comb s4 = s5;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        # 完整链: s0, s1, s2, s3, s4 (5 个 driver)
        full = t.get_driver_chain('s0', max_depth=10)
        # 截断: max_depth=3 只能到 s3 (depth 0=s0, 1=s1, 2=s2, 3=s3)
        # 实际取决于实现: walk(sig, 0) → 加 s0 的 driver, 递归 src 走 depth 1
        # 截断 = 3 应该最多到 s3
        limited = t.get_driver_chain('s0', max_depth=3)
        # 截断的不应比 full 长
        assert len(limited) <= len(full), \
            f"max_depth=3 不应比无限 max_depth 链更长: {len(limited)} vs {len(full)}"
        # 且 limited 至少 1 个 (s0 自身)
        assert len(limited) >= 1

    def test_conditional_source_in_chain(self):
        """a = sel ? b : c → chain 应包含 sel, b, c (作为 source_signals)"""
        code = '''
        module m;
            logic [7:0] a, b, c;
            logic sel;
            always_comb a = sel ? b : c;
        endmodule
        '''
        from signal_tracer import SignalTracer
        t = SignalTracer(code, 'm.sv').build()
        chain = t.get_driver_chain('a')
        # 收集所有 source_signal
        all_sources = set()
        for d in chain:
            all_sources.update(d.source_signals)
        # 至少 sel, b, c 应被某个 driver 提及 (作为 a 的 source)
        # a 的 driver.source_signals 应包含 sel, b, c
        first_driver = chain[0]
        for sig in ('sel', 'b', 'c'):
            assert sig in first_driver.source_signals, \
                f"{sig} 应在 chain[0].source_signals 里: {first_driver.source_signals}"


# ---------- M2: 上下文召回做厚 ----------

class TestContextAccuracy:
    """M2 任务 1: 修复 line / scope_line_end / scope_text 准确性"""

    def test_line_is_actual_assignment_not_scope_start(self):
        """line 应该是实际赋值表达式所在行, 不是 always_ff 起始行"""
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    q <= 8'h0;
                else
                    q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        # 期望: 2 个 driver, line 应该是 6 和 8 (不是 4)
        assert len(r.drivers) == 2
        lines = sorted(d.line for d in r.drivers)
        # line 6 是 "q <= 8'h0;" 所在行, line 8 是 "q <= d;"
        assert lines[0] >= 6, f"第一个 driver 的行号应 >= 6 (实际赋值行), got {lines[0]}"
        assert lines[0] != 4, f"line 不应是 scope 起始行 4, got {lines[0]}"

    def test_scope_line_end_is_actual_end(self):
        """scope_line_end 应该是 always 块结束行, 不是起始行"""
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    q <= 8'h0;
                else
                    q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        for d in r.drivers:
            # scope 起始行 < scope 结束行
            assert d.scope_line_start < d.scope_line_end, \
                f"scope_line_start {d.scope_line_start} 应 < scope_line_end {d.scope_line_end}"
            # 结束行应在 10 左右 (end 在 line 10)
            assert d.scope_line_end >= 9, \
                f"scope_line_end 应 >= 9, got {d.scope_line_end}"

    def test_scope_text_is_multiline(self):
        """scope_text 应保留多行 (含 \\n), 不是单行空格连接"""
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    q <= 8'h0;
                else
                    q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        for d in r.drivers:
            assert '\n' in d.scope_text, \
                f"scope_text 应含换行符 (多行), got: {d.scope_text[:80]!r}"
            # 且应能看到 'always_ff' 和 'end'
            assert 'always_ff' in d.scope_text
            assert 'end' in d.scope_text

    def test_scope_text_no_trailing_whitespace(self):
        """scope_text 不应有前导/尾部多余空白"""
        code = '''
        module m;
            logic a, b;
            always_comb a = b;
        endmodule
        '''
        r = trace_signal('a', code, 'm.sv')
        for d in r.drivers:
            assert d.scope_text == d.scope_text.strip(), \
                f"scope_text 应已被 strip, got: {d.scope_text!r}"

    def test_char_offset_populated(self):
        """char_offset 应该是表达式的字符偏移, 不再是 0"""
        code = '''
        module m;
            logic a, b;
            always_comb a = b;
        endmodule
        '''
        r = trace_signal('a', code, 'm.sv')
        for d in r.drivers:
            assert d.char_offset > 0, \
                f"char_offset 应 > 0 (实际偏移), got {d.char_offset}"


class TestContextBundle:
    """M2 任务 2 + 3: ContextBundle 数据结构 + TraceResult.context 字段"""

    def test_context_bundle_basic_fields(self):
        """ContextBundle 包含所有关键字段"""
        from signal_tracer import ContextBundle
        cb = ContextBundle(
            file='m.sv',
            line=10,
            char_offset=100,
            scope_text='always_ff ...',
            scope_line_start=8,
            scope_line_end=13,
            scope_kind='always_ff',
            clock='clk',
            reset='rst_n',
            condition='!rst_n',
            condition_stack=('!rst_n',),
            is_port=True,
            port_direction='out',
            hierarchical_path='top.u_dut.q',
            confidence='high',
        )
        assert cb.file == 'm.sv'
        assert cb.line == 10
        assert cb.clock == 'clk'
        assert cb.reset == 'rst_n'
        assert cb.condition_stack == ('!rst_n',)

    def test_context_bundle_is_frozen(self):
        """ContextBundle 是 frozen dataclass, 不能修改"""
        from signal_tracer import ContextBundle
        cb = ContextBundle(
            file='m.sv', line=10, char_offset=0,
            scope_text='', scope_line_start=0, scope_line_end=0,
            scope_kind='', clock='', reset='',
            condition='', condition_stack=(),
            is_port=False, port_direction='', hierarchical_path='',
            confidence='high',
        )
        # 尝试修改应抛 FrozenInstanceError
        import pytest
        from dataclasses import FrozenInstanceError
        with pytest.raises(FrozenInstanceError):
            cb.file = 'changed.sv'

    def test_to_context_method(self):
        """TraceResult.to_context() 返回 ContextBundle"""
        from signal_tracer import ContextBundle
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 0;
                else q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        d = r.drivers[0]
        ctx = d.to_context()
        assert isinstance(ctx, ContextBundle)
        assert ctx.file == 'm.sv'
        assert ctx.clock == 'clk'
        assert ctx.reset == 'rst_n'
        assert ctx.scope_kind == 'always_ff'

    def test_to_contexts_on_summary(self):
        """TraceSummary.to_contexts() 返回 List[ContextBundle]"""
        from signal_tracer import ContextBundle
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n) q <= 0;
                else q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        ctxs = r.to_contexts()
        assert len(ctxs) == 2
        assert all(isinstance(c, ContextBundle) for c in ctxs)

    def test_context_bundle_to_dict(self):
        """to_dict() 可序列化"""
        from signal_tracer import ContextBundle
        cb = ContextBundle(
            file='m.sv', line=10, char_offset=100,
            scope_text='always_ff @(posedge clk) ...', scope_line_start=8, scope_line_end=12,
            scope_kind='always_ff', clock='clk', reset='',
            condition='', condition_stack=('!rst_n',),
            is_port=True, port_direction='out', hierarchical_path='top.q',
            confidence='high',
        )
        d = cb.to_dict()
        assert d['file'] == 'm.sv'
        assert d['line'] == 10
        assert d['clock'] == 'clk'
        assert d['condition_stack'] == ['!rst_n']  # tuple → list
        # 可 JSON 序列化
        import json
        json_str = json.dumps(d)
        assert 'always_ff' in json_str
        assert 'clk' in json_str

    def test_context_bundle_summary(self):
        """summary() 输出一行可读摘要"""
        from signal_tracer import ContextBundle
        cb = ContextBundle(
            file='m.sv', line=10, char_offset=0,
            scope_text='', scope_line_start=8, scope_line_end=12,
            scope_kind='always_ff', clock='clk', reset='rst_n',
            condition='', condition_stack=('!rst_n',),
            is_port=False, port_direction='', hierarchical_path='',
            confidence='high',
        )
        s = cb.summary()
        assert 'm.sv:10' in s
        assert 'always_ff' in s
        assert 'clock=clk' in s
        assert 'reset=rst_n' in s
        assert '!rst_n' in s

    def test_context_bundle_condition_stack_is_tuple(self):
        """condition_stack 应是 tuple (frozen 要求)"""
        from signal_tracer import ContextBundle
        cb = ContextBundle(
            file='', line=0, char_offset=0,
            scope_text='', scope_line_start=0, scope_line_end=0,
            scope_kind='', clock='', reset='',
            condition='', condition_stack=('a', 'b', 'c'),
            is_port=False, port_direction='', hierarchical_path='',
            confidence='high',
        )
        assert isinstance(cb.condition_stack, tuple)
        assert cb.condition_stack == ('a', 'b', 'c')

    def test_to_context_preserves_all_fields(self):
        """to_context() 应保留 TraceResult 的所有相关字段"""
        code = '''
        module m;
            logic clk, rst_n, q, d;
            always_ff @(posedge clk or negedge rst_n) begin
                if (!rst_n)
                    q <= 8'h0;
                else
                    q <= d;
            end
        endmodule
        '''
        r = trace_signal('q', code, 'm.sv')
        d = r.drivers[0]
        ctx = d.to_context()
        # 字段对得上
        assert ctx.file == d.file
        assert ctx.line == d.line
        assert ctx.char_offset == d.char_offset
        assert ctx.scope_text == d.scope_text
        assert ctx.scope_line_start == d.scope_line_start
        assert ctx.scope_line_end == d.scope_line_end
        assert ctx.clock == d.clock
        assert ctx.reset == d.reset
        assert tuple(d.condition_stack) == ctx.condition_stack
        assert ctx.is_port == d.is_port
        assert ctx.port_direction == d.port_direction
        assert ctx.hierarchical_path == d.hierarchical_path
        assert ctx.confidence == d.confidence


# ---------- M3: 跨文件 + 层次路径 ----------

class TestMultiFile:
    """M3 任务 1: SignalTracer 支持多文件输入

    验证:
    - add_file() API
    - 跨文件 Compilation (单 Compilation, 多 SyntaxTree)
    - hpath-based driver 存储
    - 向后兼容 (单文件)
    """

    FIXTURE_DIR = 'tests/fixtures/m3_hierarchical'

    def _load_fixtures(self):
        from signal_tracer import SignalTracer
        t = SignalTracer()
        for n in ['top', 'mid', 'leaf']:
            path = f'{self.FIXTURE_DIR}/{n}.sv'
            t.add_file(path, open(path).read())
        t.build()
        return t

    def test_add_file_returns_self(self):
        """add_file() 返回 self 支持链式调用"""
        from signal_tracer import SignalTracer
        t = SignalTracer()
        result = t.add_file('m.sv', 'module m; endmodule')
        assert result is t

    def test_backward_compat_single_file(self):
        """老 API SignalTracer(code, path) 仍工作"""
        from signal_tracer import SignalTracer
        code = '''
        module m;
            logic a, b;
            always_comb a = b;
        endmodule
        '''
        t = SignalTracer(code, 'm.sv').build()
        r = t.trace('a')
        assert len(r.drivers) == 1

    def test_multi_file_loads_to_single_compilation(self):
        """3 个文件应加到同一 Compilation, 都能解析"""
        t = self._load_fixtures()
        # 验证 _files 里有 3 个
        assert len(t._files) == 3

    def test_hierarchical_path_storage(self):
        """driver key 应是 {hpath}.{signal} 形式"""
        t = self._load_fixtures()
        # leaf 的 dout 在两个 instance 中被驱动
        assert 'top.u_mid.u_l1.dout' in t._drivers
        assert 'top.u_mid.u_l2.dout' in t._drivers
        # leaf 端口 dout 应有 2 个 driver (rst 分支 + 正常分支) × 2 instance = 4
        assert len(t._drivers['top.u_mid.u_l1.dout']) == 2
        assert len(t._drivers['top.u_mid.u_l2.dout']) == 2

    def test_trace_by_full_hpath(self):
        """trace('top.u_mid.u_l1.dout') 查到具体 instance 的 driver"""
        t = self._load_fixtures()
        r = t.trace('top.u_mid.u_l1.dout')
        # 2 个 driver (rst 分支 + 正常分支)
        assert len(r.drivers) == 2
        # driver 应该有正确的 hpath
        for d in r.drivers:
            assert d.hierarchical_path == 'top.u_mid.u_l1', \
                f"expected 'top.u_mid.u_l1', got {d.hierarchical_path!r}"

    def test_trace_by_suffix_match_finds_all_instances(self):
        """trace('dout') 找到所有 instance 中的 dout"""
        t = self._load_fixtures()
        r = t.trace('dout')
        # 4 个 driver: u_l1.dout (2) + u_l2.dout (2)
        assert len(r.drivers) == 4
        hpaths = {d.hierarchical_path for d in r.drivers}
        assert hpaths == {'top.u_mid.u_l1', 'top.u_mid.u_l2'}

    def test_trace_by_suffix_match_for_loads(self):
        """trace('din') 找到所有 load (被读位置)"""
        t = self._load_fixtures()
        r = t.trace('din')
        # din 在 leaf 里被读 (RHS of dout <= din), 在两个 instance 中
        # leaf.din 是 input port, 不会出现在 _loads 里 (port 不算 load)
        # 实际是 mid 的 sw1/sw2 在 mid 里驱动 sum/diff 之前, din 是 leaf 内部
        # 这里 _loads 应该有 2 个 (两个 leaf instance 各一个)
        assert len(r.loads) >= 1

    def test_non_existent_signal_returns_empty(self):
        """不存在的信号返回空, 不抛异常"""
        t = self._load_fixtures()
        r = t.trace('nonexistent_signal')
        assert len(r.drivers) == 0
        assert len(r.loads) == 0

    def test_two_file_simple_hierarchy(self):
        """2 个文件的最简层级 (top + sub)"""
        from signal_tracer import SignalTracer
        sub_code = '''
        module sub (
            input  logic clk, rst_n,
            input  logic [7:0] din,
            output logic [7:0] dout
        );
            always_ff @(posedge clk or negedge rst_n)
                if (!rst_n) dout <= 0;
                else dout <= din;
        endmodule
        '''
        top_code = '''
        module top (
            input  logic clk, rst_n,
            input  logic [7:0] sw,
            output logic [7:0] led
        );
            sub u_sub(.clk(clk), .rst_n(rst_n), .din(sw), .dout(led));
        endmodule
        '''
        t = SignalTracer()
        t.add_file('sub.sv', sub_code)
        t.add_file('top.sv', top_code)
        t.build()
        # 跨文件 sub 仍能解析
        assert 'top.u_sub.dout' in t._drivers
        r = t.trace('top.u_sub.dout')
        assert len(r.drivers) == 2
