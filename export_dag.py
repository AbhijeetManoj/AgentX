import re
from app import agent

# Get the mermaid representation
try:
    mermaid_str = agent.get_graph().draw_mermaid()
    
    # Write to a JS file that exports it
    js_content = f"export const DAG_MERMAID = `{mermaid_str}`;\n"
    
    with open("frontend/src/dagMermaid.js", "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print("Successfully exported DAG to frontend/src/dagMermaid.js")
except Exception as e:
    print(f"Error exporting DAG: {e}")
