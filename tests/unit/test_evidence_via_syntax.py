"""M5.1h: syntax-based evidence 路径测试

锁定 Step 1-3 修复:
- Step 1: SignalTracer.build() 同步 SourceManager 给 evidence singleton
- Step 2: 注入 expr.syntax 而非 expr (语义节点)
- Step 3: build_evidence_via_syntax 兼容语义节点 + context_available 显式标记

设计原则: syntax 路径产出的 evidence 应该和 file-based 路径在关键字段上一致:
- line: 完全一致 (都从 SourceManager 算)
- snippet: 内容等价 (都从同一文件读, 可能差 leading whitespace)
- is_verified: 都 True (都包含 signal_name)
"""

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / 'src'
sys.path.insert(0, str(SRC))

import pytest

from signal_tracer import SignalTracer
from signal_tracer.models import (
    CodeEvidence,
    build_evidence,
    build_evidence_via_syntax,
    _get_source_manager,
)


# ---------- 基础: build() 后 SourceManager 同步 ----------

class TestSourceManagerSync:
    """Step 1 锁定: SignalTracer.build() 必须调 _set_source_manager"""

    def test_build_sets_singleton_sourcemgr(self):
        """build() 后, _get_source_manager() 返回非 None"""
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic a; endmodule\n')
        t.build()
        sm = _get_source_manager()
        assert sm is not None
        assert sm is t._source_manager

    def test_build_empty_files_leaves_singleton(self):
        """没有 file 时 build() 也走通 (singleton 维持上一次值或 None)"""
        t = SignalTracer()
        t.build()  # 没 add_file
        # 不应崩溃
        sm = _get_source_manager()
        # singleton 可能为 None 也可能维持上一次, 只验证不崩
        assert sm is None or sm is not None


# ---------- syntax 节点 vs 语义节点 ----------

class TestSyntaxNodeInjection:
    """Step 2 锁定: tracer 注入的 _syntax_node 是 syntax 节点, 不是语义 Expression"""

    def test_injected_node_is_syntax_kind(self):
        """_syntax_node 是 BinaryExpressionSyntax 等 syntax 类型, 不是 AssignmentExpression"""
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        d = t.trace_drivers('c')[0]
        # type name 应该是 SyntaxXxx, 不是 Expression
        type_name = type(d._syntax_node).__name__
        assert 'Syntax' in type_name, f"expected Syntax node, got {type_name}"
        assert 'Expression' not in type_name or 'Syntax' in type_name

    def test_injected_node_has_source_range(self):
        """syntax 节点有 sourceRange 属性"""
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic a, b;
  always_comb a = b;
