"""Debug dcr port direction"""
import sys
sys.path.insert(0, '/Users/fundou/my_dv_proj/sv-trace/src')
from parse import SVParser
import pyslang

parser = SVParser()
parser.parse_file('/Users/fundou/my_dv_proj/tiny-gpu/src/dcr.sv')

for tree in parser.trees.values():
    for i in range(len(tree.root.members)):
        m = tree.root.members[i]
        if hasattr(m, 'header') and m.header:
            if m.header.name.value == 'dcr':
                header = m.header
                
                if hasattr(header, 'ports') and header.ports and len(header.ports) > 1:
                    port_list = header.ports[1]
                    
                    for j in range(len(port_list)):
                        item = port_list[j]
                        if type(item).__name__ != 'ImplicitAnsiPortSyntax':
                            continue
                        
                        port_name = item.declarator.name.value if hasattr(item.declarator, 'name') else ""
                        
                        # Get direction
                        header_val = item.header
                        direction = "unknown"
                        
                        print(f"Port: {port_name}")
                        print(f"  header type: {type(header_val).__name__}")
                        print(f"  header: {header_val}")
                        
                        if hasattr(header_val, 'direction'):
                            dir_token = header_val.direction
                            print(f"  direction: {dir_token}")
                            print(f"  direction kind: {dir_token.kind}")
                            print(f"  Is InputKeyword: {dir_token.kind == pyslang.TokenKind.InputKeyword}")
                            print(f"  Is OutputKeyword: {dir_token.kind == pyslang.TokenKind.OutputKeyword}")
