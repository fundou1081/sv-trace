"""
Module Keyword Parser - 使用正确的 AST 遍历

提取 module 相关关键字：
- ModuleKeyword
- EndModuleKeyword

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ModuleKeyword:
    keyword: str = ""


class ModuleKeywordExtractor:
    def __init__(self):
        self.keywords: List[ModuleKeyword] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['ModuleKeyword', 'EndModuleKeyword', 'InterfaceKeyword', 
                           'EndInterfaceKeyword', 'ProgramKeyword', 'EndProgramKeyword',
                           'PackageKeyword', 'EndPackageKeyword', 'ClassKeyword', 
                           'EndClassKeyword', 'FunctionKeyword', 'EndFunctionKeyword',
                           'TaskKeyword', 'EndTaskKeyword']:
                mk = ModuleKeyword()
                mk.keyword = kind_name.replace('Keyword', '').replace('End', 'end ')
                self.keywords.append(mk)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'keyword': k.keyword[:30]} for k in self.keywords[:50]]


def extract_module_keywords(code: str) -> List[Dict]:
    return ModuleKeywordExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module top;
endmodule
'''
    result = extract_module_keywords(test_code)
    print(f"Module keywords: {len(result)}")
