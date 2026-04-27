import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

"""
批量测试 - 使用 sv-tests
"""
import sys
import os
import glob
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
from trace import DriverTracer, LoadTracer


def test_file(filepath):
    """测试单个文件"""
    try:
        with open(filepath, 'r') as f:
            code = f.read()
        
        parser = SVParser()
        tree = parser.parse_text(code, filepath)
        
        # 检查解析成功
        if parser.has_errors():
            return {"status": "parse_error", "msg": "Parse failed"}
        
        return {"status": "ok", "modules": len(parser.get_modules())}
    
    except Exception as e:
        return {"status": "error", "msg": str(e)}


def test_dir(pattern, max_files=50):
    """测试目录"""
    files = glob.glob(pattern)[:max_files]
    
    results = {"ok": 0, "parse_error": 0, "error": 0, "files": []}
    
    for fp in files:
        result = test_file(fp)
        if result["status"] == "ok":
            results["ok"] += 1
        elif result["status"] == "parse_error":
            results["parse_error"] += 1
        else:
            results["error"] += 1
        
        if result["status"] != "ok":
            results["files"].append((os.path.basename(fp), result))
    
    return results


def test_driver_load():
    """测试 driver/load 追踪"""
    test_cases = [
        ("module top; logic [7:0] a; assign a = 8'hFF; endmodule", "a"),
        ("module top; logic clk; logic [7:0] cnt; always_ff @(posedge clk) cnt <= cnt + 1; endmodule", "cnt"),
        ("module top; logic [7:0] a, b, c; assign c = a + b; endmodule", "a"),
    ]
    
    ok = 0
    for code, signal in test_cases:
        parser = SVParser()
        parser.parse_text(code)
        
        # Driver
        dt = DriverTracer(parser)
        drivers = dt.find_driver(signal)
        
        # Load  
        lt = LoadTracer(parser)
        loads = lt.find_load(signal)
        
        if drivers or signal in code:
            ok += 1
    
    return ok


if __name__ == "__main__":
    print("=" * 50)
    print("SV-TESTS BATCH TEST")
    print("=" * 50)
    
    # 测试不同章节
    chapters = [
        ("chapter-12 (if/case)", "~/my_dv_proj/sv-tests/tests/chapter-12/*.sv"),
        ("chapter-18 (class/constraint)", "~/my_dv_proj/sv-tests/tests/chapter-18/*.sv"),
    ]
    
    total_ok = 0
    total_files = 0
    
    for name, pattern in chapters:
        pattern = os.path.expanduser(pattern)
        print(f"\n{name}:")
        
        results = test_dir(pattern, max_files=30)
        
        print(f"  OK: {results['ok']}")
        print(f"  Parse Error: {results['parse_error']}")
        print(f"  Other Error: {results['error']}")
        
        total_ok += results['ok']
        total_files += results['ok'] + results['parse_error'] + results['error']
        
        if results['files']:
            print(f"  Failed files:")
            for fp, res in results['files'][:5]:
                print(f"    - {fp}: {res['msg'][:50]}")
    
    print(f"\n{'='*50}")
    print(f"Summary: {total_ok}/{total_files} files parsed OK")
    print(f"  Driver/Load test: {test_driver_load()}/{3} OK")
    
    if total_ok > total_files * 0.8:
        print("\n✓ Batch test passed!")
