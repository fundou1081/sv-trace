"""
semantic_ast 实验模块

用于验证 Semantic AST 的关键设计假设：
1. 如何在语义节点中内聚 scope/type/driver 信息
2. 如何用 pyslang Compilation 做符号消歧
3. 如何正确提取驱动源表达式 (而非 lhs)
4. generate 展开后的语义建图
"""

import pyslang
from pyslang import (
    SyntaxTree, SyntaxKind, SyntaxPrinter, Compilation,
    Lookup, LookupFlags, LookupLocation,
    TokenKind
)
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


# =============================================================================
# 语义节点类型定义 (实验性)
# =============================================================================

class SemanticNodeKind(Enum):
    """语义节点类型"""
    MODULE = "module"
    INTERFACE = "interface"
    PACKAGE = "package"
    SIGNAL = "signal"
    INSTANCE = "instance"
    ALWAYS_FF = "always_ff"
    ALWAYS_COMB = "always_comb"
    CONTINUOUS_ASSIGN = "continuous_assign"
    PORT_INPUT = "port_input"
    PORT_OUTPUT = "port_output"


@dataclass
class SemanticSignalNode:
    """语义信号节点
    
    替代传统的 (signal_name + ScopeTree + SymbolTable) 三元组
    所有信号相关的语义信息都内聚在这个节点里
    """
    name: str                          # 原始名称
    resolved_name: str = ""           # 解析后的完整名称 (含层级)
    scope_id: str = ""                 # 所在作用域 ID
    
    # 类型信息
    data_type: str = "logic"
    width: int = 1
    is_signed: bool = False
    dimensions: List[str] = field(default_factory=list)
    
    # 端口方向 (如果是端口)
    port_direction: Optional[str] = None  # input, output, inout
    
    # 驱动关系 (内聚化)
    drivers: List['SemanticDriverRef'] = field(default_factory=list)
    
    # 负载关系 (内聚化)
    loads: List['SemanticLoadRef'] = field(default_factory=list)
    
    # 置信度
    confidence: str = "high"
    caveats: List[str] = field(default_factory=list)
    
    def add_driver(self, driver: 'SemanticDriverRef'):
        self.drivers.append(driver)
    
    def add_load(self, load: 'SemanticLoadRef'):
        self.loads.append(load)


@dataclass
class SemanticDriverRef:
    """语义驱动引用"""
    source_expr: str = ""              # 驱动源表达式 (完整字符串)
    source_node: Optional[Any] = None  # 指向语义节点的引用
    kind: str = ""                     # always_ff, always_comb, continuous
    clock: str = ""
    reset: str = ""
    line: int = 0


@dataclass
class SemanticLoadRef:
    """语义负载引用"""
    load_expr: str = ""                # 负载表达式
    load_node: Optional[Any] = None
    context: str = ""                  # always_comb, assign 等
    line: int = 0


@dataclass
class SemanticScopeNode:
    """语义作用域节点"""
    scope_id: str
    kind: str                          # module, always_ff, generate_for 等
    name: str = ""
    hierarchy_path: str = ""
    parent_scope: Optional[str] = None
    signals: Dict[str, SemanticSignalNode] = field(default_factory=dict)
    children: List[str] = field(default_factory=list)  # 子作用域 IDs


@dataclass
class SemanticAST:
    """语义 AST 图
    
    替代 SemanticGraph + ScopeTree + SymbolTable 的分离架构
    """
    scopes: Dict[str, SemanticScopeNode] = field(default_factory=dict)
    signals: Dict[str, SemanticSignalNode] = field(default_factory=dict)  # 全局信号池
    
    def get_signal(self, name: str) -> Optional[SemanticSignalNode]:
        return self.signals.get(name)
    
    def add_signal(self, sig: SemanticSignalNode):
        self.signals[sig.name] = sig


# =============================================================================
# 辅助函数
# =============================================================================

def _node_to_json(node) -> dict:
    """将节点转为 dict (通过 to_json)"""
    try:
        return json.loads(node.to_json())
    except:
        return {}


def _get_expr_text(expr_node) -> str:
    """从表达式节点提取完整文本
    
    使用 to_json 方式获取 text。
    注意: to_json 会遍历整个子树，对于大型设计可能有效率问题。
    """
    node_json = _node_to_json(expr_node)
    return node_json.get('text', '') or ''


# =============================================================================
# 实验 1: 提取驱动源表达式 (非 lhs)
# =============================================================================

