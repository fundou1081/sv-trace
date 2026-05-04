"""
Parameter Port List Parser - 使用正确的 AST 遍历

提取参数端口列表：
- ParameterPortList

注意：此文件不包含任何正则表达式
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict
import pyslang


@dataclass
class ParameterPortList:
    parameters: List[str] = None
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = []


class ParameterPortListExtractor:
    def __init__(self):
        self.lists: List[ParameterPortList] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'ParameterPortList':
                ppl = ParameterPortList()
                
                params = []
                def get_params(n):
                    kn = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
                    if 'Parameter' in kn:
                        params.append(str(n)[:20])
                    return pyslang.VisitAction.Advance
                node.visit(get_params)
                ppl.parameters = params[:20]
                
                self.lists.append(ppl)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [{'count': len(l.parameters)} for l in self.lists]


def extract_parameter_ports(code: str) -> List[Dict]:
    return ParameterPortListExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module m #(
    parameter WIDTH = 8
);
endmodule
'''
    result = extract_parameter_ports(test_code)
    print(f"Parameter port lists: {len(result)}")