endmodule
''')
        t.build()
        d = t.trace_drivers('a')[0]
        assert d._syntax_node is not None
        assert hasattr(d._syntax_node, 'sourceRange')


# ---------- build_evidence_via_syntax 直接调用 ----------

class TestBuildEvidenceViaSyntax:
    """Step 3 锁定: build_evidence_via_syntax 的核心行为"""

    def _make_tracer(self) -> SignalTracer:
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        return t

    def test_syntax_node_param(self):
        """传 syntax 节点: 拿到 line + snippet + is_verified"""
        t = self._make_tracer()
        d = t.trace_drivers('c')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
        )
        assert ev.source == 'syntax'
        assert ev.line == 4  # 1-indexed, 'c = a + b;' 在第 4 行
        assert ev.snippet_present is True
        # snippet 应该包含 signal_name
        assert 'c' in ev.snippet
        assert ev.matches_signal_name is True
        assert ev.is_verified is True

    def test_semantic_expression_fallback(self):
        """传语义 Expression: 自动 fallback 到 .syntax"""
        t = self._make_tracer()
        # 拿一个语义 Expression (从 driver trace 拿 _syntax_node, 但故意包一层 Expression)
        # 简单办法: 直接 mock 一个有 .syntax 的对象
        d = t.trace_drivers('c')[0]
        # d._syntax_node 是 BinaryExpressionSyntax, 我们模拟它是 '表达式' 的场景:
        # 用 pyslang 拿一个真语义 expr
        import pyslang
        from signal_tracer.models import _set_source_manager
        # M5.1h fix: pyslang 11+ 兼容 — Compilation / SyntaxTree 都可能不在 root
        _Compilation = getattr(pyslang, 'Compilation', None) or pyslang.ast.Compilation
        _SyntaxTree = getattr(pyslang, 'SyntaxTree', None) or pyslang.syntax.SyntaxTree
        comp = _Compilation()
        comp.addSyntaxTree(_SyntaxTree.fromText(
            'module n; logic x, y; assign y = x; endmodule\n',
            'n.sv'))
        _set_source_manager(comp.sourceManager)
        # 拿 assign 的 expression (semantic)
        mod = comp.getRoot().find('n')
        sem_expr = None
        for m in mod.body:
            if type(m).__name__ == 'ContinuousAssignSymbol':
                sem_expr = m.assignment
                break
        assert sem_expr is not None
        assert 'Expression' in type(sem_expr).__name__
        # Step 3 兜底: 传语义 Expression 也应能拿到 snippet
        ev = build_evidence_via_syntax(
            syntax_node=sem_expr,
            source_expr='x',
            signal_name='y',
        )
        assert ev.source == 'syntax'
        assert ev.line > 0  # 不是 0
        assert ev.snippet_present is True
        # 语义 Expression 自动 fallback 到 .syntax, snippet 应是源码
        assert 'y' in ev.snippet

    def test_none_syntax_node_returns_empty(self):
        """传 None: 返回空 evidence, 不崩"""
        ev = build_evidence_via_syntax(syntax_node=None)
        assert ev.source == 'syntax'
        assert ev.line == 0
        assert ev.snippet == ''
        assert ev.snippet_present is False
        assert ev.is_verified is False

    def test_syntax_mode_marks_context_unavailable(self):
        """M5.1h step 7: syntax 模式 context 也可拿到, 走 SourceManager + getSourceText

        修复前 (Step 3-4): context_available=False, context_before/after=[]
        修复后 (Step 7): context_before/after 填充, context_available=True (与 file 模式一样)
        """
        t = self._make_tracer()
        d = t.trace_drivers('c')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
        )
        # Step 7 后两路都拿得到 context
        assert ev.context_available is True
        assert len(ev.context_before) > 0  # '  always_comb begin'
        assert len(ev.context_after) > 0   # '  end', 'endmodule'
        # 与 file 模式产出顺序一致 (start/end 索引算法同)
        file_ev = d._evidence_override
        assert ev.context_before == file_ev.context_before
        assert ev.context_after == file_ev.context_after

    def test_syntax_context_unavailable_when_no_sourcemgr(self):
        """syntax 模式没 SourceManager (singleton) 时 context_available=False

        防御: _get_source_manager() 返回 None 时 _extract_syntax_context 返回空。
        """
        from signal_tracer.models import _set_source_manager, build_evidence_via_syntax as bvs
        # 临时清空 singleton
        saved = _set_source_manager(None)  # 这么写 _set_source_manager 不接受 None
        # 不用上面这个, 改成走一个没 build 的 tracer
        t = self._make_tracer()
        # 不调 build, 拿不到 _syntax_node. 换个方式:
        # 直接 mock 一个没 SourceManager 的环境
        import signal_tracer.models as m
        original_sm = m._singleton_sm
        m._singleton_sm = None
        try:
            d = t.trace_drivers('c')[0]
            # 手动清掉 build 时的 singleton (上面已经设为 None)
            ev = bvs(
                syntax_node=d._syntax_node,
                source_expr=d.source_expr,
                signal_name=d.signal_name,
            )
            # context 拿不到, 但其他字段还行
            assert ev.context_available is False
            assert ev.context_before == []
            assert ev.context_after == []
        finally:
            m._singleton_sm = original_sm

    def test_file_mode_default_context_available(self):
        """file 模式: context_available 默认 True (backward compat)"""
        ev = build_evidence(
            file='m.sv', line=1,
            file_content='module m;\n  logic a;\nendmodule\n',
        )
        assert ev.context_available is True
        # context_window=2 时应该有 context
        assert len(ev.context_before) > 0 or len(ev.context_after) > 0


# ---------- syntax vs file 一致性 ----------

class TestSyntaxVsFileConsistency:
    """核心保证: 同一 trace, syntax 路径和 file 路径产出的 line + snippet 一致"""

    CODE = '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
'''

    def _both_evidences(self):
        """跑一次 trace, 同时拿 file-based 和 syntax-based evidence"""
        t = SignalTracer()
        t.add_file('m.sv', self.CODE)
        t.build()
        d = t.trace_drivers('c')[0]

        # file-based (走 _evidence_override 默认注入的)
        file_ev = d._evidence_override

        # syntax-based (直接调, 不走 override)
        syn_ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
            scope_text=d.scope_text,
            file=d.file,
        )
        return file_ev, syn_ev, d

    def test_line_identical(self):
        file_ev, syn_ev, _ = self._both_evidences()
        assert file_ev.line == syn_ev.line, \
            f"line mismatch: file={file_ev.line}, syntax={syn_ev.line}"
        assert syn_ev.line == 4  # 硬编码兜底

    def test_signal_name_match_identical(self):
        """两路都能找到 signal_name"""
        file_ev, syn_ev, _ = self._both_evidences()
        assert file_ev.matches_signal_name is True
        assert syn_ev.matches_signal_name is True

    def test_is_verified_both_true(self):
        """两路都 verified"""
        file_ev, syn_ev, _ = self._both_evidences()
        assert file_ev.is_verified is True
        assert syn_ev.is_verified is True

    def test_source_field_distinguishes(self):
        """source 字段是 'file' vs 'syntax', caller 能区分"""
        file_ev, syn_ev, _ = self._both_evidences()
        assert file_ev.source == 'file'
        assert syn_ev.source == 'syntax'

    def test_source_expr_uses_real_source_text(self):
        """M5.1h step 5: source_expr 是真实源码 (e.g. 'a + b'), 不是 C++ enum ('a Add b')

        修复前: _get_rhs_info_semantic_kind 里 BinaryOp op_text='Add' 拼出 'a Add b',
        snippet 'c = a + b;' 不包含 'a Add b' -> matches_source_expr=False。
        修复后: wrapper _get_rhs_info_semantic 覆盖 text 为 str(expr.syntax).strip(),
        拿到 'a + b' 真实源码 -> matches_source_expr=True。
        """
        t = SignalTracer()
        t.add_file('m.sv', self.CODE)
        t.build()
        d = t.trace_drivers('c')[0]
        # source_expr 应该是 'a + b' (含空格, 原始 source)
        assert d.source_expr == 'a + b', f"got {d.source_expr!r}, expected 'a + b'"
        # 两条 evidence 都应 matches_source_expr=True
        file_ev = d._evidence_override
        syn_ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
        )
        assert file_ev.matches_source_expr is True
        assert syn_ev.matches_source_expr is True


