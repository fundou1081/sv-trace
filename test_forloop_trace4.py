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
        
        if hasattr(root, 'members') and root.members:
            for i in range(len(root.members)):
                member = root.members[i]
                print(f"member[{i}]: {type(member).__name__}")
                print(f"  attrs: {[a for a in dir(member) if not a.startswith('_')][:15]}")
                
                if hasattr(member, 'body'):
                    print(f"  body: {member.body}")
                    
                    if member.body:
                        print(f"  body len: {len(member.body)}")
                        for j in range(len(member.body)):
                            print(f"    body[{j}]: {type(member.body[j]).__name__}")
finally:
    os.unlink(tmp)
