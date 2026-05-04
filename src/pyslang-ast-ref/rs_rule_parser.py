"""
RS Rule Parser - 使用正确的 AST 遍历

提取随机化约束规则：
- RsRule
- RsProdItem
- Production

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class RsRule:
    name: str = ""
    expression: str = ""


class RsRuleExtractor:
    def __init__(self):
        self.rules: List[RsRule] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['RsRule', 'RsProdItem', 'Production', 'RsCodeBlock']:
                rr = RsRule()
                rr.name = kind_name
                
                if hasattr(node, 'name') and node.name:
                    rr.name = str(node.name)
                elif hasattr(node, 'constraint') and node.constraint:
                    rr.expression = str(node.constraint)[:30]
                
                self.rules.append(rr)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': r.name[:30], 'expr': r.expression[:30]} for r in self.rules[:20]]


def extract_rs_rules(code: str) -> List[Dict]:
    return RsRuleExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
constraint c1 { x inside {[0:10]}; }
'''
    result = extract_rs_rules(test_code)
    print(f"RS rules: {len(result)}")
