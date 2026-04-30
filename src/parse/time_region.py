"""
Time/Region 解析器 - 使用 pyslang AST

支持:
- timeunit/timeprecision
- module/interface/program time region
- Disable fork
- Wait fork
- Process self()
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class TimeUnit:
    """timeunit/timeprecision"""
    unit: str = ""  # 1ns, 1ps, etc
    precision: str = ""


@dataclass  
class TimeRegion:
    """time region (module, interface, program)"""
    kind: str = ""
    name: str = ""
    timeunit: str = ""


@dataclass
class ForkItem:
    """fork join item"""
    kind: str = ""  # fork, join, join_any, join_none
    statements: List[str] = field(default_factory=list)


class TimeRegionExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.timeunit = None
        self.regions = []
        self.forks = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'TimeUnitDeclaration':
                self._extract_timeunit(node)
            elif 'Region' in kind_name:
                self._extract_region(node)
            elif kind_name in ['DisableForkStatement', 'WaitForkStatement']:
                self._extract_fork(node)
            elif kind_name == 'ProcessProceduralStatement':
                self._extract_process(node)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_timeunit(self, node):
        if not self.timeunit:
            tu = TimeUnit()
            # 提取 timeunit 和 timeprecision
            if hasattr(node, 'timeUnit') and node.timeUnit:
                tu.unit = str(node.timeUnit)
            if hasattr(node, 'timePrecision') and node.timePrecision:
                tu.precision = str(node.timePrecision)
            self.timeunit = tu
    
    def _extract_region(self, node):
        region = TimeRegion()
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        region.kind = kind_name
        
        if hasattr(node, 'name') and node.name:
            region.name = str(node.name)
        
        if hasattr(node, 'timeUnit') and node.timeUnit:
            region.timeunit = str(node.timeUnit)
        
        self.regions.append(region)
    
    def _extract_fork(self, node):
        kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
        fork = ForkItem()
        
        if kind_name == 'DisableForkStatement':
            fork.kind = 'disable_fork'
        elif kind_name == 'WaitForkStatement':
            fork.kind = 'wait_fork'
        
        self.forks.append(fork)
    
    def _extract_process(self, node):
        # process::self() 检测
        node_str = str(node)
        if 'process::self' in node_str:
            # 记录但不需要特殊处理
            pass
    
    def get_timeunit(self):
        return self.timeunit
    
    def get_regions(self):
        return self.regions
    
    def get_forks(self):
        return self.forks


def extract_time_regions(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = TimeRegionExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor


if __name__ == "__main__":
    test_code = '''
timeunit 1ns;
timeprecision 100ps;

module test;
    timeunit 1ns/10ps;
    
    initial begin
        fork
            #10;
            #20;
        join_any
        
        disable fork;
    end
    
    process::self();
endmodule
'''
    
    result = extract_time_regions(test_code)
    print("=== Time Region Extraction ===")
    if result.timeunit:
        print(f"timeunit: {result.timeunit.unit}/{result.timeunit.precision}")
    print(f"regions: {len(result.regions)}")
    print(f"forks: {len(result.forks)}")
