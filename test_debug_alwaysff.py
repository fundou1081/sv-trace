import sys, os, tempfile
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')

from parse import SVParser

TEST = '''module t;
    logic [31:0] data, r;
    logic clk, rst, valid;
    always_ff @(posedge clk) begin
        if (rst)
            r <= 0;
        else if (valid)
            r <= data;
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
            if 'ProceduralBlock' in type_name:
                print(f"{'  '*depth}ProceduralBlock: {type_name}")
                print(f"{'  '*depth}  statement: {type(node.statement)}")
                if hasattr(node.statement, 'timingControl'):
                    print(f"{'  '*depth}  timingControl: {node.statement.timingControl}")
                # Check body
                if hasattr(node.statement, 'body'):
                    print(f"{'  '*depth}  body type: {type(node.statement.body)}")
            
            for attr in ['members', 'body']:
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