def experiment_driver_source():
    """实验 1: 验证能否正确提取驱动源表达式"""
    print("\n" + "="*60)
    print("实验 1: 提取驱动源表达式")
    print("="*60)
    
    sv_code = '''
module test;
  logic [7:0] a, b, c;
  always_ff @(posedge clk) begin
    a <= b;
    b <= c;
    c <= 8'h0;
  end
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    # 深度遍历，找 NonblockingAssignmentExpression
    results = []
    
    def find_assignments(node, depth=0):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'NonblockingAssignmentExpression':
            # 提取 lhs 和 rhs
            lhs = ""
            rhs = ""
            
            for child in node:
                ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                if ckn == 'IdentifierName':
                    if not lhs:
                        lhs = child.text
                    else:
                        rhs = child.text
                elif ckn == 'IntegerLiteral':
                    rhs = child.text
                elif ckn == 'ScopedName':
                    rhs = child.text
            
            results.append({
                'lhs': lhs,
                'rhs': rhs,
                'text': node.text[:60].replace('\n', ' ')
            })
        
        try:
            for child in node:
                find_assignments(child, depth+1)
        except:
            pass
    
    find_assignments(tree.root)
    
    print("\n结果 (NonblockingAssignmentExpression):")
    for r in results:
        print(f"  LHS={r['lhs']!r:10} RHS={r['rhs']!r:10}  ({r['text']})")
    
    print("\n关键发现: 当前只能取第一个 IdentifierName，复合表达式需要递归遍历 RHS")


def experiment_scoped_name():
    """实验 2: ScopedName 结构"""
    print("\n" + "="*60)
    print("实验 2: ScopedName 结构")
    print("="*60)
    
    sv_code = '''
module top;
  logic [7:0] data;
  always_comb data = pkg::shared_data + 1;
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_scoped(node, depth=0):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'ScopedName':
            print(f"\nFound ScopedName:")
            print(f"  text: {node.text!r}")
            print(f"  to_json text: {_get_expr_text(node)!r}")
            for i, child in enumerate(node):
                ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                ctxt = child.text if hasattr(child, 'text') else ''
                print(f"  [{i}] {ckn}: {ctxt!r}")
        
        try:
            for child in node:
                find_scoped(child, depth+1)
        except:
            pass
    
    find_scoped(tree.root)


def experiment_generate_structure():
    """实验 3: Generate 块结构"""
    print("\n" + "="*60)
    print("实验 3: Generate 块结构")
    print("="*60)
    
    sv_code = '''
module gen_test;
  generate
    for (genvar i = 0; i < 2; i++) begin : GEN
      logic [7:0] tmp;
      always_ff @(posedge clk) begin
        tmp <= 8'h0;
      end
    end
  endgenerate
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_gen(node, depth=0, max_depth=10):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'LoopGenerate':
            print(f"\nFound LoopGenerate:")
            print(f"  text (first 80): {node.text[:80].replace(chr(10), ' ')!r}")
            print(f"  children:")
            for i, child in enumerate(node):
                ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                ctxt = child.text[:40].replace(chr(10), ' ') if hasattr(child, 'text') else ''
                print(f"    [{i}] {ckn}: {ctxt!r}")
        
        if depth < max_depth:
            try:
                for child in node:
                    find_gen(child, depth+1, max_depth)
            except:
                pass
    
    find_gen(tree.root)


def experiment_compilation_semantic():
    """实验 4: Compilation 的语义层能力"""
    print("\n" + "="*60)
    print("实验 4: Compilation 语义层")
    print("="*60)
    
    sv_code = '''
package pkg;
  logic [7:0] shared_data;
endpackage

module sub (
    input  logic [7:0] in,
    output logic [7:0] out
);
  assign out = in;
endmodule

module top;
  logic [7:0] data;
  sub u_sub (.in(data), .out());
  always_comb data = pkg::shared_data;
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    comp = Compilation()
    comp.addSyntaxTree(tree)
    comp.freeze()
    
    print(f"isElaborated: {comp.isElaborated}")
    print(f"isFinalized: {comp.isFinalized}")
    print(f"hasFatalErrors: {comp.hasFatalErrors}")
    
    root = comp.getRoot()
    print(f"\ngetRoot type: {type(root).__name__}")
    
    if hasattr(root, 'members'):
        print(f"root.members count: {len(root.members)}")
        for i, m in enumerate(root.members):
            mname = type(m).__name__
            print(f"  [{i}] {mname}")
    
    pkg = comp.getPackage('pkg')
    print(f"\ngetPackage('pkg'): {type(pkg).__name__ if pkg else None}")
    
    if pkg:
        print(f"  pkg.members: {[type(m).__name__ for m in getattr(pkg, 'members', [])]}")


