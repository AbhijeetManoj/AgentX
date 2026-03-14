from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.tools import tool

from langchain_core.prompts import ChatPromptTemplate

from Navigation.Browser.manager import BrowserManager
from Navigation.Tools.actions import ActionTools
from Navigation.Tools.perception import PerceptionTools
from Navigation.Tools.navigation import NavigationTools
from Navigation.Tools.Models.element import ElementStore
from Navigation.Tools.google_services import GoogleServiceManager

session = BrowserManager(headless=False)
navigation_tools = NavigationTools(session)
element_store = ElementStore() 
perception_tools = PerceptionTools(session, element_store)
action_tools = ActionTools(session, element_store, perception_tools, file_path="")

from concurrent.futures import ThreadPoolExecutor

browser_executor = ThreadPoolExecutor(max_workers=1)

try:
    google_manager = GoogleServiceManager()
    print("Google Services initialized successfully.")
except Exception as e:
    print(f"Warning: Google Services failed to initialize. Ensure credentials.json is present. Error: {e}")
    google_manager = None


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

@tool
def get_resume(filename: str = "resume") -> str:
    """
    Search for a resume PDF in Google Drive and return its text content.
    Args:
        filename (str): The name (or partial name) of the file to search for. Defaults to "resume".
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.get_resume_text(filename)

@tool
def schedule_interview(summary: str, start_time: str, duration: int = 60) -> str:
    """
    Schedule an interview on Google Calendar.
    Args:
        summary (str): Title of the event (e.g., "Interview with Company X").
        start_time (str): Start time in ISO format (e.g., "2023-10-27T10:00:00").
        duration (int): Duration in minutes. Defaults to 60.
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.schedule_event(summary, start_time, duration)

@tool
def get_unread_emails() -> str:
    """
    Get a summary of unread emails in the inbox.
    Returns: A formatted string of unread emails with sender, subject, and snippet.
    """
    if not google_manager:
        return "Google Services not initialized."
    emails = google_manager.search_emails(query='is:unread', max_results=5)
    if not emails:
        return "No unread emails found."

    result = "Unread Emails:\n"
    for email in emails:
        result += f"- [From: {email.get('sender', 'Unknown')}]\n  Subject: {email['subject']}\n  Date: {email['date']}\n  Snippet: {email['snippet']}\n\n"
    return result

@tool
def get_recent_emails(query: str = "", max_results: int = 5) -> str:
    """
    Get recent emails. Can filter by query.
    Args:
        query (str): Optional search query. defaults to "" (all emails).
        max_results (int): Number of emails to retrieve. Defaults to 5.
    """
    if not google_manager:
        return "Google Services not initialized."
    
    if not query:
        query = "category:primary" # Default to primary inbox if no query

    emails = google_manager.search_emails(query, max_results)
    if not emails:
        return "No emails found."
    
    # Format for the LLM
    result = f"Recent {len(emails)} Emails:\n"
    for email in emails:
        result += f"Subject: {email['subject']}\nFrom: {email.get('sender', 'Unknown')}\nDate: {email['date']}\nSnippet: {email['snippet']}\n\n"
    return result

@tool
def send_or_draft_email(to: str, subject: str, message_text: str, is_draft: bool = False) -> str:
    """
    Send an email or create a draft.
    Args:
        to (str): Recipient email address.
        subject (str): Email subject.
        message_text (str): Body of the email.
        is_draft (bool): Set to True to save as draft instead of sending. Defaults to False.
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.send_or_draft_email(to, subject, message_text, is_draft)

@tool
def schedule_email(to: str, subject: str, message_text: str, send_at_iso: str) -> str:
    """
    Schedule an email to be sent at a specific time.
    Args:
        to (str): Recipient email address.
        subject (str): Email subject.
        message_text (str): Body of the email.
        send_at_iso (str): Time to send the email in ISO format (e.g., '2023-10-27T10:00:00').
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.schedule_email(to, subject, message_text, send_at_iso)

@tool
def read_google_sheet(spreadsheet_id: str, range_name: str) -> str:
    """
    Read data from a Google Sheet.
    Args:
        spreadsheet_id (str): The ID of the spreadsheet (found in its URL).
        range_name (str): The A1 notation of the values to retrieve (e.g. 'Sheet1!A1:D10').
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.get_sheet_data(spreadsheet_id, range_name)

@tool
def write_google_sheet(spreadsheet_id: str, range_name: str, values: list) -> str:
    """
    Write a 2D array of data to a Google Sheet.
    Args:
        spreadsheet_id (str): The ID of the spreadsheet.
        range_name (str): The A1 notation of the values to update (e.g. 'Sheet1!A1:D10').
        values (list): A list of lists representing rows and columns, e.g., [['Name', 'Age'], ['Alice', 30]].
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.update_sheet_data(spreadsheet_id, range_name, values)

