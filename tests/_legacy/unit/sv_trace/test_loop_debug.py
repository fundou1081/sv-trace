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
        
        def walk(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ForLoop' in type_name:
                print(f"{'  '*depth}Found ForLoop:")
                print(f"{'  '*depth}  type: {type(node)}")
                print(f"{'  '*depth}  attributes: {[a for a in dir(node) if not a.startswith('_') and not a.isupper()]}")
            if 'DoWhileLoop' in type_name:
                print(f"{'  '*depth}Found DoWhileLoop:")
                print(f"{'  '*depth}  type: {type(node)}")
            if 'ForeachLoop' in type_name:
                print(f"{'  '*depth}Found ForeachLoop:")
                print(f"{'  '*depth}  type: {type(node)}")
            
            for attr in ['members', 'body', 'statements', 'items']:
                if hasattr(node, attr):
                    child = getattr(node, attr)
                    if child:
                        if isinstance(child, list):
                            for c in child:
                                walk(c, depth+1)
                        elif hasattr(child, "__len__") and hasattr(child, "__getitem__"):
                            for idx in range(len(child)):
                                walk(child[idx], depth+1)
                        else:
                            walk(child, depth+1)
        
        walk(root)
finally:
    os.unlink(tmp)
