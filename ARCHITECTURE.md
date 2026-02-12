
# Architecture and Cost Analysis

## 1. Does this incur a Cloud Bill?

### **Google Cloud Platform (GCP)**
For a personal project like this, **it is highly unlikely you will pay anything.** Google provides a very generous **Free Tier** for its APIs.

*   **Gmail API**: You get ~1,000,000,000 "quota units" per day for free. Listing messages costs 1 unit. Getting a message costs 5 units. You would need to read millions of emails a day to pay.
*   **Google Drive API**: similarly generous free quotas.
*   **Google Calendar API**: similarly generous free quotas.

**Verdict**: **Effectively Free** for personal use. You would only pay if you scaled this to thousands of users or millions of requests.

### **Groq API (The LLM)**
*   **Currently**: Groq offers a free tier (which you are likely using).
*   **The Error `429 Too Many Requests`**: This just means you hit the "Rate Limit" (requests per minute) of the free tier. It doesn't mean you are being charged. It just means "slow down".
*   **Future**: If you switch to a paid API key (like OpenAI or a paid Groq plan), you would pay per "token" (word/part of word) processed.

## 2. How this Internally Works

The system follows a **ReAct (Reasoning and Action)** or **Tool-Use** architecture.

### **The Flow:**
1.  **Input**: You type: *"Search recent emails for interviews"*.
2.  **The Brain (LLM - Groq/Llama 3)**:
    *   The `app.py` script sends your text + a list of available tools (definitions of `get_recent_emails`, `schedule_interview`, etc.) to the LLM.
    *   The LLM analyzes your request and decides: *"I need to call the `get_recent_emails` tool."*
    *   It returns a structured response: `Call: get_recent_emails(query='interview')`.
3.  **The Body (Local Execution)**:
    *   `LangGraph` (the framework) sees the LLM wants to call a tool.
    *   It executes the Python function `get_recent_emails` in `app.py`.
4.  **The Hands (Google APIs)**:
    *   `app.py` calls `google_services.py`.
    *   `google_services.py` uses your `token.json` (credentials) to securely talk to Google's servers via the internet.
    *   Google returns the raw email data (JSON).
5.  **Synthesis**:
    *   The raw email data is sent *back* to the LLM.
    *   The LLM reads the emails and summarizes them for you: *"I found 3 emails..."*

### **Diagram:**
```
[User] -> [app.py (LangGraph)] -> [LLM (Groq)]
                 ^                       |
                 | (Decides to use Tool) v
          [Google API] <------- [Tool Execution]
```

### **Why `token.json`?**
This file stores your "Access Token" and "Refresh Token".
*   **Access Token**: Like a temporary keycard. Expires in 1 hour.
*   **Refresh Token**: Used to get a new Access Token automatically without you logging in again.
*   **OAuth 2.0**: The protocol used to grant `AgentX` permission to access your data without giving it your password.
