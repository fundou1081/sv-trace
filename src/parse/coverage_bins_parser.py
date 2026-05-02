"""
Coverage Bins Parser - 使用正确的 AST 遍历

覆盖率 bins 提取

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
class CoverageBin:
    name: str = ""
    bin_type: str = ""  # default, illegal, ignore, explicit, range, transition


class CoverageBinsExtractor:
    """提取覆盖率 bins"""
    
    def __init__(self):
        self.bins: List[CoverageBin] = [], 
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['CoverageBin', 'CoverageBinArray']:
                bin = CoverageBin()
                if hasattr(node, 'name') and node.name:
                    bin.name = str(node.name)
                
                # 检查 bins 类型
                if hasattr(node, 'keyword') and node.keyword:
                    kw = str(node.keyword).lower()
                    if 'illegal' in kw:
                        bin.bin_type = 'illegal'
                    elif 'ignore' in kw:
                        bin.bin_type = 'ignore'
                    elif 'default' in kw:
                        bin.bin_type = 'default'
                
                self.bins[0].append(bin)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'name': b.name, 'type': b.bin_type} for b in self.bins[0]]


def extract_coverage_bins(code: str) -> List[Dict]:
    return CoverageBinsExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
covergroup cg;
    cp: coverpoint data {
        bins low = {[0:15]};
        bins others = default;
    }
endgroup
'''
    print(extract_coverage_bins(test_code))
