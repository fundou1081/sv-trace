"""
Time Literal Parser - 使用正确的 AST 遍历

提取时间字面量：
- 时间值 (1ns, 2us, 3ms, 4s, etc.)
- TimeUnitDeclaration

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
class TimeLiteral:
    value: str = ""
    unit: str = ""  # ns, us, ms, s, etc.


class TimeLiteralExtractor:
    def __init__(self):
        self.time_literals: List[TimeLiteral] = []
        self.time_units: List[str] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TimeLiteral':
                tl = TimeLiteral()
                if hasattr(node, 'value') and node.value:
                    tl.value = str(node.value)
                if hasattr(node, 'unit') and node.unit:
                    tl.unit = str(node.unit)
                self.time_literals.append(tl)
            
            elif kind_name == 'TimeUnitDeclaration':
                if hasattr(node, 'timeUnit') and node.timeUnit:
                    self.time_units.append(str(node.timeUnit))
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return {
            'time_literals': [{'value': tl.value, 'unit': tl.unit} for tl in self.time_literals],
            'time_units': self.time_units
        }


def extract_time_literals(code: str) -> Dict:
    return TimeLiteralExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
time #10ns, #20ns;
#1us;
#100ms;
'''
    result = extract_time_literals(test_code)
    print(f"Time literals: {len(result['time_literals'])}")
