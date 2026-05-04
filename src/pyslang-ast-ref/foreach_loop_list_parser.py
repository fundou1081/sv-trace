"""
Foreach Loop List Parser - 使用正确的 AST 遍历

提取 foreach 循环列表：
- ForeachLoopList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ForeachLoopList:
    array_name: str = ""
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = []


class ForeachLoopListExtractor:
    def __init__(self):
        self.lists: List[ForeachLoopList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForeachLoopList':
                fll = ForeachLoopList()
                
                if hasattr(node, 'array') and node.array:
                    fll.array_name = str(node.array)
                
                vars = []
                def get_vars(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Identifier' in kn:
                        vars.append(str(n))
                    return pyslang.VisitAction.Advance
                node.visit(get_vars)
                fll.variables = vars[:5]
                
                self.lists.append(fll)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'array': l.array_name, 'vars': l.variables[:5]} for l in self.lists]


def extract_foreach_lists(code: str) -> List[Dict]:
    return ForeachLoopListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
foreach (arr[i, j]) begin
end
'''
    result = extract_foreach_lists(test_code)
    print(f"Foreach lists: {len(result)}")
