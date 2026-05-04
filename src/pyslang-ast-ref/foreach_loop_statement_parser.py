"""
Foreach Loop Statement Parser - 使用正确的 AST 遍历

提取 foreach 循环语句：
- ForeachLoopStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ForeachLoopStatement:
    array_name: str = ""
    loop_variables: List[str] = None
    body: str = ""
    
    def __post_init__(self):
        if self.loop_variables is None:
            self.loop_variables = []


class ForeachLoopStatementExtractor:
    def __init__(self):
        self.statements: List[ForeachLoopStatement] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForeachLoopStatement':
                fls = ForeachLoopStatement()
                
                if hasattr(node, 'array') and node.array:
                    fls.array_name = str(node.array)
                
                vars = []
                def get_vars(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Identifier' in kn:
                        vars.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_vars)
                fls.loop_variables = vars[:5]
                
                if hasattr(node, 'body') and node.body:
                    fls.body = str(node.body)[:30]
                
                self.statements.append(fls)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'array': s.array_name, 'vars': s.loop_variables[:3], 'body': s.body[:20]} for s in self.statements]


def extract_foreach_loops(code: str) -> List[Dict]:
    return ForeachLoopStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
foreach (arr[i, j]) begin
end
'''
    result = extract_foreach_loops(test_code)
    print(f"Foreach loops: {len(result)}")
