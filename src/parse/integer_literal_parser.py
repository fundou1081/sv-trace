"""
Integer Literal Parser - 使用正确的 AST 遍历

提取整数字面量：
- 十进制整数
- 二进制整数 (8'b1010)
- 八进制整数 (8'o12)
- 十六进制整数 (8'hFF)
- 有符号/无符号

注意：此文件不包含任何正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang
from pyslang import SyntaxKind


@dataclass
class IntegerLiteral:
    """整数字面量"""
    value: str = ""
    base: str = ""  # dec, bin, oct, hex
    width: int = 0
    signed: bool = False


class IntegerLiteralExtractor:
    def __init__(self):
        self.literals: List[IntegerLiteral] = []
        self.count_by_base = {'dec': 0, 'bin': 0, 'oct': 0, 'hex': 0}
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'IntegerLiteral':
                il = IntegerLiteral()
                
                # 基本信息
                if hasattr(node, 'value') and node.value:
                    il.value = str(node.value)
                if hasattr(node, 'base') and node.base:
                    base_str = str(node.base).lower()
                    if 'bin' in base_str:
                        il.base = 'bin'
                    elif 'oct' in base_str:
                        il.base = 'oct'
                    elif 'hex' in base_str:
                        il.base = 'hex'
                    else:
                        il.base = 'dec'
                
                # 位宽
                if hasattr(node, 'width') and node.width:
                    try:
                        il.width = int(str(node.width))
                    except:
                        pass
                
                # 有符号性
                if hasattr(node, 'signed') and node.signed:
                    il.signed = bool(node.signed)
                
                self.literals.append(il)
                
                if il.base in self.count_by_base:
                    self.count_by_base[il.base] += 1
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> Dict:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        
        return {
            'total': len(self.literals),
            'by_base': self.count_by_base,
            'literals': [
                {
                    'value': il.value[:20],
                    'base': il.base,
                    'width': il.width,
                    'signed': il.signed
                }
                for il in self.literals[:10]
            ]
        }


def extract_integer_literals(code: str) -> Dict:
    return IntegerLiteralExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    logic [7:0] a = 8'b10101010;
    logic [7:0] b = 8'hFF;
    logic [15:0] c = 16'd1234;
    logic [7:0] d = 8'o77;
    integer e = -100;
endmodule
'''
    result = extract_integer_literals(test_code)
    print(f"Integer literals: {result['total']}")
    print(f"By base: {result['by_base']}")
