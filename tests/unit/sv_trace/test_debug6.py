import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

TEST = '''module t;
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
    f.write(TEST)
    tmp = f.name

try:
    parser = SVParser()
    parser.parse_file(tmp)
    for path, tree in parser.trees.items():
        root = tree.root
        
        def walk(node, depth=0):
            if not node:
                return
            print(f"{'  '*depth}{type(node).__name__}")
            for attr in ['members', 'body', 'statements', 'items', 'statement', 'elseClause']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                walk(c, depth+1)
                        elif 'ConditionalStatement' in str(type(node)):
                            # Special handling for conditional
                            print(f"{'  '*depth}  -> elseClause:")
                            walk(child, depth+2)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                walk(child[idx], depth+1)
                        else:
                            walk(child, depth+1)
        
        walk(root)
finally:
    os.unlink(tmp)