def experiment_assignment_expression():
    """实验 5: AssignmentExpression 内部结构"""
    print("\n" + "="*60)
    print("实验 5: AssignmentExpression 结构")
    print("="*60)
    
    sv_code = '''
module test;
  logic [7:0] a, b;
  assign a = b + 1;
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_assign(node):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'AssignmentExpression':
            print(f"\nFound AssignmentExpression:")
            print(f"  to_json text: {_get_expr_text(node)!r}")
            print(f"  direct attrs:")
            for attr in dir(node):
                if attr.startswith('_'):
                    continue
                val = getattr(node, attr, None)
                if val is None or callable(val):
                    continue
                val_str = str(val)[:50] if not isinstance(val, (int, str, bool)) else str(val)
                print(f"    {attr}: {val_str}")
        
        try:
            for child in node:
                find_assign(child)
        except:
            pass
    
    find_assign(tree.root)


def experiment_identifier_resolution():
    """实验 6: 标识符解析"""
    print("\n" + "="*60)
    print("实验 6: 标识符解析")
    print("="*60)
    
    sv_code = '''
module top;
  logic [7:0] data;
  logic [7:0] out;
  sub u_sub (.in(data), .out(out));
endmodule

module sub (
    input  logic [7:0] in,
    output logic [7:0] out
);
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_hier_inst(node):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'HierarchyInstantiation':
            print(f"\nFound HierarchyInstantiation:")
            print(f"  text: {node.text[:80].replace(chr(10), ' ')!r}")
            for attr in ['moduleName', 'instances', 'parameterAssignments', 'portConnections']:
                if hasattr(node, attr):
                    val = getattr(node, attr)
                    print(f"  {attr}: {val}")
        
        try:
            for child in node:
                find_hier_inst(child)
        except:
            pass
    
    find_hier_inst(tree.root)


def experiment_clock_in_always():
    """实验 7: 从 always_ff 提取时钟"""
    print("\n" + "="*60)
    print("实验 7: always_ff 时钟提取")
    print("="*60)
    
    sv_code = '''
module test;
  logic clk, rst_n;
  logic [7:0] data;
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n)
      data <= 8'h0;
    else
      data <= data + 1;
  end
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_always(node):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'AlwaysFFBlock':
            print(f"\nFound AlwaysFFBlock:")
            
            if hasattr(node, 'statement'):
                timing = node.statement
                print(f"  timing (statement): {type(timing).__name__}")
                print(f"  timing text: {timing.text[:60].replace(chr(10), ' ')!r}")
                
                def find_clocks(n, depth=0):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'SignalEvent' in kn:
                        print(f"    SignalEvent: {n.text!r}")
                    try:
                        for child in n:
                            find_clocks(child, depth+1)
                    except:
                        pass
                
                find_clocks(timing)
        
        try:
            for child in node:
                find_always(child)
        except:
            pass
    
    find_always(tree.root)


def experiment_expression_rhs():
    """实验 8: 提取复合 RHS 表达式"""
    print("\n" + "="*60)
    print("实验 8: 复合 RHS 表达式提取")
    print("="*60)
    
    sv_code = '''
module test;
  logic [7:0] a, b, c;
  logic [7:0] out;
  always_comb out = (a + b) * c;
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def find_rhs_expr(node, depth=0):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kind_name == 'AssignmentExpression':
            print(f"\nFound AssignmentExpression:")
            
            # 用 to_json 获取文本
            node_json = _node_to_json(node)
            full_text = node_json.get('text', '')
            print(f"  Full text from to_json: {full_text!r}")
            
            # 找到 Equals 的位置，然后取 RHS
            children = list(node)
            eq_idx = None
            for i, child in enumerate(children):
                ckn = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
                if ckn == 'Equals':
                    eq_idx = i
                    break
            
            if eq_idx is not None:
                # 收集 Equals 之后的所有表达式
                rhs_nodes = children[eq_idx+1:]
                rhs_text = _get_expr_text(node).split('=')[-1].strip() if '=' in _get_expr_text(node) else ''
                print(f"  RHS text (split): {rhs_text!r}")
            
            return
        
        try:
            for child in node:
                find_rhs_expr(child, depth+1)
        except:
            pass
    
    find_rhs_expr(tree.root)


