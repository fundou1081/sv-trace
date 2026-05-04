"""
CoverCross Parser - 使用正确的 AST 遍历

提取覆盖组交叉和 bins：
- covergroup 声明
- coverpoint
- covercross
- 自动生成 bins
- 交叉bins 声明

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class CoverageBin:
    """覆盖率 bins"""
    name: str = ""
    bin_type: str = ""  # default, auto, illegal, ignore, explicit
    range_start: str = ""
    range_end: str = ""


@dataclass
class Coverpoint:
    """覆盖点"""
    name: str = ""
    expression: str = ""  # 覆盖的变量/表达式


@dataclass
class CoverCross:
    """覆盖交叉"""
    name: str = ""
    coverpoints: List[str] = field(default_factory=list)
    bins: List[CoverageBin] = field(default_factory=list)
    option_auto_bin_max: int = 0


@dataclass
class Covergroup:
    """覆盖组"""
    name: str = ""
    coverpoints: List[Coverpoint] = field(default_factory=list)
    crosses: List[CoverCross] = field(default_factory=list)


class CoverCrossExtractor:
    """提取 covergroup、coverpoint 和 covercross"""
    
    def __init__(self):
        self.covergroups: List[Covergroup] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # CovergroupDeclaration
            if kind_name == 'CovergroupDeclaration':
                cg = self._extract_covergroup(node)
                if cg:
                    self.covergroups.append(cg)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_covergroup(self, node) -> Optional[Covergroup]:
        cg = Covergroup()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            cg.name = str(node.name)
        
        # 遍历子节点
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            # CoverpointSymbol
            if child_kind == 'CoverpointSymbol':
                cp = Coverpoint()
                if hasattr(child, 'name') and child.name:
                    cp.name = str(child.name)
                if hasattr(child, 'expression') and child.expression:
                    cp.expression = str(child.expression)
                cg.coverpoints.append(cp)
            
            # CoverCrossSymbol
            elif child_kind == 'CoverCrossSymbol':
                cc = self._extract_covercross(child)
                if cc:
                    cg.crosses.append(cc)
        
        return cg if cg.name else None
    
    def _extract_covercross(self, node) -> Optional[CoverCross]:
        cc = CoverCross()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            cc.name = str(node.name)
        
        # 提取交叉的 coverpoint
        if hasattr(node, 'coverpoints') and node.coverpoints:
            for cp in node.coverpoints:
                if hasattr(cp, 'name') and cp.name:
                    cc.coverpoints.append(str(cp.name))
        
        # 选项
        if hasattr(node, 'option') and node.option:
            for opt in node.option:
                if hasattr(opt, 'name') and opt.name:
                    if 'auto_bin_max' in str(opt.name):
                        if hasattr(opt, 'value') and opt.value:
                            cc.option_auto_bin_max = int(str(opt.value))
        
        # 提取 bins
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind == 'CoverageBin':
                bin = self._extract_bin(child)
                if bin:
                    cc.bins.append(bin)
        
        return cc if cc.name or cc.coverpoints else None
    
    def _extract_bin(self, node) -> Optional[CoverageBin]:
        b = CoverageBin()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            b.name = str(node.name)
        
        # 类型
        if hasattr(node, 'keyword') and node.keyword:
            kw = str(node.keyword).lower()
            if 'illegal' in kw:
                b.bin_type = 'illegal'
            elif 'ignore' in kw:
                b.bin_type = 'ignore'
            elif 'default' in kw:
                b.bin_type = 'default'
            else:
                b.bin_type = 'explicit'
        
        # 范围
        if hasattr(node, 'range') and node.range:
            r = node.range
            if hasattr(r, 'left') and r.left:
                b.range_start = str(r.left)
            if hasattr(r, 'right') and r.right:
                b.range_end = str(r.right)
        
        return b if b.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return [
            {
                'name': cg.name,
                'coverpoints': [
                    {'name': cp.name, 'expr': cp.expression[:30]}
                    for cp in cg.coverpoints
                ],
                'crosses': [
                    {
                        'name': cc.name,
                        'coverpoints': cc.coverpoints,
                        'bins_count': len(cc.bins),
                        'auto_bin_max': cc.option_auto_bin_max
                    }
                    for cc in cg.crosses
                ]
            }
            for cg in self.covergroups
        ]
    
    def extract_from_file(self, filepath: str) -> List[Dict]:
        with open(filepath, 'r') as f:
            code = f.read()
        return self.extract_from_text(code, filepath)


def extract_covercross(code: str) -> List[Dict]:
    """便捷函数"""
    return CoverCrossExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    covergroup cg @(posedge clk);
        coverpoint addr {
            bins low = {[0:127]};
            bins high = {[128:255]};
            bins others = default;
        }
        
        cross addr, data {
            option.auto_bin_max = 8;
            bins range = binsof(addr) intersect {[10:50]};
            illegal bins illegal_range = binsof(data) intersect {[100:200]};
        }
    endgroup
endmodule
'''
    
    print("=== CoverCross Extraction ===\n")
    result = extract_covercross(test_code)
    for item in result:
        print(f"Covergroup: {item['name']}")
        for cp in item['coverpoints']:
            print(f"  Coverpoint: {cp['name']} ({cp['expr']}...)")
        for cx in item['crosses']:
            print(f"  Cross: {cx['name']}, {len(cx['coverpoints'])} points, {cx['bins_count']} bins")
    print(f"\nTotal: {len(result)} covergroups")
