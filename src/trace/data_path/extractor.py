"""RTL Data Path Extractor

从RTL提取数据通路元素:
- 操作单元(ADD, MUL, MUX, etc.)
- 数据流边
- 控制信号
- 时序/组合逻辑边界
"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass


@dataclass
class DataPathNode:
    """数据通路节点"""
    name: str
    node_type: str  # 'operator', 'register', 'mux', 'fifo', 'signal'
    width: int = 0
    line: int = 0
    modules: List[str] = None
    
    def __post_init__(self):
        if self.modules is None:
            self.modules = []


@dataclass
class DataPathEdge:
    """数据通路边 / 数据流"""
    src: str
    dst: str
    edge_type: str  # 'data', 'control', 'valid'
    condition: str = ""  # MUX selection condition
    width: int = 0


class DataPathExtractor:
    """从RTL提取数据通路"""
    
    # 操作符映射
    OPERATORS = {
        'add': 'ADD', '+': 'ADD',
        'sub': 'SUB', '-': 'SUB', 
        'mul': 'MUL', '*': 'MUL',
        'div': 'DIV', '/': 'DIV',
        'shl': 'SHL', '>>': 'SHL',
        'shr': 'SHR', '<<': 'SHR',
        'and': 'AND', '&': 'AND',
        'or': 'OR', '|': 'OR',
        'xor': 'XOR', '^': 'XOR',
        'compare': 'CMP', '==': 'CMP', '!=': 'CMP',
        'mux': 'MUX',
    }
    
    def __init__(self, parser):
        self.parser = parser
        self.nodes: Dict[str, DataPathNode] = {}
        self.edges: List[DataPathEdge] = []
        self._extract()
    
    def _extract(self):
        """提取数据通路"""
        for class_name, cls in self._get_classes().items():
            self._extract_from_class(class_name, cls)
    
    def _get_classes(self):
        from debug.class_extractor import ClassExtractor
        extractor = ClassExtractor(self.parser)
        return extractor.classes
    
    def _extract_from_class(self, class_name: str, cls):
        """从class提取数据通路"""
        # 添加操作符
        for method in cls.methods:
            node_type = self._get_operator_type(method.prototype)
            if node_type:
                self._add_node(method.name, node_type, cls.line_number if hasattr(cls, 'line_number') else 0)
        
        # 添加属性作为寄存器/信号
        for prop in cls.properties:
            node_type = 'REGISTER' if prop.rand_mode in ('rand', 'randc') else 'SIGNAL'
            self._add_node(prop.name, node_type, 0, prop.width if hasattr(prop, 'width') else 0)
    
    def _get_operator_type(self, proto: str) -> str:
        """识别操作符类型"""
        for keyword, op_type in self.OPERATORS.items():
            if keyword in proto.lower():
                return op_type
        return None
    
    def _add_node(self, name: str, node_type: str, line: int = 0, width: int = 0):
        full_name = f"{name}"  # 可以加class前缀
        if full_name not in self.nodes:
            self.nodes[full_name] = DataPathNode(full_name, node_type, width, line)
    
    def build_edges(self) -> List[DataPathEdge]:
        """构建数据流边"""
        # 从constraint/dependency提取数据流
        from debug.constraint_parser_v2 import parse_constraints
        cp = parse_constraints(self.parser)
        
        for const in cp.constraints.values():
            # 变量之间的依赖 = 数据流
            for var in const.variables:
                if var.name in self.nodes:
                    # 可以通过更多分析建立边
                    edge = DataPathEdge(
                        src=var.name,
                        dst=const.name,
                        edge_type='data'
                    )
                    self.edges.append(edge)
        
        return self.edges
    
    def get_summary(self) -> str:
        """返回摘要"""
        by_type = {}
        for node in self.nodes.values():
            by_type[node.node_type] = by_type.get(node.node_type, 0) + 1
        
        lines = ["Data Path Extraction Summary", "=" * 40]
        for t, c in sorted(by_type.items()):
            lines.append(f"  {t}: {c}")
        lines.append(f"  Edges: {len(self.edges)}")
        return "\n".join(lines)


def extract_data_path(parser) -> DataPathExtractor:
    """便捷函数"""
    return DataPathExtractor(parser)
