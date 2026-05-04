"""
Queue Dimension Specifier Parser - 使用正确的 AST 遍历

提取队列维度说明符：
- QueueDimensionSpecifier

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class QueueDimensionSpecifier:
    max_size: str = ""


class QueueDimensionSpecifierExtractor:
    def __init__(self):
        self.specifiers: List[QueueDimensionSpecifier] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'QueueDimensionSpecifier':
                qds = QueueDimensionSpecifier()
                if hasattr(node, 'maxSize') and node.maxSize:
                    qds.max_size = str(node.maxSize)
                self.specifiers.append(qds)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'max_size': s.max_size[:20]} for s in self.specifiers]


def extract_queue_dims(code: str) -> List[Dict]:
    return QueueDimensionSpecifierExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
int q[$];
int q2 [$:100];
'''
    result = extract_queue_dims(test_code)
    print(f"Queue dimension specifiers: {len(result)}")
