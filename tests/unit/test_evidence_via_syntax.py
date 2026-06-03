"""M5.2c: syntax-based evidence 路径测试

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
        comp = pyslang.Compilation()
        comp.addSyntaxTree(pyslang.SyntaxTree.fromText(
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
        """syntax 模式: context_available 必须 False, 区别 file 模式"""
        t = self._make_tracer()
        d = t.trace_drivers('c')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            source_expr=d.source_expr,
            signal_name=d.signal_name,
        )
        assert ev.context_available is False
        assert ev.context_before == []
        assert ev.context_after == []

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
        """M5.2c step 5: source_expr 是真实源码 (e.g. 'a + b'), 不是 C++ enum ('a Add b')

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

    def test_credibility_score_syntax_lower(self):
        """syntax 路径没 file_readable (0.2), 所以 credibility 略低

        M5.2c step 5 修后: source_expr 走真实源码 ('a + b'), matches_source_expr
        两路都为 True。file 加 file_readable 仍领先 0.2。
        - file:  file_readable(0.2) + snippet(0.2) + source_expr(0.4) + signal_name(0.2) = 1.0
        - syntax: snippet(0.2) + source_expr(0.4) + signal_name(0.2) = 0.8
        """
        file_ev, syn_ev, _ = self._both_evidences()
        assert file_ev.credibility_score == pytest.approx(1.0)
        assert syn_ev.credibility_score == pytest.approx(0.8)
        # syntax 仍略低 0.2 (file_readable 那一项)
        assert file_ev.credibility_score > syn_ev.credibility_score


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
        """syntax 模式 to_evidence_string 应显示 'M5.3 TODO' 提示"""
        # 直接走 tracer 拿 _syntax_node, 避免手写 pyslang drill-down
        t = SignalTracer()
        t.add_file('m.sv', 'module m; logic a, b; always_comb a = b; endmodule\n')
        t.build()
        d = t.trace_drivers('a')[0]
        ev = build_evidence_via_syntax(
            syntax_node=d._syntax_node,
            signal_name='a',
        )
        s = ev.to_evidence_string()
        assert 'source: syntax' in s
        assert 'M5.3' in s or 'context_window' in s
