from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


from Navigation.Browser.manager import BrowserManager
from Navigation.Tools.actions import ActionTools
from Navigation.Tools.perception import PerceptionTools
from Navigation.Tools.navigation import NavigationTools
from Navigation.Tools.Models.element import ElementStore

session = BrowserManager(headless=False)
navigation_tools = NavigationTools(session)
element_store = ElementStore() 
perception_tools = PerceptionTools(session, element_store)
action_tools = ActionTools(session, element_store, perception_tools, file_path="")

from concurrent.futures import ThreadPoolExecutor

browser_executor = ThreadPoolExecutor(max_workers=1)


@tool
def open_page(url: str) -> str:
    """Opens a webpage"""
    future = browser_executor.submit(navigation_tools.open_page, url)
    return future.result()

@tool
def click_elements(element_ids:list[str]) -> str:
    """Click elements matching the element ids"""
    future = browser_executor.submit(action_tools.click_elements, element_ids)
    return future.result()

@tool
def type_in_elements(entries: list[dict]) -> str:
    """Type in elements matching the element ids"""
    future = browser_executor.submit(action_tools.type_in_elements, entries)
    return future.result()

@tool
def extract_elements() -> str:
    """Extract elements in the page for understanding the page structure"""
    future = browser_executor.submit(perception_tools.take_snapshot)
    return future.result()

tools = [open_page, click_elements, type_in_elements, extract_elements]

# ---- LLM ----
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash",   
#     temperature=0
# )


# ---- Create Agent ----
agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt="""
You are an assistant for web navigation and interaction. You can use the following tools to interact with web pages:
1. open_page(url: str) -> str: Opens a webpage given a URL.
2. click_elements(element_ids: list[str]) -> str: Clicks on elements identified by their element IDs.
3. type_in_elements(entries: list[dict]) -> str: Types text into elements identified
4. extract_elements() -> str: Extracts elements from the current page to understand its structure. This tool returns all 
the elements including their element IDs and text content.

User Details:
Name: Abhijeet
CGPA: 9.5
phone number: 1234567890
email:xyz@gmail.com
class:computer science

    """
)

# ---- Run Loop ----
print("Type 'exit' to quit")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ["exit", "quit"]:
        break

    result = agent.invoke({
        "messages": [HumanMessage(content=user_input)]
    })

    print("Agent:", result["messages"][-1].content)




# You: https://docs.google.com/forms/d/e/1FAIpQLSc4iTT49seK6JaNWqFjZCym2ifMRnA9HV1v7VLV9tzRoO4V2w/viewform?usp=header open this form, extract elements in this pagae and click on any one option at random