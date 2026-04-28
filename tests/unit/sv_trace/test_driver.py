import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

# Test simple if/else
TEST1 = '''module t;
    logic [31:0] a, b, r;
    logic cond;
    always_comb begin
        if (cond)
            r = a;
        else
            r = b;
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST1)
    tmp1 = f.name

try:
    parser1 = SVParser()
    parser1.parse_file(tmp1)
    drv1 = DriverTracer(parser1)
    drivers1 = drv1.find_driver('r')
    print(f'=== Simple If/Else ===')
    print(f'Drivers for r: {len(drivers1)}')
    for d in drivers1:
        print(f'  - kind={d.kind}, source={d.sources[0].strip()[:60]}')
    print()
finally:
    os.unlink(tmp1)

# Test nested if/else-if/else
TEST2 = '''module t;
    logic [31:0] a, b, c, r;
    logic [1:0] sel;
    always_comb begin
        if (sel == 2'b00)
            r = a;
        else if (sel == 2'b01)
            r = b;
        else
            r = c;
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST2)
    tmp2 = f.name

try:
    parser2 = SVParser()
    parser2.parse_file(tmp2)
    drv2 = DriverTracer(parser2)
    drivers2 = drv2.find_driver('r')
    print(f'=== Nested If/Else-If/Else ===')
    print(f'Drivers for r: {len(drivers2)}')
    for d in drivers2:
        print(f'  - kind={d.kind}, source={d.sources[0].strip()[:60]}')
finally:
    os.unlink(tmp2)
