"""
Force/Release Parser - 使用正确的 AST 遍历

提取 force 和 release 语句：
- force 语句
- release 语句

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
class ForceStmt:
    target: str = ""
    value: str = ""


@dataclass
class ReleaseStmt:
    target: str = ""


class ForceReleaseExtractor:
    def __init__(self):
        self.force_stmts: List[ForceStmt] = []
        self.release_stmts: List[ReleaseStmt] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ForceStatement':
                f = ForceStmt()
                if hasattr(node, 'target') and node.target:
                    f.target = str(node.target)
                if hasattr(node, 'value') and node.value:
                    f.value = str(node.value)
                self.force_stmts.append(f)
            
            elif kind_name == 'ReleaseStatement':
                r = ReleaseStmt()
                if hasattr(node, 'target') and node.target:
                    r.target = str(node.target)
                self.release_stmts.append(r)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return {
            'force': [{'target': f.target, 'value': f.value} for f in self.force_stmts],
            'release': [{'target': r.target} for r in self.release_stmts]
        }


def extract_force_release(code: str) -> Dict:
    return ForceReleaseExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    initial begin
        force data = 8'hFF;
        force addr = 16'h1234;
        #10;
        release data;
    end
endmodule
'''
    result = extract_force_release(test_code)
    print(f"Force: {len(result['force'])}, Release: {len(result['release'])}")
