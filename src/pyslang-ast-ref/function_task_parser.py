"""
Function 和 Task Parser - 使用 pyslang AST

支持:
- FunctionDeclaration (function ... endfunction)
- TaskDeclaration (task ... endtask)
- FunctionPrototype (函数原型)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class FunctionInfo:
    """函数信息"""
    name: str = ""
    return_type: str = ""
    arguments: List[Dict] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    is_virtual: bool = False
    is_extern: bool = False
    is_static: bool = False
    has_time: bool = False  # #time 或 # timescale
    statements_count: int = 0


@dataclass
class TaskInfo:
    """任务信息"""
    name: str = ""
    arguments: List[Dict] = field(default_factory=list)
    qualifiers: List[str] = field(default_factory=list)
    is_extern: bool = False
    is_static: bool = False
    has_time: bool = False
    statements_count: int = 0


class FunctionTaskExtractor:
    """从 SystemVerilog 代码中提取函数和任务"""
    
    def __init__(self):
        self.functions: List[FunctionInfo] = []
        self.tasks: List[TaskInfo] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'FunctionDeclaration':
                func = self._extract_function(node)
                if func:
                    self.functions.append(func)
            
            elif kind_name == 'TaskDeclaration':
                task = self._extract_task(node)
                if task:
                    self.tasks.append(task)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.functions + self.tasks
    
    def _extract_function(self, node) -> Optional[FunctionInfo]:
        """提取函数"""
        func = FunctionInfo()
        
        # 函数名
        if hasattr(node, 'name') and node.name:
            func.name = str(node.name)
        
        # 返回类型
        if hasattr(node, 'returnType') and node.returnType:
            func.return_type = str(node.returnType)
        
        # 修饰符
        qualifiers = []
        if hasattr(node, 'qualifier'):
            q = str(node.keyword).lower() if hasattr(node, 'keyword') else ""
            if 'virtual' in q:
                func.is_virtual = True
                qualifiers.append('virtual')
            if 'static' in q:
                func.is_static = True
                qualifiers.append('static')
        func.qualifiers = qualifiers
        
        # 参数列表
        if hasattr(node, 'portList') and node.portList:
            for port in node.portList:
                arg = {}
                # 查找参数名
                if hasattr(port, 'name') and port.name:
                    arg['name'] = str(port.name)
                elif hasattr(port, 'identifier') and port.identifier:
                    arg['name'] = str(port.identifier)
                # 查找参数类型
                if hasattr(port, 'dataType') and port.dataType:
                    arg['type'] = str(port.dataType)
                elif hasattr(port, 'type') and port.type:
                    arg['type'] = str(port.type)
                if arg:
                    func.arguments.append(arg)
        
        # 语句计数
        func.statements_count = self._count_statements(node)
        
        return func
    
    def _extract_task(self, node) -> Optional[TaskInfo]:
        """提取任务"""
        task = TaskInfo()
        
        # 任务名
        if hasattr(node, 'name') and node.name:
            task.name = str(node.name)
        
        # 修饰符
        qualifiers = []
        if hasattr(node, 'qualifier'):
            q = str(node.keyword).lower() if hasattr(node, 'keyword') else ""
            if 'static' in q:
                task.is_static = True
                qualifiers.append('static')
        task.qualifiers = qualifiers
        
        # 参数列表
        if hasattr(node, 'portList') and node.portList:
            for port in node.portList:
                arg = {}
                if hasattr(port, 'name') and port.name:
                    arg['name'] = str(port.name)
                elif hasattr(port, 'identifier') and port.identifier:
                    arg['name'] = str(port.identifier)
                if hasattr(port, 'dataType') and port.dataType:
                    arg['type'] = str(port.dataType)
                elif hasattr(port, 'type') and port.type:
                    arg['type'] = str(port.type)
                if arg:
                    task.arguments.append(arg)
        
        # 语句计数
        task.statements_count = self._count_statements(node)
        
        return task
    
    def _count_statements(self, node) -> int:
        """统计语句数量"""
        count = 0
        
        def traverse(n, depth=0):
            nonlocal count
            if depth > 15:
                return
            
            try:
                kind_name = n.kind.name if hasattr(n.kind, 'name') else str(n.kind)
            except:
                return
            
            if 'Statement' in kind_name or kind_name == 'ExpressionStatement':
                count += 1
            
            if hasattr(n, '__iter__'):
                for child in n:
                    traverse(child, depth + 1)
        
        traverse(node)
        return count
    
    def extract_from_text(self, code: str, source: str = "<text>"):
        tree = pyslang.SyntaxTree.fromText(code, source)
        return self._extract_from_tree(tree.root)
    
    def get_functions(self) -> List[FunctionInfo]:
        return self.functions
    
    def get_tasks(self) -> List[TaskInfo]:
        return self.tasks


# ============================================================================
# 便捷函数
# ============================================================================

def extract_functions(code: str) -> List[Dict]:
    """从代码提取函数"""
    extractor = FunctionTaskExtractor()
    extractor.extract_from_text(code)
    
    return [
        {
            'name': f.name,
            'return_type': f.return_type,
            'arguments': f.arguments,
            'qualifiers': f.qualifiers,
            'is_virtual': f.is_virtual,
            'statements_count': f.statements_count
        }
        for f in extractor.functions
    ]


def extract_tasks(code: str) -> List[Dict]:
    """从代码提取任务"""
    extractor = FunctionTaskExtractor()
    extractor.extract_from_text(code)
    
    return [
        {
            'name': t.name,
            'arguments': t.arguments,
            'qualifiers': t.qualifiers,
            'statements_count': t.statements_count
        }
        for t in extractor.tasks
    ]


def extract_functions_tasks(code: str) -> Dict[str, List]:
    """一次性提取函数和任务"""
    extractor = FunctionTaskExtractor()
    extractor.extract_from_text(code)
    
    return {
        'functions': [
            {
                'name': f.name,
                'return_type': f.return_type,
                'arguments': f.arguments,
                'is_virtual': f.is_virtual,
                'statements': f.statements_count
            }
            for f in extractor.functions
        ],
        'tasks': [
            {
                'name': t.name,
                'arguments': t.arguments,
                'statements': t.statements_count
            }
            for t in extractor.tasks
        ],
        'function_count': len(extractor.functions),
        'task_count': len(extractor.tasks)
    }


if __name__ == "__main__":
    test_code = '''
module test;
    // Simple function
    function int add(input int a, b);
        return a + b;
    endfunction
    
    // Virtual function
    virtual function bit [7:0] process();
        return 8'h55;
    endfunction
    
    // Task
    task send_data(input [31:0] d, input bit v);
        @(posedge clk);
        data <= d;
        valid <= v;
    endtask
    
    // Static task
    static task wait_cycles(input int n);
        repeat(n) @(posedge clk);
    endtask
endmodule
'''
    
    print("=== Function/Task Extraction ===\n")
    
    result = extract_functions_tasks(test_code)
    
    print(f"Functions ({result['function_count']}):")
    for f in result['functions']:
        virt_str = "virtual " if f['is_virtual'] else ""
        ret_str = f"{f['return_type']} " if f['return_type'] else ""
        print(f"  {virt_str}function {ret_str}{f['name']}({len(f['arguments'])} args) - {f['statements']} statements")
    
    print(f"\nTasks ({result['task_count']}):")
    for t in result['tasks']:
        print(f"  task {t['name']}({len(t['arguments'])} args) - {t['statements']} statements")
