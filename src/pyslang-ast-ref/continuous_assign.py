"""
Continuous Assign Parser - 使用正确的 AST 遍历

连续赋值语句提取

注意：此文件使用正确的 AST 属性访问，不包含正则表达式
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass
from typing import List, Dict, Optional
import pyslang
from pyslang import SyntaxKind


@dataclass
class ContinuousAssign:
    name: str = ""
    left: str = ""
    right: str = ""
    delay: str = ""


class ContinuousAssignExtractor:
    """提取连续赋值语句 - 使用正确的 AST 遍历"""
    
    def __init__(self):
        self.assigns: List[ContinuousAssign] = []
    
    def _extract_from_tree(self, root):
        """使用 AST 遍历"""
        self.assigns = []
        
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            # ContinuousAssign
            if kind_name == 'ContinuousAssign':
                assign = self._extract_assign(node)
                if assign:
                    self.assigns.append(assign)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
        return self.assigns
    
    def _extract_assign(self, node) -> Optional[ContinuousAssign]:
        """提取连续赋值 - 使用 AST 属性"""
        assign = ContinuousAssign()
        
        # 赋值名称 (optional label)
        if hasattr(node, 'name') and node.name:
            assign.name = str(node.name)
        elif hasattr(node, 'label') and node.label:
            assign.name = str(node.label)
        
        # 左侧 (目标)
        if hasattr(node, 'left') and node.left:
            assign.left = str(node.left)
        elif hasattr(node, 'target') and node.target:
            assign.left = str(node.target)
        
        # 右侧 (表达式)
        if hasattr(node, 'right') and node.right:
            assign.right = str(node.right)
        elif hasattr(node, 'expression') and node.expression:
            assign.right = str(node.expression)
        
        # 延迟
        if hasattr(node, 'delay') and node.delay:
            assign.delay = str(node.delay)
        
        return assign if assign.left or assign.right else None
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        """提取"""
        tree = pyslang.SyntaxTree.fromText(code, source)
        assigns = self._extract_from_tree(tree.root)
        
        return [
            {
                'name': a.name,
                'left': a.left[:50],
                'right': a.right[:50],
                'delay': a.delay
            }
            for a in assigns
        ]


# ============================================================================
# 便捷函数
# ============================================================================

def extract_continuous_assigns(code: str) -> List[Dict]:
    """提取连续赋值"""
    extractor = ContinuousAssignExtractor()
    return extractor.extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
module test;
    wire [7:0] a = 8'h0;
    wire b = c;
    assign d = e;
    assign #5 f = g;
endmodule
'''
    
    print("=== Continuous Assign Extraction ===\n")
    
    result = extract_continuous_assigns(test_code)
    
    print(f"Found {len(result)} continuous assigns:")
    for r in result:
        delay_str = f", delay={r['delay']}" if r['delay'] else ""
        print(f"  {r['left']} = {r['right']}{delay_str}")
