"""
Modport Parser - 使用正确的 AST 遍历

提取 modport 声明：
- modport 名称
- 接口信号方向

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
class ModportSignal:
    name: str = ""
    direction: str = ""  # input, output, inout, ref


@dataclass
class ModportDef:
    name: str = ""
    signals: List[ModportSignal] = field(default_factory=list)


class ModportExtractor:
    def __init__(self):
        self.modports: List[ModportDef] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ModportDeclaration':
                md = self._extract_modport(node)
                if md:
                    self.modports.append(md)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_modport(self, node) -> Optional[ModportDef]:
        md = ModportDef()
        
        # 名称
        if hasattr(node, 'name') and node.name:
            md.name = str(node.name)
        
        # 遍历子节点
        for child in node:
            if not child:
                continue
            try:
                child_kind = child.kind.name if hasattr(child.kind, 'name') else str(child.kind)
            except:
                continue
            
            if child_kind in ['ModportItem', 'ModportSignal']:
                sig = ModportSignal()
                if hasattr(child, 'name') and child.name:
                    sig.name = str(child.name)
                if hasattr(child, 'direction') and child.direction:
                    sig.direction = str(child.direction).lower()
                md.signals.append(sig)
        
        return md if md.name else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {
                'name': mp.name,
                'signals': [{'name': s.name, 'direction': s.direction} for s in mp.signals]
            }
            for mp in self.modports
        ]


def extract_modports(code: str) -> List[Dict]:
    return ModportExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
interface arb_if;
    logic [7:0] data;
    modport master (input data);
    modport slave (output data);
endinterface
'''
    result = extract_modports(test_code)
    for item in result:
        print(f"Modport: {item['name']}")
        for sig in item['signals']:
            print(f"  {sig['direction']}: {sig['name']}")
