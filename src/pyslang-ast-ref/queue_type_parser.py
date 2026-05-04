"""
Queue Type Parser - 使用正确的 AST 遍历

提取队列类型：
- QueueType
- DollarUnpackedDimension

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class QueueType:
    data_type: str = ""
    max_size: str = ""


class QueueTypeExtractor:
    def __init__(self):
        self.types: List[QueueType] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name in ['QueueType', 'QueueVariableType']:
                qt = QueueType()
                if hasattr(node, 'dataType') and node.dataType:
                    qt.data_type = str(node.dataType)[:20]
                if hasattr(node, 'maxSize') and node.maxSize:
                    qt.max_size = str(node.maxSize)
                self.types.append(qt)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'data': t.data_type[:20], 'max': t.max_size[:10]} for t in self.types]


def extract_queue_types(code: str) -> List[Dict]:
    return QueueTypeExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int queue [$];
int queue2 [$:100];
'''
    result = extract_queue_types(test_code)
    print(f"Queue types: {len(result)}")
