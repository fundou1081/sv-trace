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
                
                if hasattr(member, 'members') and member.members:
                    for j in range(len(member.members)):
                        m = member.members[j]
                        
                        if 'ProceduralBlock' in str(type(m)):
                            stmt = m.statement
                            if hasattr(stmt, 'items') and stmt.items:
                                for k in range(len(stmt.items)):
                                    item = stmt.items[k]
                                    
                                    if 'ForLoop' in str(type(item)):
                                        print(f"ForLoop attributes:")
                                        attrs = [a for a in dir(item) if not a.startswith('_')]
                                        print(f"  {attrs}")
                                        # Check common attributes
                                        for attr in ['statement', 'loopBody', 'body', 'statements']:
                                            if hasattr(item, attr):
                                                print(f"  {attr}: {type(getattr(item, attr))}")
finally:
    os.unlink(tmp)
