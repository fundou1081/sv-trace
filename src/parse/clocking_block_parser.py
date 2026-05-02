"""
Clocking Block Parser - 使用正确的 AST 遍历

提取 clocking block：
- clocking 声明
- clocking event
- input/output signals
- default setup/hold timing

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
    direction: str = ""  # input, output, inout
    timing: str = ""  # ##delay, etc.


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
            
            if kind_name == 'ClockingDeclaration':
                cb = self._extract_clocking_block(node)
                if cb:
                    self.clocking_blocks.append(cb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_clocking_block(self, node) -> Optional[ClockingBlock]:
        cb = ClockingBlock()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            cb.name = str(node.name)
        
        # 时钟事件
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
            
            # 信号声明
            if child_kind in ['ClockingInput', 'ClockingOutput', 'ClockingInout']:
                sig = ClockingSignal()
                sig.direction = child_kind.replace('Clocking', '').lower()
                
                if hasattr(child, 'name') and child.name:
                    sig.name = str(child.name)
                if hasattr(child, 'skew') and child.skew:
                    sig.timing = str(child.skew)
                
                cb.signals.append(sig)
        
        # 默认 skew
        if hasattr(node, 'defaultInputSkew') and node.defaultInputSkew:
            cb.default_input_skew = str(node.defaultInputSkew)
        if hasattr(node, 'defaultOutputSkew') and node.defaultOutputSkew:
            cb.default_output_skew = str(node.defaultOutputSkew)
        
        return cb if cb.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': cb.name,
                'clock_event': cb.clock_event,
                'signals': [{'name': s.name, 'dir': s.direction, 'timing': s.timing} for s in cb.signals],
                'input_skew': cb.default_input_skew,
                'output_skew': cb.default_output_skew
            }
            for cb in self.clocking_blocks
        ]


def extract_clocking_blocks(code: str) -> List[Dict]:
    return ClockingBlockExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    clocking cb @(posedge clk);
        default input #1step output #2;
        input data;
        output addr;
        inout ready;
    endclocking
endmodule
'''
    result = extract_clocking_blocks(test_code)
    for item in result:
        print(f"Clocking: {item['name']}")
        print(f"  Clock: {item['clock_event']}")
        for sig in item['signals']:
            print(f"  {sig['dir']}: {sig['name']} {sig['timing']}")
