"""
Clocking Block Parser - 使用正确的 AST 遍历

提取 clocking block：
- ClockingDeclaration (主要)
- ClockingBlock (别名)
- ClockingItem (时钟项)

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClockingSignal:
    name: str = ""
    direction: str = ""
    skew: str = ""


@dataclass
class ClockingBlock:
    name: str = ""
    clock_event: str = ""
    signals: List[ClockingSignal] = field(default_factory=list)
    default_input_skew: str = ""
    default_output_skew: str = ""


class ClockingBlockExtractor:
    def __init__(self):
        self.clocking_blocks: List[ClockingBlock] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # ClockingDeclaration 是主要的语法
            # ClockingBlock 可能作为别名或内部表示
            if kind_name in ['ClockingDeclaration', 'ClockingBlock', 'ClockingItem']:
                cb = self._extract_clocking_block(node)
                if cb:
                    self.clocking_blocks.append(cb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_clocking_block(self, node) -> Optional[ClockingBlock]:
        cb = ClockingBlock()
        
        if hasattr(node, 'name') and node.name:
            cb.name = str(node.name)
        
        if hasattr(node, 'clock') and node.clock:
            cb.clock_event = str(node.clock)
        
        # 遍历子节点
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # ClockingInput, ClockingOutput
            if child_kind in ['ClockingInput', 'ClockingOutput', 'ClockingDirection']:
                sig = ClockingSignal()
                if 'Input' in child_kind:
                    sig.direction = 'input'
                elif 'Output' in child_kind:
                    sig.direction = 'output'
                else:
                    sig.direction = 'inout'
                
                if hasattr(child, 'name') and child.name:
                    sig.name = str(child.name)
                if hasattr(child, 'skew') and child.skew:
                    sig.skew = str(child.skew)
                
                if sig.name:
                    cb.signals.append(sig)
        
        # 默认 skew
        if hasattr(node, 'defaultInputSkew') and node.defaultInputSkew:
            cb.default_input_skew = str(node.defaultInputSkew)
        if hasattr(node, 'defaultOutputSkew') and node.defaultOutputSkew:
            cb.default_output_skew = str(node.defaultOutputSkew)
        
        return cb if cb.name or cb.clock_event else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': cb.name,
                'clock_event': cb.clock_event[:30] if cb.clock_event else '',
                'signals': [{'name': s.name, 'dir': s.direction, 'skew': s.skew} for s in cb.signals],
                'input_skew': cb.default_input_skew,
                'output_skew': cb.default_output_skew
            }
            for cb in self.clocking_blocks
        ]


def extract_clocking_blocks(code: str) -> List[Dict]:
    return ClockingBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
clocking cb @(posedge clk);
    default input #1step output #2;
    input data;
    output addr;
endclocking
'''
    result = extract_clocking_blocks(test_code)
    print(f"Clocking blocks: {len(result)}")
