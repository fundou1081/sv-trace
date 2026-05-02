"""
Gate Instantiation Parser - 使用正确的 AST 遍历

提取门级实例化：
- GateInstantiation

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class GateInstantiation:
    gate_type: str = ""
    instances: List[str] = None
    
    def __post_init__(self):
        if self.instances is None:
            self.instances = []


class GateInstantiationExtractor:
    def __init__(self):
        self.instantiations: List[GateInstantiation] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['GateInstantiation', 'PrimitiveInstantiation']:
                gi = GateInstantiation()
                
                if hasattr(node, 'gate') and node.gate:
                    gi.gate_type = str(node.gate)
                elif hasattr(node, 'type') and node.type:
                    gi.gate_type = str(node.type)
                
                insts = []
                def get_insts(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Instance' in kn:
                        insts.append(str(n)[:30])
                    return pyslang.VisitAction.Advance
                node.visit(get_insts)
                gi.instances = insts[:10]
                
                self.instantiations.append(gi)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': g.gate_type[:20], 'instances': len(g.instances)} for g in self.instantiations]


def extract_gate_instantiations(code: str) -> List[Dict]:
    return GateInstantiationExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
and u1 (out, in1, in2);
'''
    result = extract_gate_instantiations(test_code)
    print(f"Gate instantiations: {len(result)}")