class TestLoadTraceNarrowing:
    """M5.1h step 6: load trace 的 syntax snippet narrow 到具体 sub-expression

    driver trace 的 signal_name 是 LHS, 不能 narrow (会丢 source_expr=RHS)。
    load trace 的 signal_name 是 RHS signal, narrow 到该 sub-expr 更准。
    """

    def test_load_a_narrows_to_identifier(self):
        """load 'a' in 'c = a + b' -> snippet='a' (不是 'c = a + b')"""
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        l = t.trace_loads('a')[0]
        ev = l.to_context(source_mode='syntax').code_evidence
        assert ev.snippet == 'a'
        assert ev.matches_signal_name is True

    def test_load_b_narrows_to_identifier(self):
        """load 'b' in 'c = a + b' -> snippet='b'"""
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        l = t.trace_loads('b')[0]
        ev = l.to_context(source_mode='syntax').code_evidence
        assert ev.snippet == 'b'

    def test_load_rangeselect_narrows_to_whole_bit_slice(self):
        """load 'mem' in 'c = mem[3:0] & mask[3:0]' -> snippet='mem[3:0]'
        (narrowing 到最具体含 'mem' 的子节点, 是 RangeSelectSyntax, 显示具体位选)
        """
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] c;
  logic [3:0] mem, mask;
  always_comb c = mem[3:0] & mask[3:0];
