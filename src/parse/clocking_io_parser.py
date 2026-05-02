"""
Clocking IO Parser - 使用正确的 AST 遍历

提取 clocking 输入输出信号：
- ClockingInput
- ClockingOutput
- ClockingBlock

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class ClockingIOSignal:
    name: str = ""
    direction: str = ""  # input, output, inout
    skew: str = ""


@dataclass
class ClockingBlockDef:
    name: str = ""
    clock_event: str = ""
    inputs: List[ClockingIOSignal] = field(default_factory=list)
    outputs: List[ClockingIOSignal] = field(default_factory=list)


class ClockingIOExtractor:
    def __init__(self):
        self.blocks: List[ClockingBlockDef] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ClockingDeclaration':
                cb = ClockingBlockDef()
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
                    
                    sig = ClockingIOSignal()
                    
                    if child_kind == 'ClockingInput':
                        sig.direction = 'input'
                        if hasattr(child, 'name') and child.name:
                            sig.name = str(child.name)
                        if hasattr(child, 'skew') and child.skew:
                            sig.skew = str(child.skew)
                        cb.inputs.append(sig)
                    
                    elif child_kind == 'ClockingOutput':
                        sig.direction = 'output'
                        if hasattr(child, 'name') and child.name:
                            sig.name = str(child.name)
                        if hasattr(child, 'skew') and child.skew:
                            sig.skew = str(child.skew)
                        cb.outputs.append(sig)
                
                if cb.name:
                    self.blocks.append(cb)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': cb.name,
                'clock': cb.clock_event[:30],
                'inputs': [{'name': s.name, 'skew': s.skew} for s in cb.inputs],
                'outputs': [{'name': s.name, 'skew': s.skew} for s in cb.outputs]
            }
            for cb in self.blocks
        ]


def extract_clocking_io(code: str) -> List[Dict]:
    return ClockingIOExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
clocking cb @(posedge clk);
    default input #1step output #2;
    input data;
    input valid;
    output addr;
endclocking
'''
    result = extract_clocking_io(test_code)
    print(f"Clocking blocks: {len(result)}")