def experiment_rhs_collector():
    """实验 9: 收集完整的 RHS 表达式"""
    print("\n" + "="*60)
    print("实验 9: 收集完整 RHS 表达式")
    print("="*60)
    
    sv_code = '''
module test;
  logic [7:0] a, b, c;
  logic [7:0] out;
  always_comb out = (a + b) * c + 1;
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def collect_rhs(node, collecting=False, result=None):
        if result is None:
            result = []
        
        kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kn == 'Equals':
            collecting = True
            return collecting, result
        
        if collecting:
            txt = getattr(node, 'text', '') or ''
            kn_str = kn or ''
            # 跳过纯结构节点
            if txt and kn_str not in ('SyntaxList', 'SeparatedList', 'TokenList'):
                result.append(txt)
        
        try:
            for child in node:
                collecting, result = collect_rhs(child, collecting, result)
        except:
            pass
        
        return collecting, result
    
    _, rhs_parts = collect_rhs(tree.root)
    print(f"RHS tokens: {rhs_parts}")
    print(f"RHS joined: {' '.join(rhs_parts)!r}")


def _get_identifier_text(node) -> str:
    """从 IdentifierNameSyntax 节点提取标识符文本"""
    if node is None:
        return ''
    ident = getattr(node, 'identifier', None)
    if ident is None:
        return getattr(node, 'text', '') or ''
    return getattr(ident, 'valueText', '') or ''


def _collect_expr_identifiers(node, result: List[str], _visited=None):
    """递归收集表达式中的所有标识符和字面量
    
    关键发现:
    - AssignmentExpression / NonblockingAssignmentExpression 有 .left / .right 属性
    - IdentifierNameSyntax 有 .identifier.valueText
    - IntegerVectorExpression 有 .value.valueText (Token 类型)
    - 二元表达式有 .left / .right / .expression 属性
    """
    if node is None:
        return
    if _visited is None:
        _visited = set()
    
    node_id = id(node)
    if node_id in _visited:
        return
    _visited.add(node_id)
    
    kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
    
    # 标识符节点
    if kn == 'IdentifierName':
        txt = _get_identifier_text(node)
        if txt:
            result.append(txt)
        return
    
    # IntegerLiteral (Token)
    elif kn == 'IntegerLiteral':
        txt = getattr(node, 'text', '') or ''
        if txt:
            result.append(txt)
        return
    
    # IntegerVectorExpression (like 8'hFF)
    elif kn == 'IntegerVectorExpression':
        val = getattr(node, 'value', None)
        if val and hasattr(val, 'valueText'):
            result.append(val.valueText)
        return
    
    # IntegerLiteralExpression (literal expression wrapper)
    elif kn == 'IntegerLiteralExpression':
        lit = getattr(node, 'literal', None)
        if lit:
            txt = getattr(lit, 'valueText', '') or getattr(lit, 'text', '') or ''
            if txt:
                result.append(txt)
        return
    
    # 二元表达式 (AddExpression, MultiplyExpression 等)
    # ParenthesizedExpression 有 .expression 属性
    elif any(hasattr(node, p) for p in ['left', 'right', 'expression', 'operand']):
        for prop in ['left', 'right', 'expression', 'operand']:
            sub = getattr(node, prop, None)
            if sub is not None:
                _collect_expr_identifiers(sub, result, _visited)
        return
    
    # 继续遍历子节点
    try:
        for child in node:
            _collect_expr_identifiers(child, result, _visited)
    except:
        pass


def experiment_rhs_with_properties():
    """实验 11: 使用 left/right 属性提取 RHS (关键发现)"""
    print("\n" + "="*60)
    print("实验 11: 使用 left/right 属性提取 RHS")
    print("="*60)
    
    sv_code = '''
module test;
  logic [7:0] a, b, c;
  always_ff @(posedge clk) begin
    a <= b;
    b <= a + b;
    c <= (a + b) * 2;
  end
endmodule
'''
    
    tree = SyntaxTree.fromText(sv_code)
    
    def extract_drivers(node):
        kn = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        
        if kn in ('NonblockingAssignmentExpression', 'AssignmentExpression'):
            left = getattr(node, 'left', None)
            right = getattr(node, 'right', None)
            
            lhs_name = _get_identifier_text(left)
            
            rhs_parts = []
            if right:
                _collect_expr_identifiers(right, rhs_parts)
            
            print(f"  LHS={lhs_name!r:8} <- RHS={rhs_parts}")
        
        try:
            for child in node:
                extract_drivers(child)
        except:
            pass
    
    extract_drivers(tree.root)
    print("\n结论: 使用 .left/.right + .identifier.valueText + .value.valueText + 递归遍历二元表达式")
    print("      pyslang 的赋值表达式直接支持 left/right 属性，不需要自己解析语法树")


# =============================================================================
# 主实验入口
# =============================================================================

def run_all_experiments():
    """运行所有实验"""
    experiments = [
        experiment_driver_source,
        experiment_scoped_name,
        experiment_generate_structure,
        experiment_compilation_semantic,
        experiment_assignment_expression,
        experiment_identifier_resolution,
        experiment_clock_in_always,
        experiment_expression_rhs,
        experiment_rhs_collector,
        experiment_rhs_with_properties,
    ]
    
    for exp in experiments:
        try:
            exp()
        except Exception as e:
            print(f"\n实验 {exp.__name__} 出错: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    run_all_experiments()