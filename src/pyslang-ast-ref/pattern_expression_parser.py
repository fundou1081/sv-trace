"""
Pattern Expression Parser - 使用正确的 AST 遍历

提取模式表达式：
- ExpressionPattern
- VariablePattern
- StructurePattern
- TaggedPattern

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class PatternExpression:
    pattern_type: str = ""
    expression: str = ""


class PatternExpressionExtractor:
    def __init__(self):
        self.expressions: List[PatternExpression] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ExpressionPattern', 'VariablePattern', 'StructurePattern',
                           'TaggedPattern', 'OrderedStructurePatternMember']:
                pe = PatternExpression()
                pe.pattern_type = kind_name.replace('Pattern', '').replace('Member', '')
                
                if hasattr(node, 'expression') and node.expression:
                    pe.expression = str(node.expression)[:30]
                elif hasattr(node, 'variable') and node.variable:
                    pe.expression = str(node.variable)[:30]
                
                self.expressions.append(pe)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': e.pattern_type, 'expr': e.expression[:25]} for e in self.expressions[:20]]


def extract_pattern_expressions(code: str) -> List[Dict]:
    return PatternExpressionExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
var s;
with (s.field);
'''
    result = extract_pattern_expressions(test_code)
    print(f"Pattern expressions: {len(result)}")
