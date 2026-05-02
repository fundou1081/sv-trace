"""
Parameter Value Assignment Parser - 使用正确的 AST 遍历

提取参数值赋值：
- ParameterValueAssignment

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
class ParameterValueAssignment:
    parameters: List[str] = field(default_factory=list)


class ParameterValueAssignmentExtractor:
    def __init__(self):
        self.assignments: List[ParameterValueAssignment] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParameterValueAssignment':
                pva = ParameterValueAssignment()
                
                if hasattr(node, 'parameters') and node.parameters:
                    for p in node.parameters:
                        pva.parameters.append(str(p)[:30])
                elif hasattr(node, 'values') and node.values:
                    for v in node.values:
                        pva.parameters.append(str(v)[:30])
                
                self.assignments.append(pva)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'params': p.parameters} for p in self.assignments]


def extract_param_values(code: str) -> List[Dict]:
    return ParameterValueAssignmentExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
defines #(.WIDTH(8), .DEPTH(16))
'''
    result = extract_param_values(test_code)
    print(f"Parameter value assignments: {len(result)}")
