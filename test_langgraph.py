
try:
    from langgraph.prebuilt import create_react_agent
    print("SUCCESS: create_react_agent imported!")
except ImportError as e:
    print(f"FAILURE: {e}")
