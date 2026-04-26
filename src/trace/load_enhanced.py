"""
Load Tracer Enhanced - 增强版信号负载追踪器
修复扇出统计不准确的问题
"""
import pyslang
from pyslang import SyntaxKind
from typing import List, Dict, Set, Optional
import re
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.models import Load


class LoadTracerEnhanced:
    """
    增强版信号负载追踪器
    
    改进:
    1. 直接遍历所有always块，不依赖visit callback
    2. 正确追踪信号的读写使用
    3. 支持跨always块的信号统计
    """
    
    def __init__(self, parser):
        self.parser = parser
        self.compilation = parser.compilation
        self._signal_uses: Dict[str, Set[str]] = {}  # signal -> set of using signals
        self._use_contexts: Dict[str, List[Load]] = {}  # signal -> loads
        self._build()
    
    def _build(self):
        """构建信号使用映射"""
        # 首先收集所有信号
        self._all_signals: Set[str] = set()
        self._signal_defs: Dict[str, List[str]] = {}  # signal -> sources
        
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._extract_signals(tree.root)
        
        # 然后分析每个always块的使用
        for key, tree in self.parser.trees.items():
            if not tree or not tree.root:
                continue
            self._analyze_always_blocks(tree.root)
    
    def _extract_signals(self, root):
        """提取所有信号"""
        # 使用正则提取信号声明
        code = ""
        if hasattr(root, 'source') and root.source:
            code = root.source
        elif hasattr(root, 'text') and root.text:
            code = root.text
        
        if code:
            # 提取logic/wire/reg声明的信号
            patterns = [
                r'logic\s*\[[^\]]+\]\s+([a-zA-Z_]\w*)',
                r'logic\s+([a-zA-Z_]\w*)',
                r'wire\s+\[[^\]]+\]\s+([a-zA-Z_]\w*)',
                r'wire\s+([a-zA-Z_]\w*)',
                r'reg\s*\[[^\]]+\]\s+([a-zA-Z_]\w*)',
                r'reg\s+([a-zA-Z_]\w*)',
            ]
            for pattern in patterns:
                for match in re.finditer(pattern, code):
                    self._all_signals.add(match.group(1))
    
    def _analyze_always_blocks(self, root):
        """分析所有always块"""
        def visit(node, depth=0):
            if depth > 50:  # 防止递归过深
                return
            
            kind_name = str(node.kind) if hasattr(node, 'kind') else ''
            
            # 检查always块
            if 'ProceduralBlock' in kind_name or 'Always' in kind_name:
                self._process_procedural_block(node)
            
            # 检查连续赋值
            if kind_name == 'ContinuousAssign':
                self._process_continuous_assign(node)
            
            # 继续遍历子节点
            if hasattr(node, 'members'):
                for i in range(len(node.members)):
                    visit(node.members[i], depth + 1)
            
            # 遍历body/statement等
            for attr in ['body', 'statement', 'statements', 'ifStatement', 'elseStatement']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                if hasattr(c, 'kind'):
                                    visit(c, depth + 1)
                        elif hasattr(child, 'kind'):
                            visit(child, depth + 1)
        
        visit(root)
    
    def _process_procedural_block(self, block):
        """处理过程块"""
        try:
            # 获取块内所有赋值语句的右侧
            self._walk_for_rhs(block, set())
        except Exception as e:
            pass
    
    def _process_continuous_assign(self, assign):
        """处理连续赋值"""
        try:
            if hasattr(assign, 'assignments') and assign.assignments:
                for i in range(len(assign.assignments)):
                    assign_expr = assign.assignments[i]
                    if hasattr(assign_expr, 'right') and assign_expr.right:
                        self._extract_rhs_signals(assign_expr.right)
        except:
            pass
    
    def _walk_for_rhs(self, node, signals: Set[str]):
        """遍历节点提取右侧信号"""
        if node is None:
            return
        
        kind_name = str(node.kind) if hasattr(node, 'kind') else ''
        
        # AssignmentExpression: 左右都有
        if 'AssignmentExpression' in kind_name:
            # 右侧是信号使用
            if hasattr(node, 'right') and node.right:
                self._extract_rhs_signals(node.right)
        
        # IdentifierName: 是信号引用
        if kind_name == 'IdentifierName':
            name = self._get_identifier_name(node)
            if name and name in self._all_signals:
                signals.add(name)
        
        # 遍历子节点
        for attr in ['right', 'expression', 'expr', 'body', 'statement', 'statements']:
            if hasattr(node, attr):
                child = getattr(node, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._walk_for_rhs(c, signals)
                    else:
                        self._walk_for_rhs(child, signals)
    
    def _extract_rhs_signals(self, node):
        """提取右侧所有信号"""
        if node is None:
            return
        
        kind_name = str(node.kind) if hasattr(node, 'kind') else ''
        
        # IdentifierName
        if kind_name == 'IdentifierName':
            name = self._get_identifier_name(node)
            if name:
                if name not in self._signal_uses:
                    self._signal_uses[name] = set()
        
        # 继续遍历
        for attr in dir(node):
            if attr.startswith('_'):
                continue
            try:
                child = getattr(node, attr)
                if child and not callable(child):
                    if isinstance(child, list):
                        for c in child:
                            self._extract_rhs_signals(c)
                    elif hasattr(child, 'kind'):
                        self._extract_rhs_signals(child)
            except:
                pass
    
    def _get_identifier_name(self, node) -> Optional[str]:
        """获取IdentifierName的值"""
        if hasattr(node, 'value'):
            return str(node.value)
        if hasattr(node, 'name'):
            name = node.name
            if hasattr(name, 'value'):
                return str(name.value)
            return str(name)
        return None
    
    def find_load(self, signal_name: str, module_name: str = None) -> List[Load]:
        """查找信号被加载的位置"""
        loads = []
        
        # 从源码中查找
        for key, tree in self.parser.trees.items():
            if not tree:
                continue
            
            code = ""
            if hasattr(tree, 'source') and tree.source:
                code = tree.source
            elif hasattr(key, 'read'):
                try:
                    code = key.read()
                except:
                    continue
            
            if not code:
                continue
            
            # 查找信号在if/case条件中的使用
            # 格式: if (signal_name ...) 或 case (signal_name)
            pattern = rf'(?:if\s*\(\s*{signal_name}|case\s*\(\s*{signal_name})'
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count('\n') + 1
                loads.append(Load(
                    signal_name=signal_name,
                    context=code[max(0, match.start()-20):match.end()+20],
                    line=line_num
                ))
            
            # 查找信号在其他信号的右侧使用
            # 模式: other_sig = ... signal_name ...
            pattern = rf'\w+\s*=\s*[^;]*\b{signal_name}\b'
            for match in re.finditer(pattern, code):
                line_num = code[:match.start()].count('\n') + 1
                loads.append(Load(
                    signal_name=signal_name,
                    context=code[max(0, match.start()-20):match.end()+20],
                    line=line_num
                ))
        
        return loads
    
    def get_fanout(self, signal_name: str) -> int:
        """获取信号的直接扇出"""
        loads = self.find_load(signal_name)
        # 去重统计
        contexts = set()
        for load in loads:
            contexts.add(load.context)
        return len(contexts)
    
    def get_all_fanout(self) -> Dict[str, int]:
        """获取所有信号的扇出"""
        result = {}
        for sig in self._all_signals:
            result[sig] = self.get_fanout(sig)
        return result
    
    def find_high_fanout(self, threshold: int = 10) -> List[tuple]:
        """查找高扇出信号"""
        all_fanout = self.get_all_fanout()
        return [(sig, count) for sig, count in all_fanout.items() 
                if count >= threshold]


# 导出
__all__ = ['LoadTracerEnhanced']
