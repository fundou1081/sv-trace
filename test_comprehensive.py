import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace.driver import DriverTracer

tests = [
    ("Simple If/Else", '''module t;
        logic [31:0] a, b, r;
        logic cond;
        always_comb begin
            if (cond)
                r = a;
            else
                r = b;
        end
    endmodule''', 'r'),
    
    ("Nested If/Else-If/Else", '''module t;
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
    endmodule''', 'r'),
    
    ("Case Statement", '''module t;
        logic [7:0] a, b, c, r;
        logic [1:0] op;
        always_comb begin
            case(op)
                0: c = a + b;
                1: c = a - b;
                default: c = 0;
            endcase
            r = c + 1;
        end
    endmodule''', 'c'),
    
    ("Always_ff", '''module t;
        logic [31:0] data, r;
        logic clk, rst, valid;
        always_ff @(posedge clk) begin
            if (rst)
                r <= 0;
            else if (valid)
                r <= data;
        end
    endmodule''', 'r'),
    
    ("Mixed If/Case", '''module t;
        logic [31:0] a, b, c, r;
        logic [1:0] sel;
        logic mode;
        always_comb begin
            if (mode)
                r = a + b;
            else begin
                case (sel)
                    0: r = a;
                    1: r = b;
                    default: r = c;
                endcase
            end
        end
    endmodule''', 'r'),
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
            src = d.source_expr.strip()[:50].replace('\n', ' ')
            print(f"  - {d.driver_kind.name}: {src}")
        print()
    except Exception as e:
        print(f"=== {name} ===")
        print(f"ERROR: {e}")
        print()
    finally:
        os.unlink(tmp)
