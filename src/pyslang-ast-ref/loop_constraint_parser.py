"""
Loop Constraint Parser - 使用正确的 AST 遍历

提取循环约束：
- LoopConstraint

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class LoopConstraint:
    loop_variable: str = ""
    count: str = ""
    body: str = ""


class LoopConstraintExtractor:
    def __init__(self):
        self.constraints: List[LoopConstraint] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'LoopConstraint':
                lc = LoopConstraint()
                
                if hasattr(node, 'loopVariable') and node.loopVariable:
                    lc.loop_variable = str(node.loopVariable)[:20]
                
                if hasattr(node, 'count') and node.count:
                    lc.count = str(node.count)[:20]
                
                if hasattr(node, 'constraint') and node.constraint:
                    lc.body = str(node.constraint)[:30]
                
                self.constraints.append(lc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'var': c.loop_variable[:15], 'count': c.count[:15], 'body': c.body[:25]} for c in self.constraints]


def extract_loop_constraints(code: str) -> List[Dict]:
    return LoopConstraintExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c { foreach (arr[i]) arr[i] > 0; }
'''
    result = extract_loop_constraints(test_code)
    print(f"Loop constraints: {len(result)}")
