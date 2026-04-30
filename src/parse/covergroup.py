"""
Covergroup 解析器 - 使用 pyslang AST

支持:
- covergroup 声明
- coverpoint (bins, iff, with)
- cross
- wildcard/illegal/ignore bins
- bins with range,权重,条件
"""
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class CoverpointBin:
    """coverpoint bin"""
    name: str = ""
    values: List[str] = field(default_factory=list)
    weight: int = 0
    condition: str = ""  # iff 条件
    with_expr: str = ""  # with clause


@dataclass
class Coverpoint:
    """coverpoint 定义"""
    name: str = ""
    bins: List[CoverpointBin] = field(default_factory=list)
    iff_condition: str = ""  # coverpoint 级别的 iff


@dataclass
class CoverCross:
    """cross cover"""
    name: str = ""
    points: List[str] = field(default_factory=list)
    bins: List[str] = field(default_factory=list)


@dataclass
class CovergroupDef:
    """covergroup 定义"""
    name: str = ""
    coverpoints: List[Coverpoint] = field(default_factory=list)
    crosses: List[CoverCross] = field(default_factory=list)
    option: dict = field(default_factory=dict)


def _collect_nodes(node):
    nodes = []
    def collect(n):
        nodes.append(n)
        return pyslang.VisitAction.Advance
    node.visit(collect)
    return nodes


class CovergroupExtractor:
    def __init__(self, parser=None):
        self.parser = parser
        self.covergroups = {}
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            if tree and hasattr(tree, 'root') and tree.root:
                self._extract_from_tree(tree)
    
    def _extract_from_tree(self, tree):
        # 支持传入 tree 或 root
        if hasattr(tree, 'root'):
            tree = tree.root
        
        root = tree.root if hasattr(tree, "root") else tree
        
        def collect(node):
            if node.kind == SyntaxKind.CovergroupDeclaration:
                self._extract_covergroup(node)
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_covergroup(self, node):
        cg = CovergroupDef()
        
        # name
        if hasattr(node, 'name') and node.name:
            cg.name = str(node.name).strip()
        
        # option (per_instance, weight, etc)
        if hasattr(node, 'option') and node.option:
            cg.option = str(node.option).strip()
        
        # members: coverpoints, crosses
        if hasattr(node, 'members') and node.members:
            for m in node.members:
                if not m:
                    continue
                
                kind_name = m.kind.name
                
                # Coverpoint
                if kind_name == 'Coverpoint':
                    cp = self._extract_coverpoint(m)
                    if cp:
                        cg.coverpoints.append(cp)
                
                # CoverCross
                elif kind_name == 'CoverCross':
                    cross = self._extract_cross(m)
                    if cross:
                        cg.crosses.append(cross)
                
                # Option (covergroup option)
                elif kind_name == 'CovergroupOption':
                    opt_str = str(m).strip()
                    if 'per_instance' in opt_str:
                        cg.option['per_instance'] = True
                    if 'weight' in opt_str:
                        cg.option['weight'] = True
        
        if cg.name:
            self.covergroups[cg.name] = cg
    
    def _extract_coverpoint(self, node):
        cp = Coverpoint()
        
        # name
        if hasattr(node, 'name') and node.name:
            cp.name = str(node.name).strip()
        
        # iff 条件 (coverpoint 级别)
        if hasattr(node, 'iffCondition') and node.iffCondition:
            cp.iff_condition = str(node.iffCondition).strip()
        
        # bins - 从 items 提取
        if hasattr(node, 'items') and node.items:
            for item in node.items:
                if not item:
                    continue
                
                item_str = str(item).strip()
                
                # 判断 bin 类型
                bin_type = 'normal'
                if 'wildcard' in item_str.lower():
                    bin_type = 'wildcard'
                elif 'illegal' in item_str.lower():
                    bin_type = 'illegal'
                elif 'ignore' in item_str.lower():
                    bin_type = 'ignore'
                
                # 解析 bin
                bin_obj = self._parse_bin(item, bin_type)
                if bin_obj:
                    cp.bins.append(bin_obj)
        
        return cp if cp.name or cp.bins else None
    
    def _parse_bin(self, node, bin_type='normal'):
        """解析单个 bin"""
        bin_obj = CoverpointBin()
        bin_str = str(node).strip()
        
        # 提取 bin 名称和值
        # 格式: bins NAME = {values};
        # 格式: bins NAME = value with (condition);
        # 格式: bins NAME = value iff (condition);
        
        # bins 名称
        match = re.search(r'bins\s+(\w+)\s*=', bin_str)
        if match:
            bin_obj.name = match.group(1)
        
        # iff 条件
        iff_match = re.search(r'iff\s*\(([^)]+)\)', bin_str)
        if iff_match:
            bin_obj.condition = iff_match.group(1).strip()
        
        # with clause
        with_match = re.search(r'with\s*\(([^)]+)\)', bin_str)
        if with_match:
            bin_obj.with_expr = with_match.group(1).strip()
        
        # 权重 (dist 分布)
        weight_match = re.search(r':=\s*(\d+)', bin_str)
        if weight_match:
            bin_obj.weight = int(weight_match.group(1))
        
        # 范围值 {[low:high]}
        range_match = re.search(r'\{\[?([^}\]]+)\]?\}', bin_str)
        if range_match:
            vals = range_match.group(1).split(':')
            bin_obj.values = [v.strip() for v in vals]
        
        # single value {N}
        single_match = re.search(r'\{\s*(\d+)\s*\}', bin_str)
        if single_match and not bin_obj.values:
            bin_obj.values = [single_match.group(1)]
        
        # default bins
        if 'default' in bin_str.lower():
            bin_obj.name = 'default'
            bin_obj.values = ['default']
        
        return bin_obj if bin_obj.name or bin_obj.values else None
    
    def _extract_cross(self, node):
        cross = CoverCross()
        
        # name
        if hasattr(node, 'name') and node.name:
            cross.name = str(node.name).strip()
        
        # 覆盖点列表
        if hasattr(node, 'covergroupIdentifierList') and node.covergroupIdentifierList:
            points_str = str(node.covergroupIdentifierList).strip()
            cross.points = [p.strip() for p in points_str.split(',')]
        
        # bins with soft
        if hasattr(node, 'items') and node.items:
            for item in node.items:
                item_str = str(item).strip()
                if item_str:
                    cross.bins.append(item_str)
        
        return cross if cross.name or cross.points else None
    
    def get_covergroups(self):
        return self.covergroups


