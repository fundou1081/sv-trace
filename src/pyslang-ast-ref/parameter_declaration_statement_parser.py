"""
Parameter Declaration Statement Parser - 使用正确的 AST 遍历

提取参数声明语句：
- ParameterDeclarationStatement

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ParamDeclStmt:
    name: str = ""
    data_type: str = ""
    default: str = ""


class ParameterDeclarationStatementExtractor:
    def __init__(self):
        self.statements: List[ParamDeclStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParameterDeclarationStatement':
                pds = ParamDeclStmt()
                if hasattr(node, 'name') and node.name:
                    pds.name = str(node.name)
                if hasattr(node, 'dataType') and node.dataType:
                    pds.data_type = str(node.dataType)[:20]
                if hasattr(node, 'defaultValue') and node.defaultValue:
                    pds.default = str(node.defaultValue)[:20]
                self.statements.append(pds)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': s.name, 'type': s.data_type[:20], 'default': s.default[:20]} for s in self.statements]


def extract_param_decl_statements(code: str) -> List[Dict]:
    return ParameterDeclarationStatementExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
parameter WIDTH = 8;
'''
    result = extract_param_decl_statements(test_code)
    print(f"Parameter declarations: {len(result)}")