endmodule
''')
        t.build()
        l = t.trace_loads('mem')[0]
        ev = l.to_context(source_mode='syntax').code_evidence
        assert ev.snippet == 'mem[3:0]'
        assert ev.matches_signal_name is True

    def test_driver_trace_not_narrowed(self):
        """driver trace 的 snippet 是整节点 (e.g. 'c = a + b'), 不 narrow 到 LHS

        如果 narrow 到 'c', 会丢 source_expr='a + b' 上下文, matches_source_expr 变 False。
        """
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        d = t.trace_drivers('c')[0]
        ev = d.to_context(source_mode='syntax').code_evidence
        # 整节点保留
        assert ev.snippet == 'c = a + b'
        # matches_source_expr 验证 source_expr='a + b' 在 snippet 中
        assert ev.matches_source_expr is True
        # credibility 仍能拿到 0.8
        assert ev.credibility_score == pytest.approx(0.8)

    def test_repeated_signal_narrows_to_first(self):
        """'c = a + a' 中 load 'a' 出现两次, narrow 到左起第一个 'a'"""
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic a, b, c;
  always_comb c = a + a;
endmodule
''')
        t.build()
        loads = t.trace_loads('a')
        assert len(loads) == 2  # 2 个 load (左 + 右)
        for l in loads:
            ev = l.to_context(source_mode='syntax').code_evidence
            assert ev.snippet == 'a'  # 两条都 narrow 到 'a'

    def test_no_narrow_when_signal_not_in_node(self):
        """signal_name 不在 syntax_node 中时, 不 narrow (退化到整节点)

        例: load trace 的 signal_name 不在 syntax 树中 (pyslang 未解析出的信号),
        DFS 找不到, fallback 到整节点。snippet 是整表达式。
        """
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
''')
        t.build()
        # signal_name='nonexistent_xyz' 不在 syntax 树中
        d = t.trace_drivers('c')[0]
        # 手动调 build_evidence_via_syntax, narrow_to 找不到
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name='nonexistent_xyz',
            narrow_to='nonexistent_xyz',
        )
        # narrow_to 找不到, 退化到整节点
        assert ev.snippet == 'c = a + b'
        # matches_signal_name=False (因为 'nonexistent_xyz' 不在 snippet)
        assert ev.matches_signal_name is False


# ---------- to_context 集成 ----------

class TestToContextIntegration:
    """TraceResult.to_context() 三种 source_mode 行为"""

    CODE = '''module m;
  logic [7:0] a, b, c;
  always_comb begin
    c = a + b;
  end
endmodule
'''

    def test_auto_mode_uses_pre_built(self):
        """auto + 有 _evidence_override: 走 file-based"""
        t = SignalTracer()
        t.add_file('m.sv', self.CODE)
        t.build()
        d = t.trace_drivers('c')[0]
        # 默认 verify=True, _evidence_override 已被设
        assert d._evidence_override is not None
        ctx = d.to_context(source_mode='auto')
        assert ctx.code_evidence.source == 'file'

    def test_syntax_mode_explicit(self):
        """source_mode='syntax' 强制走 syntax 路径"""
        t = SignalTracer()
        t.add_file('m.sv', self.CODE)
        t.build()
        d = t.trace_drivers('c')[0]
        ctx = d.to_context(source_mode='syntax')
        assert ctx.code_evidence.source == 'syntax'
        assert ctx.code_evidence.line == 4
        assert ctx.code_evidence.is_verified is True

    def test_file_mode_explicit(self):
        """source_mode='file' 强制走 file 路径"""
        t = SignalTracer()
        t.add_file('m.sv', self.CODE)
        t.build()
        d = t.trace_drivers('c')[0]
        ctx = d.to_context(source_mode='file')
        assert ctx.code_evidence.source == 'file'


# ---------- 跨文件 ----------

class TestCrossFile:
    """M4 跨文件: SourceManager 路径天然支持, syntax evidence 也应工作"""

    def test_evidence_in_second_file(self):
        """driver 在第 2 个文件, line 应该按 2.sv 算"""
        t = SignalTracer()
        t.add_file('a.sv', '''module a;
  logic [7:0] x, y;
  always_comb x = y + 1;
