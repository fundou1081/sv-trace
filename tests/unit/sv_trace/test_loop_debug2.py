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
        
        def find_always(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ProceduralBlock' in type_name:
                print(f"{'  '*depth}ProceduralBlock:")
                stmt = node.statement
                if hasattr(stmt, 'items') and stmt.items:
                    for idx in range(len(stmt.items)):
                        item = stmt.items[idx]
                        print(f"{'  '*depth}  item[{idx}]: {type(item).__name__}")
            
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    find_always(m, depth+1)
            if hasattr(node, 'body') and node.body:
                for b in node.body:
                    find_always(b, depth+1)
        
        find_always(root)
finally:
    os.unlink(tmp)
