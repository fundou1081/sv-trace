"""
Hierarchical Instance Parser - 使用正确的 AST 遍历

提取层次化实例：
- HierarchicalInstance
- InstanceName
- HierarchyInstantiation

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
class HierarchicalInstance:
    module_type: str = ""
    instance_name: str = ""
    connections: List[str] = field(default_factory=list)


class HierarchicalInstanceExtractor:
    def __init__(self):
        self.instances: List[HierarchicalInstance] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'HierarchicalInstance':
                hi = self._extract_instance(node)
                if hi:
                    self.instances.append(hi)
            
            elif kind_name == 'InstanceName':
                hi = HierarchicalInstance()
                hi.instance_name = str(node)
                self.instances.append(hi)
            
            elif kind_name == 'HierarchyInstantiation':
                hi = HierarchicalInstance()
                if hasattr(node, 'module') and node.module:
                    hi.module_type = str(node.module)
                if hasattr(node, 'name') and node.name:
                    hi.instance_name = str(node.name)
                self.instances.append(hi)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def _extract_instance(self, node) -> HierarchicalInstance:
        hi = HierarchicalInstance()
        if hasattr(node, 'module') and node.module:
            hi.module_type = str(node.module)
        if hasattr(node, 'name') and node.name:
            hi.instance_name = str(node.name)
        
        if hasattr(node, 'connections') and node.connections:
            for conn in node.connections:
                hi.connections.append(str(conn)[:30])
        
        return hi if hi.instance_name or hi.module_type else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'type': i.module_type, 'name': i.instance_name, 'conns': len(i.connections)}
            for i in self.instances[:20]
        ]


def extract_instances(code: str) -> List[Dict]:
    return HierarchicalInstanceExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
my_module u1 (.clk(clk), .data(data));
my_module u2 (.clk(clk), .data(data));
'''
    result = extract_instances(test_code)
    print(f"Instances: {len(result)}")
