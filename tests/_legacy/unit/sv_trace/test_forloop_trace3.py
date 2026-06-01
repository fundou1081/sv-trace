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
        
        # Correct way to iterate members
        if hasattr(root, 'members') and root.members:
            for i in range(len(root.members)):
                member = root.members[i]
                print(f"member[{i}]: {type(member).__name__}")
                
                # Get module body
                if hasattr(member, 'body') and member.body:
                    for j in range(len(member.body)):
                        body_item = member.body[j]
                        print(f"  body[{j}]: {type(body_item).__name__}")
                        
                        if 'ProceduralBlock' in str(type(body_item)):
                            stmt = body_item.statement
                            print(f"    statement: {type(stmt).__name__}")
                            
                            if hasattr(stmt, 'items') and stmt.items:
                                for k in range(len(stmt.items)):
                                    item = stmt.items[k]
                                    print(f"    item[{k}]: {type(item).__name__}")
                                    
                                    if 'ForLoop' in str(type(item)):
                                        print(f"      === FOR LOOP FOUND ===")
                                        print(f"      has body: {hasattr(item, 'body')}")
                                        print(f"      body type: {type(item.body) if hasattr(item, 'body') else 'N/A'}")
finally:
    os.unlink(tmp)
