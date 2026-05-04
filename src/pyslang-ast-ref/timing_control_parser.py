"""
Timing Control Parser - 使用正确的 AST 遍历

提取时序控制语句：
- TimingControlStatement
- SignalEventExpression
- EventControlWithExpression
- DelayControl
- ParenthesizedEventExpression

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
class TimingControl:
    control_type: str = ""  # delay, event, etc.
    expression: str = ""


class TimingControlExtractor:
    def __init__(self):
        self.controls: List[TimingControl] = []
    
    def _extract_from_tree(self, root):
        def collect(node):
            try:
                kind_name = node.kind.name if hasattr(node.kind, 'name') else str(node.kind)
            except:
                return pyslang.VisitAction.Advance
            
            if kind_name == 'TimingControlStatement':
                tc = TimingControl()
                tc.control_type = 'timing_control'
                if hasattr(node, 'control') and node.control:
                    tc.expression = str(node.control)[:50]
                self.controls.append(tc)
            
            elif kind_name == 'SignalEventExpression':
                tc = TimingControl()
                tc.control_type = 'signal_event'
                if hasattr(node, 'expression') and node.expression:
                    tc.expression = str(node.expression)
                self.controls.append(tc)
            
            elif kind_name == 'EventControlWithExpression':
                tc = TimingControl()
                tc.control_type = 'event_control'
                if hasattr(node, 'expression') and node.expression:
                    tc.expression = str(node.expression)
                self.controls.append(tc)
            
            elif kind_name == 'DelayControl':
                tc = TimingControl()
                tc.control_type = 'delay'
                if hasattr(node, 'delay') and node.delay:
                    tc.expression = str(node.delay)
                self.controls.append(tc)
            
            elif kind_name == 'ParenthesizedEventExpression':
                tc = TimingControl()
                tc.control_type = 'parenthesized_event'
                self.controls.append(tc)
            
            return pyslang.VisitAction.Advance
        
        root.visit(collect)
    
    def extract_from_text(self, code: str, source: str = "<text>") -> List[Dict]:
        tree = pyslang.SyntaxTree.fromText(code, source)
        self._extract_from_tree(tree.root)
        return [
            {'type': tc.control_type, 'expr': tc.expression[:30]}
            for tc in self.controls[:20]
        ]


def extract_timing_controls(code: str) -> List[Dict]:
    return TimingControlExtractor().extract_from_text(code)


if __name__ == "__main__":
    test_code = '''
always @(posedge clk) begin
    #10 data = 0;
    @(posedge clk);
end
'''
    result = extract_timing_controls(test_code)
    print(f"Timing controls: {len(result)}")