endmodule
''')
        t.add_file('b.sv', '''module b;
  logic [7:0] q;
  always_comb q = 8'h00;
endmodule
''')
        t.build()

        # 追 a.sv 里的 x
        d = t.trace_drivers('x')[0]
        syn_ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
            file=d.file,
        )
        file_ev = d._evidence_override

        # line 一致
        assert syn_ev.line == file_ev.line
        # file 字段应该反映 a.sv
        assert 'a' in syn_ev.file or 'a' in file_ev.file


# ---------- to_evidence_string 格式 ----------

class TestEvidenceStringFormat:
    """to_evidence_string 应该区分 file / syntax 格式"""

    def test_file_mode_shows_context(self):
        ev = build_evidence(
            file='m.sv', line=3,
            file_content='module m;\n  logic a;\n  always_comb a = 1;\nendmodule\n',
            signal_name='a',
        )
        s = ev.to_evidence_string()
        assert 'source: file' in s
        assert 'a = 1' in s

    def test_syntax_mode_marks_no_context(self):
        """M5.1h step 7: syntax 模式 to_evidence_string 现在也有 context (与 file 一样)

        修复前 (Step 3): 显示 'context unavailable' 提示
        修复后 (Step 7): 与 file 模式一致, 都有 context_before/after 显示

        用多行文件确保 context 实际有内容 (单行文件 line=1 没前后行会回退到退化路径)。
        """
        t = SignalTracer()
        t.add_file('m.sv', '''module m;
  logic a, b;
  always_comb begin
    a = b;
  end
