"""
Jump Statement Parser - 使用正确的 AST 遍历

提取跳转语句：
- JumpStatement
- ReturnStatement
- BreakStatement
- ContinueStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class JumpStatement:
    statement_type: str = ""
    expression: str = ""


class JumpStatementExtractor:
    def __init__(self):
        self.statements: List[JumpStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['JumpStatement', 'ReturnStatement', 'BreakStatement', 
                           'ContinueStatement', 'Return']:
                js = JumpStatement()
                js.statement_type = kind_name.replace('Statement', '').lower()
                
                if hasattr(node, 'expression') and node.expression:
                    js.expression = str(node.expression)[:30]
                
                self.statements.append(js)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'type': s.statement_type, 'expr': s.expression[:25]} for s in self.statements]


def extract_jump_statements(code: str) -> List[Dict]:
    return JumpStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
return 5;
break;
continue;
'''
    result = extract_jump_statements(test_code)
    print(f"Jump statements: {len(result)}")
