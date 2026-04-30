"""
Coverage Bins Parser - 使用 pyslang AST

支持:
- CoverageBinsArray (数组 bins)
- WildcardCoverageBin
- IllegalCoverageBin
- IgnoreCoverageBin
- BinsArraySize
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class CoverageBinArray:
    """Coverage bins array"""
    name: str = ""
    size: str = ""  # [N] or [*] or [$]
    values: List[str] = field(default_factory=list)
    is_with: str = ""  # with clause
    is_default: bool = False


@dataclass
class CoverageBinsDef:
    """Coverage bins definition"""
    kind: str = ""  # normal, wildcard, illegal, ignore
    name: str = ""
    array: CoverageBinArray = None
    weight: int = 0


class CoverageBinsParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.bins = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name in ['WildcardCoverageBin', 'IllegalCoverageBin', 
                          'IgnoreCoverageBin', 'CoverageBinArray']:
                self._extract_bins(node, kind_name)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_bins(self, node, kind_name):
        bins_def = CoverageBinsDef()
        
        # 判断类型
        if kind_name == 'WildcardCoverageBin':
            bins_def.kind = 'wildcard'
        elif kind_name == 'IllegalCoverageBin':
            bins_def.kind = 'illegal'
        elif kind_name == 'IgnoreCoverageBin':
            bins_def.kind = 'ignore'
        else:
            bins_def.kind = 'normal'
        
        node_str = str(node)
        
        # bin 名称
        if hasattr(node, 'identifier') and node.identifier:
            bins_def.name = str(node.identifier)
        
        # 数组大小
        arr = CoverageBinArray()
        if 'with' in node_str:
            # with clause
            import re
            with_match = re.search(r'with\s*\(([^)]+)\)', node_str)
            if with_match:
                arr.is_with = with_match.group(1)
        
        # 提取数组大小
        if hasattr(node, 'coverageBinsArraySize'):
            arr.size = str(node.coverageBinsArraySize)
        
        bins_def.array = arr
        self.bins.append(bins_def)
    
    def get_bins(self):
        return self.bins


def extract_coverage_bins(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = CoverageBinsParser(None)
    extractor._extract_from_tree(tree)
    return extractor.bins


if __name__ == "__main__":
    test_code = '''
module test;
    covergroup cg with function sample(bit [7:0] data);
        coverpoint data {
            bins q[*] = q;
            bins low = {[0:10]};
            wildcard bins valid = {8'b01??_????};
            illegal bins illegal_val = {8'hFF};
            ignore bins ignore_val = {[32:63]};
        }
    endgroup
endmodule
'''
    
    result = extract_coverage_bins(test_code)
    print("=== Coverage Bins ===")
    for bins in result:
        print(f"  {bins.name} ({bins.kind})")
