import os
"""
特殊语法解析器 - 使用字符串提取

处理:
- fork...join/join_any/join_none
- #<time> 延迟
- DPI import/export
- $sformatf, $display 等系统函数
- ##<cycle> 延迟
"""
import sys
import re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dataclasses import dataclass, field
import pyslang


@dataclass
class ForkJoinBlock:
    kind: str = ""
    body: list = field(default_factory=list)


@dataclass
class TimeDelay:
    delay: str = ""


@dataclass
class SystemCall:
    name: str = ""
    args: list = field(default_factory=list)


@dataclass
class DPIImport:
    name: str = ""
    return_type: str = ""


class SpecialSyntaxExtractor:
    def __init__(self, code):
        self.code = code
        self.fork_joins = []
        self.time_delays = []
        self.system_calls = []
        self.dpi_imports = []
        
        self._extract()
    
    def _extract(self):
        # Fork...join
        for m in re.finditer(r'(fork\s*(?:join|join_any|join_none)?)\s*([^;]+(?:;[^{]+?)?end)', self.code, re.DOTALL):
            fk = ForkJoinBlock()
            if 'join_any' in m.group(1):
                fk.kind = 'join_any'
            elif 'join_none' in m.group(1):
                fk.kind = 'join_none'
            elif 'join' in m.group(1):
                fk.kind = 'join'
            else:
                fk.kind = 'fork'
            self.fork_joins.append(fk)
        
        # Time delays #<number>
        for m in re.finditer(r'#(\d+)(?:ns|us|ms|ps)?', self.code):
            self.time_delays.append(TimeDelay(delay=m.group()))
        
        for m in re.finditer(r'##(\d+)', self.code):
            self.time_delays.append(TimeDelay(delay='##' + m.group(1)))
        
        # System functions $name
        for m in re.finditer(r'\$(\w+)\s*\(([^)]*)\)', self.code):
            sc = SystemCall(name=m.group(1), args=m.group(2).split(','))
            self.system_calls.append(sc)
        
        # DPI import
        for m in re.finditer(r'import\s+"DPI"\s*(\w*)\s*(\w+)\s*\(', self.code):
            dpi = DPIImport()
            dpi.return_type = m.group(1) or "void"
            dpi.name = m.group(2)
            self.dpi_imports.append(dpi)
    
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
    // fork...join
    fork
        #5;
        #10;
    join_any
    
    // time delay
    #3ps data = 1;
    #10ns addr = 0;
    ##1 ack = 1;
    
    // system function
    initial begin
        string s;
        $sformatf(s, "Value: %d", data);
        $display("Hello");
    end
    
    // DPI import
    import "DPI" void test_import(input int a);
    import "DPI" context int test_context();
endmodule'''
    
    result = extract_special_syntax(test_code)
    
    print("=== 特殊语法 ===")
    print(f"\nFork/Join ({len(result['fork_joins'])}):")
    for f in result['fork_joins']:
        print(f"  {f.kind}")
    
    print(f"\nTime Delays ({len(result['time_delays'])}):")
    for t in result['time_delays']:
        print(f"  {t.delay}")
    
    print(f"\nSystem Calls ({len(result['system_calls'])}):")
    for s in result['system_calls']:
        print(f"  ${s.name}")
    
    print(f"\nDPI Imports ({len(result['dpi_imports'])}):")
    for d in result['dpi_imports']:
        print(f"  {d.return_type} {d.name}")
