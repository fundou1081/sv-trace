import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

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
    for path, tree in parser.trees.items():
        root = tree.root
        
        def walk_all(node, depth=0):
            if not node:
                return
            print(f"{'  '*depth}{type(node).__name__}")
            
            # Stop after going too deep
            if depth > 8:
                return
            
            for attr in ['members', 'body', 'statements', 'items']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                walk_all(c, depth+1)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                walk_all(child[idx], depth+1)
        
        walk_all(root)
finally:
    os.unlink(tmp)
