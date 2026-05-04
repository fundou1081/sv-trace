"""
Type Assignment Parser - 使用正确的 AST 遍历

提取类型赋值：
- TypeAssignment

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class TypeAssignment:
    name: str = ""
    data_type: str = ""


class TypeAssignmentExtractor:
    def __init__(self):
        self.assignments: List[TypeAssignment] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TypeAssignment':
                ta = TypeAssignment()
                
                if hasattr(node, 'name') and node.name:
                    ta.name = str(node.name)
                
                if hasattr(node, 'dataType') and node.dataType:
                    ta.data_type = str(node.dataType)[:30]
                
                self.assignments.append(ta)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': a.name, 'type': a.data_type[:25]} for a in self.assignments]


def extract_type_assignments(code: str) -> List[Dict]:
    return TypeAssignmentExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
typedef int my_int;
'''
    result = extract_type_assignments(test_code)
    print(f"Type assignments: {len(result)}")
