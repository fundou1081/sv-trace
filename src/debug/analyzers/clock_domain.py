"""
ClockDomainAnalyzer - 时钟域分析
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class RegisterInfo:
    signal: str
    clock: str
    clock_edge: str
    has_async_reset: bool = False
    reset_signal: str = ""


    def extract_from_text(source: str):
        """从源码文本提取时钟域"""
        import pyslang
        
        try:
            tree = pyslang.SyntaxTree.fromText(source)
            
            class TextParser:
                def __init__(self, tree):
                    self.trees = {"input.sv": tree}
            
            return ClockDomainAnalyzer(TextParser(tree))
        except Exception as e:
            print(f"ClockDomain analyze error: {e}")
            return None

class ClockDomainAnalyzer:
    """时钟域分析器 - 从 AST 直接提取时钟信息"""
    
    def __init__(self, parser):
        self.parser = parser
        self._registers: Dict[str, RegisterInfo] = {}
        self._clock_domains: Dict[str, Set[str]] = defaultdict(set)
        self._analyze()
    
    def _analyze(self):
        """直接遍历 AST 查找 always_ff 块"""
        
        for path, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            if not hasattr(root, 'members'):
                continue
            
            # 遍历根成员 (通常是模块)
            for i in range(len(root.members)):
                member = root.members[i]
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                # 遍历模块成员
                if not hasattr(member, 'members'):
                    continue
                
                for j in range(len(member.members)):
                    mm = member.members[j]
                    
                    # 找到 always_ff 块
                    if 'ProceduralBlock' in str(type(mm)):
                        if self._is_always_ff(mm):
                            # 从 statement 提取时钟
                            clock, edge, rst = self._extract_clock_from_block(mm)
                            
                            # 提取驱动的信号
                            driven = self._extract_driven_signals(mm)
                            
                            for sig in driven:
                                self._registers[sig] = RegisterInfo(
                                    signal=sig,
                                    clock=clock or "unknown",
                                    clock_edge=edge or "posedge",
                                    has_async_reset=(rst is not None),
                                    reset_signal=rst or ""
                                )
                                
                                if clock:
                                    self._clock_domains[clock].add(sig)
    
    def _is_always_ff(self, block) -> bool:
        """检查是否是 always_ff"""
        if not hasattr(block, 'statement'):
            return False
        
        stmt = block.statement
        
        # TimingControlStatement 是 always_ff
        if 'TimingControlStatement' in str(type(stmt)):
            return True
        
        return False
    
    def _extract_clock_from_block(self, block) -> tuple:
        """从 always_ff 块提取时钟 - 从完整 statement 字符串"""
        clock = None
        edge = "posedge"
        reset = None
        
        if not hasattr(block, 'statement'):
            return clock, edge, reset
        
        # 获取完整的 statement 字符串 (包含时钟信息!)
        full_stmt = str(block.statement)
        
        # 从完整 statement 中提取时钟
        # 格式: @(posedge clk) 或 @(posedge clk or negedge rst)
        for match in re.finditer(r'(posedge|negedge)\s+(\w+)', full_stmt, re.IGNORECASE):
            m_edge = match.group(1)
            m_clock = match.group(2)
            if m_edge.lower() == 'posedge':
                clock = m_clock
                edge = "posedge"
            else:
                reset = m_clock
        
        return clock, edge, reset
    
    def _extract_driven_signals(self, block) -> list:
        """提取 always 块驱动的信号"""
        signals = []
        
        if not hasattr(block, 'statement'):
            return signals
        
        stmt = block.statement
        
        # 获取 statement 内部 (跳过 timing control)
        inner_stmt = None
        if hasattr(stmt, 'statement'):
            inner_stmt = stmt.statement
        
        if inner_stmt:
            self._find_assignments(inner_stmt, signals)
        
        return signals
    
    def _find_assignments(self, node, signals):
        """递归查找赋值语句"""
        if not node:
            return
        
        type_name = str(type(node))
        
        # AssignmentStatementSyntax
        if 'AssignmentStatement' in type_name:
            if hasattr(node, 'left') and node.left:
                if hasattr(node.left, 'name'):
                    sig = node.left.name.value if hasattr(node.left.name, 'value') else str(node.left.name)
                    if sig and sig not in signals:
                        signals.append(sig)
        
        # BinaryExpression (e.g., data_a <= 1'b1)
        if 'BinaryExpression' in type_name:
            if hasattr(node, 'left') and node.left:
                left = node.left
                # IdentifierNameSyntax has a 'value' attribute with the signal name
                sig = None
                if hasattr(left, 'value'):
                    sig = left.value
                elif hasattr(left, 'name'):
                    sig = left.name.value if hasattr(left.name, 'value') else str(left.name)
                else:
                    # Direct string representation
                    sig = str(left).strip()
                
                if sig and sig not in signals:
                    signals.append(sig)
        
        # ExpressionStatement (contains an assignment in expr)
        if 'ExpressionStatement' in type_name:
            if hasattr(node, 'expr') and node.expr:
                # expr is the assignment expression
                self._find_assignments(node.expr, signals)
        
        # BlockStatement - has items instead of body
        if 'BlockStatement' in type_name or 'Block' in type_name:
            if hasattr(node, 'items') and node.items:
                for k in range(len(node.items)):
                    self._find_assignments(node.items[k], signals)
        
        # 遍历子节点
        for attr in ['body', 'statement', 'statements', 'ifBody', 'elseBody', 'ifStatement', 'elseStatement']:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_assignments(c, signals)
                    else:
                        self._find_assignments(child, signals)
    
    def get_clock_domain(self, signal: str) -> Optional[str]:
        if signal in self._registers:
            return self._registers[signal].clock
        return None
    
    def get_register_info(self, signal: str) -> Optional[RegisterInfo]:
        return self._registers.get(signal)
    
    def get_all_domains(self) -> List[str]:
        return list(self._clock_domains.keys())
    
    def get_signals_in_domain(self, clock: str) -> List[str]:
        return list(self._clock_domains.get(clock, set()))
    
    def get_all_registers(self) -> Dict[str, RegisterInfo]:
        return self._registers
