import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

tests = [
    ("Simple Assign", '''module t; logic a, b; assign b = a; endmodule''', 'b'),
    ("If/Else", '''module t; logic a, b, r; always_comb begin if (a) r = b; else r = 0; end endmodule''', 'r'),
    ("Case", '''module t; logic [1:0] s; logic a, b, r; always_comb case(s) 0: r=a; 1: r=b; endcase endmodule''', 'r'),
    ("For Loop", '''module t; logic [31:0] sum; always_comb begin sum=0; for(int i=0;i<4;i++) sum=sum+i; end endmodule''', 'sum'),
    ("While Loop", '''module t; logic [31:0] cnt; always_comb begin cnt=0; while(cnt<10) cnt=cnt+1; end endmodule''', 'cnt'),
    ("Foreach", '''module t; logic [31:0] arr [3:0], sum; always_comb begin sum=0; foreach(arr[i]) sum=sum+arr[i]; end endmodule''', 'sum'),
    ("Always_ff", '''module t; logic clk, d, q; always_ff @(posedge clk) q <= d; endmodule''', 'q'),
]

all_passed = True
for name, code, signal in tests:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        drv = DriverTracer(parser)
        drivers = drv.find_driver(signal)
        status = "✅" if drivers else "❌"
        print(f"{status} {name}: {len(drivers)} drivers")
        if not drivers:
            all_passed = False
    except Exception as e:
        print(f"❌ {name}: ERROR - {e}")
        all_passed = False
    finally:
        os.unlink(tmp)

print()
print("All tests passed!" if all_passed else "SOME TESTS FAILED!")
