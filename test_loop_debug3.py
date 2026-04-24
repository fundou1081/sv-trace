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
        
        def find_loops(node, depth=0):
            if not node:
                return
            type_name = str(type(node))
            if 'ForLoopStatement' in type_name:
                print(f"{'  '*depth}ForLoopStatement:")
                print(f"{'  '*depth}  dir: {[a for a in dir(node) if not a.startswith('_')]}")
                if hasattr(node, 'body'):
                    print(f"{'  '*depth}  body: {type(node.body)}")
                if hasattr(node, 'initializer'):
                    print(f"{'  '*depth}  initializer: {type(node.initializer)}")
                if hasattr(node, 'condition'):
                    print(f"{'  '*depth}  condition: {node.condition}")
                if hasattr(node, 'increment'):
                    print(f"{'  '*depth}  increment: {node.increment}")
            
            if hasattr(node, 'items'):
                for i in range(len(node.items)):
                    find_loops(node.items[i], depth)
            if hasattr(node, 'members') and node.members:
                for m in node.members:
                    find_loops(m, depth+1)
            if hasattr(node, 'body') and node.body:
                find_loops(node.body, depth+1)
            if hasattr(node, 'body') and node.body:
                if isinstance(node.body, list):
                    for b in node.body:
                        find_loops(b, depth+1)
        
        find_loops(root)
finally:
    os.unlink(tmp)
