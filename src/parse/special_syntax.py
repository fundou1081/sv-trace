
import sys
import os
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
import pyslang
from pyslang import SyntaxKind


@dataclass
class ForkJoinBlock:
    kind: str = ""


@dataclass
class TimeDelay:
    delay: str = ""


@dataclass
class SystemCall:
    name: str = ""


@dataclass
class DPIImport:
    name: str = ""


class SpecialSyntaxExtractor:
    def __init__(self, code):
        self.code = code
        self.fork_joins = []
        self.time_delays = []
        self.system_calls = []
        self.dpi_imports = []
        
        self._extract()
    
    def _extract(self):
        # Fork/Join
        for m in re.finditer(r'fork.+join', self.code):
            fk = ForkJoinBlock()
            if 'join_any' in m.group():
                fk.kind = 'join_any'
            elif 'join_none' in m.group():
                fk.kind = 'join_none'
            else:
                fk.kind = 'join'
            self.fork_joins.append(fk)
        
        # Time delays #<num>
        for m in re.finditer(r'#(\d+(?:\.\d+)?)(ns|us|ms|ps)?', self.code):
            self.time_delays.append(TimeDelay(delay=m.group()))
        
        # Cycle delay ##
        for m in re.finditer(r'##(\d+)', self.code):
            self.time_delays.append(TimeDelay(delay='##'+m.group(1)))
        
        # System function $
        for m in re.finditer(r'\$(\w+)', self.code):
            name = m.group(1)
            if name not in ['fopen', 'fclose', 'read', 'write', 'finish', 'fwrite', 'fdisplay']:
                self.system_calls.append(SystemCall(name=name))
        
        # DPI
        for m in re.finditer(r'import\s+"DPI"\s*(\w*)\s*(\w+)', self.code):
            self.dpi_imports.append(DPIImport(name=m.group(2)))
    
    def get_results(self):
        return {
            'fork_joins': self.fork_joins,
            'time_delays': self.time_delays,
            'system_calls': self.system_calls,
            'dpi_imports': self.dpi_imports
        }


def extract_special_syntax(code):
    return SpecialSyntaxExtractor(code).get_results()


if __name__ == "__main__":
    test_code = '''module m;
    fork #5; join_any
    #3ps sig = 1;
    ##1 sig2 = 1;
    $sformatf(s, "v: %d", d);
    $display("Hello");
    import "DPI" void test_import(input int a);
endmodule'''
    
    result = extract_special_syntax(test_code)
    
    print("=== 特殊语法 ===")
    print(f"Fork/Join: {len(result['fork_joins'])} - {[f.kind for f in result['fork_joins']]}")
    print(f"Time Delays: {[t.delay for t in result['time_delays']]}")
    print(f"System Calls: {[s.name for s in result['system_calls']]}")
    print(f"DPI: {[d.name for d in result['dpi_imports']]}")
