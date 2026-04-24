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
        print(f"Root type: {type(root)}")
        print(f"Root: {root}")
        
        # Check what attributes root has
        print(f"Root dir: {[a for a in dir(root) if not a.startswith('_')][:10]}")
        
        # Try to get members
        if hasattr(root, 'members'):
            print(f"Root has members: {root.members}")
            if root.members:
                print(f"Members count: {len(root.members)}")
                for i in range(len(root.members)):
                    print(f"  member[{i}]: {type(root.members[i]).__name__}")
finally:
    os.unlink(tmp)
