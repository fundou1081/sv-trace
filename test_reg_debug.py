import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

code = '''module t;
    logic [31:0] reg1;
    logic clk, rst;
    always_ff @(posedge clk) begin
        if (rst)
            reg1 <= 0;
        else
            reg1 <= 1;
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(code)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    
    drv = DriverTracer(parser)
    drivers = drv.find_driver('reg1')
    
    print(f"Drivers for reg1: {len(drivers)}")
    for d in drivers:
        print(f"  [{d.driver_kind.name}] expr: {d.source_expr}")
        print(f"    lower: {d.source_expr.lower()}")
        print(f"    has rst: {'rst' in d.source_expr.lower()}")
        print(f"    has <= 0: {'<= 0' in d.source_expr}")
finally:
    os.unlink(tmp)