def extract_covergroups(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = CovergroupExtractor(None)
    extractor._extract_from_tree(tree)
    return extractor.covergroups


if __name__ == "__main__":
    test_code = '''class test;
    covergroup cg with function sample(bit [7:0] data);
        // 基础 coverpoint
        coverpoint data;
        
        // iff 条件
        coverpoint data iff (enable);
        
        // bins with range
        coverpoint data {
            bins zero = {0};
            bins low = {[1:10]};
            bins others = default;
        }
        
        // wildcard bins
        coverpoint data {
            wildcard bins wb = {[0:255]};
        }
        
        // illegal bins
        coverpoint data {
            illegal bins ib = {255};
        }
        
        // ignore bins  
        coverpoint data {
            ignore bins ign = {[32:63]};
        }
        
        // with clause
        coverpoint data {
            bins valid = {[0:255]} with (item < 128);
        }
        
        // iff + with
        coverpoint data iff (valid) {
            bins ok = {[10:50]} with (item inside {[10:30]});
        }
        
        // cross with bins
        cross a, b {
            bins c = binsof(a) intersect {1};
        }
        
        option.per_instance = 1;
    endgroup
endclass'''
    
    result = extract_covergroups(test_code)
    
    print("=== Covergroup 增强测试 ===")
    print(f"\nFound {len(result)} covergroups")
    
    for name, cg in result.items():
        print(f"\n📦 {name}")
        
        # coverpoints
        print(f"  Coverpoints ({len(cg.coverpoints)}):")
        for cp in cg.coverpoints:
            print(f"    📍 {cp.name or '(auto)'}")
            if cp.iff_condition:
                print(f"       iff: {cp.iff_condition}")
            
            print(f"       bins ({len(cp.bins)}):")
            for b in cp.bins[:5]:
                vals = ','.join(b.values[:3])
                extra = []
                if b.condition:
                    extra.append(f"iff({b.condition})")
                if b.with_expr:
                    extra.append(f"with({b.with_expr})")
                if b.weight:
                    extra.append(f"weight={b.weight}")
                
                suffix = f" [{','.join(extra)}]" if extra else ""
                print(f"         - {b.name or vals}{suffix}")
        
        # crosses
        print(f"  Crosses ({len(cg.crosses)}):")
        for cr in cg.crosses:
            print(f"    {cr.points}")
            for b in cr.bins[:3]:
                print(f"      - {b}")
        
        # option
        if cg.option:
            print(f"  Options: {cg.option}")
