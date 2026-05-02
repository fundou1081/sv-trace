"""
Cover Options Parser - 使用正确的 AST 遍历

提取覆盖率选项：
- CovergroupOption
- CoverpointOption
- CrossOption

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class CoverOption:
    option_name: str = ""
    option_value: str = ""
    parent_type: str = ""  # covergroup, coverpoint, cross


class CoverOptionsExtractor:
    def __init__(self):
        self.options: List[CoverOption] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'CovergroupOption':
                opt = CoverOption()
                opt.parent_type = 'covergroup'
                if hasattr(node, 'name') and node.name:
                    opt.option_name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    opt.option_value = str(node.value)
                self.options.append(opt)
            
            elif kind_name == 'CoverpointOption':
                opt = CoverOption()
                opt.parent_type = 'coverpoint'
                if hasattr(node, 'name') and node.name:
                    opt.option_name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    opt.option_value = str(node.value)
                self.options.append(opt)
            
            elif kind_name == 'CrossOption':
                opt = CoverOption()
                opt.parent_type = 'cross'
                if hasattr(node, 'name') and node.name:
                    opt.option_name = str(node.name)
                if hasattr(node, 'value') and node.value:
                    opt.option_value = str(node.value)
                self.options.append(opt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'type': o.parent_type, 'name': o.option_name, 'value': str(o.option_value)[:20]}
            for o in self.options
        ]


def extract_cover_options(code: str) -> List[Dict]:
    return CoverOptionsExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
covergroup cg @(posedge clk);
    option.per_instance = 1;
    cp: coverpoint data {
        option.auto_bin_max = 16;
    }
    cross a, b {
        option.comment = "cross coverage";
    }
endgroup
'''
    result = extract_cover_options(test_code)
    print(f"Cover options: {len(result)}")
