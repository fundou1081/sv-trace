"""
控制流分析应用 - 分析代码的控制流结构
"""
import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parse import SVParser
from dataclasses import dataclass
from typing import Dict, List, Set, Optional


@dataclass
class ControlBlock:
    kind: str
    block_type: str
    condition: str = ""
    body: str = ""
    line: int = 0


@dataclass
class StateMachine:
    name: str
    states: List[str]
    
    def __init__(self, name: str = "", states: List[str] = None):
        self.name = name
        self.states = states or []


class ControlFlowAnalyzer:
    def __init__(self):
        self.parser = SVParser()
        self.control_blocks: List[ControlBlock] = []
        self.state_machines: List[StateMachine] = []
    
    def load_file(self, filepath: str):
        with open(filepath, 'r') as f:
            code = f.read()
        self.parser.parse_text(code)
        self._extract_control_flow()
    
    def _extract_control_flow(self):
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            
            if hasattr(root, 'members') and root.members:
                for m in root.members:
                    self._find_control_in_member(m)
    
    def _find_control_in_member(self, member):
        type_name = str(type(member))
        body_str = str(member)
        
        line = 0
        if hasattr(member, 'sourceRange') and member.sourceRange:
            line = member.sourceRange.start.offset
        
        kind = "ProceduralBlock"
        if 'always_ff' in body_str:
            kind = "always_ff"
        elif 'always_comb' in body_str:
            kind = "always_comb"
        elif 'always_latch' in body_str:
            kind = "always_latch"
        elif 'initial' in body_str:
            kind = "initial"
        
        if 'Procedural' in type_name or 'always' in body_str or 'initial' in body_str:
            block = ControlBlock(
                kind=kind,
                block_type="procedural",
                body=body_str[:200],
                line=line
            )
            
            sens_match = re.search(r'@(.*?)(?:begin|$)', body_str)
            if sens_match:
                block.condition = sens_match.group(1).strip()
            
            self.control_blocks.append(block)
        
        for attr in ['body', 'members', 'statements']:
            if hasattr(member, attr):
                child = getattr(member, attr)
                if child:
                    if isinstance(child, list):
                        for c in child:
                            self._find_control_in_member(c)
                    else:
                        self._find_control_in_member(child)
    
    def find_always_ff(self) -> List[ControlBlock]:
        return [b for b in self.control_blocks if b.kind == "always_ff"]
    
    def find_always_comb(self) -> List[ControlBlock]:
        return [b for b in self.control_blocks if b.kind == "always_comb"]
    
    def find_state_machines(self) -> List[StateMachine]:
        for key, tree in self.parser.trees.items():
            if not tree or not hasattr(tree, 'root') or not tree.root:
                continue
            
            root = tree.root
            root_str = str(root)
            
            enum_matches = re.findall(r'typedef\s+enum\s+.*?\{\s*(.*?)\s*\}\s*(\w+)', root_str, re.DOTALL)
            
            for enum_body, enum_name in enum_matches:
                states = [s.split('=')[0].strip() for s in enum_body.split(',') if s.strip()]
                
                if 'always_ff' in root_str and ('next_state' in root_str or 'state' in root_str):
                    sm = StateMachine(name=enum_name, states=states)
                    self.state_machines.append(sm)
        
        return self.state_machines
    
    def analyze(self, module_name: str = None):
        print(f"\n{'='*60}")
        print(f"控制流分析")
        print(f"{'='*60}")
        
        always_ff = self.find_always_ff()
        print(f"\nAlways_ff: {len(always_ff)}")
        for b in always_ff[:3]:
            print(f"  - 敏感: {b.condition or '(none)'}")
        
        always_comb = self.find_always_comb()
        print(f"\nAlways_comb: {len(always_comb)}")
        
        sms = self.find_state_machines()
        print(f"\n状态机: {len(sms)}")
        for sm in sms:
            print(f"  - {sm.name}: {sm.states}")


def demo():
    code = '''
module fsm (
    input clk,
    input rst_n,
    input go,
    output done
);
    
    typedef enum logic [1:0] {
        IDLE = 2'b00,
        RUN  = 2'b01,
        DONE = 2'b10
    } state_t;
    
    state_t state, next_state;
    
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            state <= IDLE;
        else
            state <= next_state;
    end
    
    always_comb begin
        next_state = state;
        case (state)
            IDLE: if (go) next_state = RUN;
            RUN:  next_state = DONE;
            DONE: next_state = IDLE;
        endcase
    end
    
    assign done = (state == DONE);
    
endmodule
'''
    
    analyzer = ControlFlowAnalyzer()
    analyzer.parser.parse_text(code)
    analyzer._extract_control_flow()
    analyzer.analyze()


if __name__ == "__main__":
    demo()
