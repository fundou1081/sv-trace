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
        
        # Manually walk down to the always block
        if hasattr(root, 'members') and root.members:
            for i in range(len(root.members)):
                m = root.members[i]
                print(f"  member[{i}]: {type(m).__name__}")
                if hasattr(m, 'body') and m.body:
                    for j in range(len(m.body)):
                        b = m.body[j]
                        print(f"    body[{j}]: {type(b).__name__}")
                        if 'ProceduralBlock' in str(type(b)):
                            stmt = b.statement
                            print(f"      statement: {type(stmt)}")
                            if hasattr(stmt, 'items') and stmt.items:
                                for k in range(len(stmt.items)):
                                    it = stmt.items[k]
                                    print(f"        item[{k}]: {type(it).__name__}")
                                    if 'ForLoop' in str(type(it)):
                                        print(f"          Found ForLoop!")
                                        print(f"          body: {type(it.body) if hasattr(it, 'body') else 'N/A'}")
finally:
    os.unlink(tmp)
