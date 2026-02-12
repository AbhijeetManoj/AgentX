
# AgentX Demo Guide

To demonstrate the capabilities of AgentX with Google Services, ensure you have enabled the **Gmail API**, **Google Drive API**, and **Google Calendar API** in your Google Cloud Console project (`952277707742`).

Run the agent:
```bash
python app.py
```

## 1. Google Drive Demo (Resume Reading)
**Goal**: The agent searches for a PDF named "resume" in your Drive, reads it, and answers questions.

**Prerequisite**: Upload a PDF file named `resume.pdf` (or similar, e.g., `My_Resume.pdf`) to your Google Drive.

**Prompt**:
> "Read my resume and tell me my phone number or skills."
> "What is the experience listed in my resume?"

**Under the hood**: using `get_resume(filename="resume")`.

## 2. Google Calendar Demo (Scheduling)
**Goal**: The agent schedules an event on your primary Google Calendar.

**Prompt**:
> "Schedule a meeting with potential candidate on Friday at 2 PM for 1 hour."

**Under the hood**: using `schedule_interview(summary="Meeting with potential candidate", start_time="202X-XX-XXT14:00:00", duration=60)`.

## 3. Gmail Demo (Email Analysis)
**Goal**: The agent checks emails for keywords or unread status.

**Prompt**:
> "Check my recent emails for any interview updates."
> "Do I have any unread emails?"

**Under the hood**: using `get_recent_emails(query="interview")` or `get_unread_emails()`.

## 4. Full Workflow (The "Magic")
**Goal**: Combine tools. Find an email about an interview and schedule it.

**Prompt**:
> "Check my emails for an interview invite from Google, and if you find one, schedule it on my calendar."

**Logic**:
1. Agent calls `get_recent_emails(query="Google interview")`.
2. Agent reads the email body to find the date/time (e.g., "Oct 25th at 10 AM").
3. Agent calls `schedule_interview(summary="Google Interview", start_time="...", duration=45)`.
