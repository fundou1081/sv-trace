import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

tests = [
    ("For Loop", '''module t;
        logic [31:0] i, sum, data [0:3];
        always_comb begin
            sum = 0;
            for (int i = 0; i < 4; i++) begin
                sum = sum + data[i];
            end
        end
    endmodule''', 'sum'),
    
    ("While Loop", '''module t;
        logic [31:0] cnt, max_val;
        logic valid;
        always_comb begin
            cnt = 0;
            while (cnt < max_val && valid) begin
                cnt = cnt + 1;
            end
        end
    endmodule''', 'cnt'),
    
    ("Do-While", '''module t;
        logic [31:0] cnt;
        always_comb begin
            do begin
                cnt = cnt - 1;
            end while (cnt > 0);
        end
    endmodule''', 'cnt'),
    
    ("Foreach", '''module t;
        logic [31:0] arr [0:3], sum;
        always_comb begin
            sum = 0;
            foreach (arr[i]) begin
                sum = sum + arr[i];
            end
        end
    endmodule''', 'sum'),
]

for name, code, signal in tests:
    with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
        f.write(code)
        tmp = f.name
    
    try:
        parser = SVParser()
        parser.parse_file(tmp)
        drv = DriverTracer(parser)
        drivers = drv.find_driver(signal)
        print(f"=== {name} ===")
        print(f"Signal: {signal}, Drivers: {len(drivers)}")
        for d in drivers:
            src = d.source_expr.strip()[:60].replace('\n', ' ')
            print(f"  - {d.driver_kind.name}: {src}")
        if not drivers:
            print("  (no drivers found)")
        print()
    except Exception as e:
        print(f"=== {name} ===")
        print(f"ERROR: {e}")
        print()
    finally:
        os.unlink(tmp)
