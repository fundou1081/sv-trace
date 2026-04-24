"""
ControlFlowTracer - 控制流分析
追踪信号的控制依赖关系 (if/case/always_ff 条件)
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Driver, Load
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set


@dataclass
class ControlCondition:
    """控制条件"""
    condition_expr: str          # 条件表达式
    signal_name: str            # 被控制的信号
    condition_signals: List[str] = field(default_factory=list)  # 条件中的信号
    statement_type: str = ""    # if/case/always_ff
    line: int = 0


@dataclass 
class ControlFlow:
    """控制流"""
    signal_name: str
    controlling_signals: List[str] = field(default_factory=list)  # 直接控制它的信号
    dependent_signals: List[str] = field(default_factory=list)    # 它控制的信号
    conditions: List[ControlCondition] = field(default_factory=list)
    
    def visualize(self) -> str:
        lines = ["=== Control Flow Analysis ==="]
        lines.append(f"Signal: {self.signal_name}")
        
        if self.controlling_signals:
            lines.append(f"\n[Controlling Signals] ({len(self.controlling_signals)})")
            for s in sorted(self.controlling_signals):
                lines.append(f"  - {s}")
        
        if self.dependent_signals:
            lines.append(f"\n[Dependent Signals] ({len(self.dependent_signals)})")
            for s in sorted(self.dependent_signals):
                lines.append(f"  - {s}")
        
        if self.conditions:
            lines.append(f"\n[Conditions] ({len(self.conditions)})")
            for c in self.conditions:
                lines.append(f"  [{c.statement_type}] {c.condition_expr[:60].strip()}")
                if c.condition_signals:
                    lines.append(f"    → signals: {c.condition_signals}")
        
        return "\n".join(lines)


class ControlFlowTracer:
    """控制流分析器"""
    
    def __init__(self, parser):
        self.parser = parser
        self._all_signals = self._collect_all_signals()
    
    def _collect_all_signals(self) -> Set[str]:
        """收集所有信号名"""
        signals = set()
        
        for tree in self.parser.trees.values():
            if not tree or not hasattr(tree, 'root'):
                continue
            
            root = tree.root
            members = getattr(root, 'members', None)
            if not members:
                continue
            
            for i in range(len(members)):
                member = members[i]
                
                if 'ModuleDeclaration' not in str(type(member)):
                    continue
                
                mod_members = getattr(member, 'members', None)
                if not mod_members:
                    continue
                
                for j in range(len(mod_members)):
                    mm = mod_members[j]
                    
                    if 'DataDeclaration' not in str(type(mm)):
                        continue
                    
                    declarators = getattr(mm, 'declarators', None)
                    if declarators:
                        try:
                            for decl in declarators:
                                if hasattr(decl, 'name'):
                                    name = decl.name.value if hasattr(decl.name, 'value') else str(decl.name)
                                    signals.add(name)
                        except TypeError:
                            pass
        
        return signals
    
    def find_control_dependencies(self, signal_name: str, module_name: str = None) -> ControlFlow:
        """查找信号的控制依赖"""
        
        # 1. 找到信号的驱动
        from .driver import DriverTracer
        driver_tracer = DriverTracer(self.parser)
        drivers = driver_tracer.get_drivers(signal_name)
        
        # 2. 分析每个驱动中的条件
        controlling_signals = set()
        conditions = []
        
        for driver in drivers:
            if driver.kind.name in ['AlwaysFF', 'AlwaysComb', 'AlwaysLatch']:
                # 从完整语句提取所有信号（排除目标信号）
                all_signals = self._extract_signals_from_expr(" ".join(driver.sources))
                # 过滤掉目标信号
                valid_signals = [s for s in all_signals if s in self._all_signals and s != signal_name]
                
                controlling_signals.update(valid_signals)
                
                # 提取条件信号（if 条件、case 条件等）
                cond_signals = self._extract_condition_signals(" ".join(driver.sources), signal_name)
                cond_signals = [s for s in cond_signals if s in self._all_signals and s != signal_name]
                
                conditions.append(ControlCondition(
                    condition_expr=" ".join(driver.sources),
                    signal_name=signal_name,
                    condition_signals=list(set(cond_signals)),  # 去重
                    statement_type=driver.kind.name,
                    line=driver.lines[0] if driver.lines else 0
                ))
        
        # 3. 查找该信号控制的信号
        from .load import LoadTracer
        load_tracer = LoadTracer(self.parser)
        loads = load_tracer.find_load(signal_name, module_name)
        
        dependent_signals = [load.signal_name for load in loads if load.signal_name != signal_name]
        
        return ControlFlow(
            signal_name=signal_name,
            controlling_signals=list(controlling_signals),
            dependent_signals=dependent_signals,
            conditions=conditions
        )
    
    def _extract_condition_signals(self, expr: str, target_signal: str) -> List[str]:
        """从表达式中提取条件信号（if 条件、case 条件等）"""
        if not expr:
            return []
        
        signals = set()
        
        # 1. 提取 if 条件 if (condition)
        if_pattern = r'if\s*\(([^)]+)\)'
        for match in re.finditer(if_pattern, expr):
            condition = match.group(1)
            signals.update(self._extract_signals_from_expr(condition))
        
        # 2. 提取 case 条件 case (expr)
        case_pattern = r'case\s*\(([^)]+)\)'
        for match in re.finditer(case_pattern, expr):
            condition = match.group(1)
            signals.update(self._extract_signals_from_expr(condition))
        
        # 3. 提取 ternary 条件 a ? b : c -> 条件是 a
        # 找到所有 ? 前面部分
        for match in re.finditer(r'([^?]+)\?', expr):
            condition = match.group(1).strip()
            # 取最后一部分（避免匹配到赋值等）
            if '(' in condition:
                # 提取最内层的括号内容
                signals.update(self._extract_signals_from_expr(condition))
        
        return list(signals)
    
    def _extract_signals_from_expr(self, expr: str) -> List[str]:
        """从表达式中提取信号名"""
        if not expr:
            return []
        
        signals = []
        
        # 关键词 - 排除
        keywords = {
            'if', 'else', 'case', 'endcase', 'begin', 'end',
            'for', 'while', 'do', 'repeat', 'always', 'assign',
            'module', 'endmodule', 'input', 'output', 'inout',
            'wire', 'reg', 'logic', 'supply0', 'supply1',
            'posedge', 'negedge', 'or', 'and', 'not', 'xor',
            'new', 'null', 'this', 'super', 'return',
            'default', 'then', 'else', 'endcase',
            'always_ff', 'always_comb', 'always_latch',
            'posedge', 'negedge', 'clk', 'rst',
        }
        
        # 匹配标识符
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        
        for match in re.finditer(pattern, expr):
            name = match.group()
            # 排除关键字和数字开头的
            if name not in keywords and not name[0].isdigit() and not name.startswith("'"):
                signals.append(name)
        
        return signals
    
    def find_all_control_signals(self, signal_name: str, max_depth: int = 3) -> List[Dict]:
        """递归查找所有控制信号链"""
        chain = []
        visited = set()
        
        def dfs(signal, depth):
            if depth > max_depth or signal in visited:
                return
            
            visited.add(signal)
            
            flow = self.find_control_dependencies(signal)
            
            for ctrl_sig in flow.controlling_signals:
                chain.append({
                    "signal": signal,
                    "controls": ctrl_sig,
                    "depth": depth
                })
                dfs(ctrl_sig, depth + 1)
        
        dfs(signal_name, 0)
        
        return chain
    
    def visualize_control_flow(self, signal_name: str) -> str:
        """生成可读的控制流描述"""
        flow = self.find_control_dependencies(signal_name)
        return flow.visualize()