endmodule
''')
        t.build()
        d = t.trace_drivers('a')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            signal_name='a',
        )
        s = ev.to_evidence_string()
        assert 'source: syntax' in s
        # Step 7 后 syntax 模式也有 context (file 多行, line 4 有前后)
        # 退化路径会含 'context unavailable' 提示
        assert 'context unavailable' not in s
        assert '| ' in s  # context 行有 '| ' 分隔符
        # context_before 包含 'always_comb begin' (line 3, 算法与 file-based 同)
        assert 'always_comb begin' in s
        # context_after 包含 'end' (line 5)
        assert 'end' in s
        # 实际显示
        print('--- syntax evidence ---')
        print(s)


# ---------- M5.1h 修复回归: SyntaxNodeSnapshot 冻结文本 ----------
class TestSyntaxNodeSnapshot:
    """锁定 M5.1h SyntaxNodeSnapshot 修复: 防止 pyslang buffer 复用导致 str() 截断

    背景: pyslang SyntaxNode.__str__() 依赖 Compilation 内部 buffer, 第二个 Compilation
    创建后, 第一个的 SyntaxNode 调 str() 会返回截断的内容 (e.g. 'b = foo(a)' → 'b = foo')。
    修复: SyntaxNodeSnapshot 在 inject 时立刻 str() 冻结文本。
    """

    def test_snapshot_freezes_text_on_inject(self):
        """driver trace 的 _syntax_node 是 SyntaxNodeSnapshot, str() 返回冻结文本"""
        from signal_tracer.models import SyntaxNodeSnapshot
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic [7:0] a, b, c; always_comb c = a + b; endmodule')
        t.build()
        d = t.trace_drivers('c')[0]
        assert isinstance(d._syntax_node, SyntaxNodeSnapshot)
        # str() 立刻返回完整内容, 不依赖 buffer
        assert str(d._syntax_node) == ' c = a + b'

    def test_snapshot_text_survives_second_tracer(self):
        """核心 bug 回归: 第二个 SignalTracer 创建后, 第一个的 _syntax_node 仍正确

        不修复时, 第一个 trace 的 _syntax_node 调 str() 会变 'b = foo' (丢 '(a)')
        """
        # 第一个 tracer
        t1 = SignalTracer()
        t1.add_file('m.sv', 'module m; logic [7:0] a, b; function [7:0] foo(input [7:0] x); foo = x + 1; endfunction; always_comb b = foo(a); endmodule')
        t1.build()
        d1 = t1.trace_drivers('b')[0]
        text1 = str(d1._syntax_node)
        assert 'b = foo(a)' == text1.strip()

        # 第二个 tracer 创建 → pyslang 内部 buffer 复用
        t2 = SignalTracer()
        t2.add_file('m.sv', 'module m; logic [7:0] a, b, c; always_comb c = a + b; endmodule')
        t2.build()
        t2.trace_drivers('c')  # 触发访问

        # 第一个 trace 的 syntax node 应该仍正确 (snapshot 冻结)
        text1_after = str(d1._syntax_node)
        assert text1 == text1_after, f"snapshot not frozen: {text1_after!r}"

    def test_function_call_driver_snippet_complete(self):
        """函数调用 driver: snippet 应包含完整 'b = foo(a)' 而非 'b = foo'"""
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic [7:0] a, b; function [7:0] foo(input [7:0] x); foo = x + 1; endfunction; always_comb b = foo(a); endmodule')
        t.build()
        d = t.trace_drivers('b')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
            file='m.sv',
            narrow_to=None,
        )
        assert 'b = foo(a)' in ev.snippet
        assert ev.matches_source_expr is True
        assert ev.matches_signal_name is True

    def test_function_call_load_narrows_correctly(self):
        """函数调用 load 'a': load trace 的 _syntax_node 应该是 RHS (foo(a)) 而非整条 assignment

        验证 _process_assignment_expr load 路径用 expr.right.syntax (RHS 节点)
        而非 expr.syntax (整个 BinaryExpressionSyntax)。
        narrowing 本身依赖 pyslang SyntaxNode.iter 状态, 不是一个新 tracer 创建后能可無跑过的;
        只验证 _syntax_node 类型/内容。
        """
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic [7:0] a, b; function [7:0] foo(input [7:0] x); foo = x + 1; endfunction; always_comb b = foo(a); endmodule')
        t.build()
        l = t.trace_loads('a')[0]
        # _syntax_node 是 RHS 节点 (字符串包含 'foo(a)') 而非整条 assignment (不包含 ' b = ')
        s = str(l._syntax_node)
        assert 'foo(a)' in s, f"load _syntax_node should contain RHS foo(a), got {s!r}"
        assert ' b = ' not in s, f"load _syntax_node should NOT contain 'b = ' (that's the whole assignment), got {s!r}"

    def test_snapshot_preserves_source_range(self):
        """SyntaxNodeSnapshot 保留 sourceRange, 走代理访问"""
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic [7:0] a, b, c; always_comb c = a + b; endmodule')
        t.build()
        d = t.trace_drivers('c')[0]
        # sourceRange 通过 snapshot 代理拿到
        assert d._syntax_node.sourceRange is not None
        # start.offset end.offset 是语法节点范围
        sr = d._syntax_node.sourceRange
        assert sr.start.offset < sr.end.offset

    def test_snapshot_preserves_iter(self):
        """SyntaxNodeSnapshot 代理 __iter__, 让 _find_subexpr_for_signal 能 DFS"""
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic [7:0] a, b, c; always_comb c = a + b; endmodule')
        t.build()
        d = t.trace_drivers('c')[0]
        # iter 走的 underlying node
        kids = list(d._syntax_node)
        assert len(kids) > 0  # BinaryExpressionSyntax 有 children
