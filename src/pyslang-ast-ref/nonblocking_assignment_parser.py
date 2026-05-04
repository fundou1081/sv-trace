"""
Nonblocking Assignment Parser - 使用正确的 AST 遍历

提取非阻塞赋值：
- NonblockingAssignmentExpression

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class NonblockingAssignment:
    target: str = ""
    value: str = ""


class NonblockingAssignmentExtractor:
    def __init__(self):
        self.assignments: List[NonblockingAssignment] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'NonblockingAssignmentExpression':
                nba = NonblockingAssignment()
                if hasattr(node, 'left') and node.left:
                    nba.target = str(node.left)
                if hasattr(node, 'right') and node.right:
                    nba.value = str(node.right)[:30]
                self.assignments.append(nba)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'target': a.target[:30], 'value': a.value[:30]} for a in self.assignments[:20]]


def extract_nonblocking(code: str) -> List[Dict]:
    return NonblockingAssignmentExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always @(posedge clk) begin
    q <= d;
end
'''
    result = extract_nonblocking(test_code)
    print(f"Nonblocking assignments: {len(result)}")
