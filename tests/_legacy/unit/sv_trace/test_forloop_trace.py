import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser
import traceback

TEST = '''module t;
    logic [31:0] i, sum, data [0:3];
    always_comb begin
        sum = 0;
        for (int i = 0; i < 4; i++) begin
            sum = sum + data[i];
        end
    end
endmodule'''

with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
    f.write(TEST)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    print("Parse OK", file=sys.stderr)
    
    for path, tree in parser.trees.items():
        root = tree.root
        
        modules = []
        if 'ModuleDeclaration' in str(type(root)):
            modules = [root]
        
        print(f"Modules: {len(modules)}", file=sys.stderr)
        
        for module in modules:
            print(f"Module body: {hasattr(module, 'body')}", file=sys.stderr)
            if hasattr(module, 'body') and module.body:
                print(f"Body items: {len(module.body)}", file=sys.stderr)
                for idx, b in enumerate(module.body):
                    print(f"  body[{idx}]: {type(b).__name__}", file=sys.stderr)
                    if 'ProceduralBlock' in str(type(b)):
                        print(f"    -> ProceduralBlock", file=sys.stderr)
                        stmt = b.statement
                        print(f"    statement: {type(stmt)}", file=sys.stderr)
                        if hasattr(stmt, 'items') and stmt.items:
                            print(f"    items: {len(stmt.items)}", file=sys.stderr)
                            for i, item in enumerate(stmt.items):
                                print(f"      item[{i}]: {type(item).__name__}", file=sys.stderr)
                                if 'ForLoop' in str(type(item)):
                                    print(f"        FORLOOP FOUND!", file=sys.stderr)
                                    
except Exception as e:
    traceback.print_exc()
finally:
    os.unlink(tmp)
