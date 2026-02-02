from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os


load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY not set in environment")


def add_list_of_numbers_tool(numbers: list[int]) -> int:
    """
    Add a list of numbers.
    """
    print(f"[Tool] Adding numbers: {numbers}")
    return sum(numbers)


llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)


graph = create_agent(
    model=llm,
    tools=[add_list_of_numbers_tool],
    system_prompt=(
        "You are a helpful assistant. "
        "You can add numbers using the tool when needed. "
        "Only use the provided tools. "
        "Call a tool at most once and then respond."
    )
)


print("💬 Chat started. Type 'exit' or 'quit' to stop.\n")

while True:
    try:
        user_input = input("You: ").strip()

        if user_input.lower() in {"exit", "quit"}:
            print("\n👋 Goodbye!")
            break

        inputs = {
            "messages": [
                {"role": "user", "content": user_input}
            ]
        }

        result = graph.invoke(inputs)

        assistant_reply = result["messages"][-1].content
        print(f"Assistant: {assistant_reply}\n")

    except KeyboardInterrupt:
        print("\n👋 Chat ended.")
        break

    except Exception as e:
        print(f"\n⚠️ Error: {e}\n")