@tool
def convert_text_to_speech(text: str, filename: str = "output.mp3") -> str:
    """
    Convert text to an MP3 audio file using Google Translate Text-to-Speech (gTTS).
    Args:
        text (str): The text to convert to speech.
        filename (str): The output file name. Defaults to "output.mp3".
    """
    if not google_manager:
        return "Google Services not initialized."
    return google_manager.text_to_speech(text, filename)

tools = [open_page, click_elements, type_in_elements, extract_elements, get_resume, schedule_interview, get_recent_emails, get_unread_emails, send_or_draft_email, schedule_email, read_google_sheet, write_google_sheet, convert_text_to_speech]

from langgraph.prebuilt import create_react_agent

# ---- LLM ----
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    model_kwargs={"parallel_tool_calls": False}  # ← passed directly to Groq API
)

# ---- Create Agent ----
system_prompt = """
You are an assistant for web navigation and integration. You are capable of navigating the web, interacting with page elements, reading resumes from Google Drive, managing emails, and scheduling interviews on Google Calendar.

Available Tools:
1. open_page(url): Opens a webpage.
2. click_elements(element_ids): Clicks elements by ID.
3. type_in_elements(entries): Types text into elements.
4. extract_elements(): Extracts page structure/elements.
5. get_resume(filename): Reads resume text from Drive.
6. schedule_interview(summary, start_time, duration): Schedules calendar events.
7. get_recent_emails(query, max_results): Gets recent emails. Use this for general email checking.
8. get_unread_emails(): Gets a summary of unread emails.
9. send_or_draft_email(to, subject, message_text, is_draft): Sends an email or creates a draft.
10. schedule_email(to, subject, message_text, send_at_iso): Schedules an email to be sent at a specific time.
11. read_google_sheet(spreadsheet_id, range_name): Read data from a Google Sheet.
12. write_google_sheet(spreadsheet_id, range_name, values): Write an array of data to a Google Sheet.
13. convert_text_to_speech(text, filename): Convert text to speech audio file using Google TTS.

User Details:
Name: Abhijeet
CGPA: 9.5
Phone: 1234567890
Email: xyz@gmail.com
Class: Computer Science

Instructions:
- Use the provided tools to complete the user's request.
- When opening a form, first open the page, then extract elements to understand the structure before interacting.
- If you need to fill a form, use `extract_elements` to find the field IDs, then `type_in_elements` or `click_elements`.
- You can access the user's resume for details if needed.
- To check for emails, use `get_recent_emails()`. It defaults to checking the primary inbox (first 5). You can also provide a query.
- To check unread emails specifically, use `get_unread_emails()`.
- Analyze email snippets to find companies and dates as requested.
- If a tool call fails, try to understand why (e.g., invalid JSON) and retry with the correct format.
- CRITICAL: Once you have successfully executed the tool(s) to fulfill the user's request (e.g. sending an email or scheduling an event), STOP. Do NOT call `get_recent_emails` or perform additional checking unless explicitly asked. Provide your final answer immediately.
"""

# Create the agent using LangGraph
agent = create_react_agent(llm, tools)

# ---- Run Loop ----
if __name__ == '__main__':
    print("Type 'exit' to quit")

    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        try:
            # Update system prompt with current time to assist with "today", "tomorrow" queries
            import datetime
            current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            dynamic_system_prompt = f"{system_prompt}\n\nCurrent Date and Time: {current_time_str}\nTimezone: Asia/Kolkata (IST)"

            # LangGraph agent is invoked directly
            messages = [
                ("system", dynamic_system_prompt),
                ("user", user_input)
            ]
            
            # Simple retry logic for rate limits
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    result = agent.invoke({"messages": messages})
                    # The result is a state dict, look for the last message
                    last_message = result["messages"][-1]
                    print("Agent:", last_message.content)
                    break # Success!
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        print(f"Rate limit hit. Retrying in 2 seconds... (Attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(2)
                    else:
                        raise e # Re-raise if not 429 or out of retries

        except Exception as e:
            print(f"Error: {e}")
