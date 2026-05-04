"""
Timing Control Expression Parser - 使用正确的 AST 遍历

提取时序控制表达式：
- TimingControlExpression

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TimingControlExpression:
    timing_control: str = ""
    expression: str = ""


class TimingControlExpressionExtractor:
    def __init__(self):
        self.expressions: List[TimingControlExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TimingControlExpression':
                tce = TimingControlExpression()
                if hasattr(node, 'timingControl') and node.timingControl:
                    tce.timing_control = str(node.timingControl)[:30]
                if hasattr(node, 'expression') and node.expression:
                    tce.expression = str(node.expression)[:30]
                self.expressions.append(tce)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'timing': t.timing_control[:30], 'expr': t.expression[:30]} for t in self.expressions[:20]]


def extract_timing_controls(code: str) -> List[Dict]:
    return TimingControlExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
##5 data_valid;
'''
    result = extract_timing_controls(test_code)
    print(f"Timing controls: {len(result)}")
