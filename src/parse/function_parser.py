"""
Function/Task Parser - 使用 pyslang AST

支持:
- FunctionDeclaration
- TaskDeclaration
- Return type
- Arguments (ref, const ref, etc)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List
import pyslang
from pyslang import SyntaxKind


@dataclass
class FunctionArg:
    """函数参数"""
    name: str = ""
    direction: str = ""  # input, output, ref, const ref
    data_type: str = ""
    default: str = ""


@dataclass
class FunctionDef:
    """函数/任务定义"""
    name: str = ""
    is_task: bool = False
    return_type: str = ""
    arguments: List[FunctionArg] = field(default_factory=list)
    body: str = ""


class FunctionParser:
    def __init__(self, parser=None):
        self.parser = parser
        self.functions = []
        
        if parser:
            self._extract_all()
    
    def _extract_all(self):
        for key, tree in getattr(self.parser, 'trees', {}).items():
            root = tree.root if hasattr(tree, 'root') else tree
            self._extract_from_tree(root)
    
    def _extract_from_tree(self, root):
        def collect(node):
            kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            
            if kind_name == 'FunctionDeclaration':
                self._extract_function(node, False)
            elif kind_name == 'TaskDeclaration':
                self._extract_function(node, True)
            
            return pyslang.VisitAction.Advance
        
        (root.root if hasattr(root, "root") else root).visit(collect)
    
    def _extract_function(self, node, is_task):
        func = FunctionDef()
        func.is_task = is_task
        
        # 名称
        if hasattr(node, 'name') and node.name:
            func.name = str(node.name)
        
        # 返回类型
        if hasattr(node, 'returnType') and node.returnType:
            func.return_type = str(node.returnType)
        
        # 参数
        if hasattr(node, 'ports') and node.ports:
            for port in node.ports:
                if not port:
                    continue
                
                fa = FunctionArg()
                
                # 参数名
                if hasattr(port, 'name') and port.name:
                    fa.name = str(port.name)
                elif hasattr(port, 'identifier'):
                    fa.name = str(port.identifier)
                
                # 方向
                if hasattr(port, 'direction'):
                    fa.direction = str(port.direction)
                
                # 类型
                if hasattr(port, 'dataType'):
                    fa.data_type = str(port.dataType)
                
                # 默认值
                if hasattr(port, 'value') and port.value:
                    fa.default = str(port.value)
                
                func.arguments.append(fa)
        
        # body (提取第一条语句作为示例)
        if hasattr(node, 'body') and node.body:
            func.body = str(node.body)[:50]
        
        self.functions.append(func)
    
    def get_functions(self):
        return self.functions


def extract_functions(code):
    tree = pyslang.SyntaxTree.fromText(code)
    extractor = FunctionParser(None)
    extractor._extract_from_tree(tree)
    return extractor.functions


if __name__ == "__main__":
    test_code = '''
module test;
    function bit [7:0] add(input bit [7:0] a, b);
        return a + b;
    endfunction
    
    task send_data(input [7:0] data, ref bit [7:0] ack);
        ack = data;
    endtask
    
    function automatic void process();
    endfunction
endmodule
'''
    
    result = extract_functions(test_code)
    print("=== Function/Task Extraction ===")
    for func in result:
        kind = "task" if func.is_task else "function"
        print(f"{kind} {func.name}: {len(func.arguments)} args")
