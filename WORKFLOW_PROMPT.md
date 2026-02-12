
# Workflow Prompt: Job Application Assistant

Use the following prompt to demonstrate the integration of **Gmail**, **Google Drive**, and **Google Calendar**.

## The Prompt

Copy and paste this into the agent's terminal:

> **"Check my recent emails for any messages with the subject 'Interview'. If you find an email, extract the date and time. Then, read my 'resume' from Google Drive to summarize my key skills. Finally, schedule the interview on my Google Calendar using the date/time from the email and include my key skills in the event description."**

## What this triggers:

1.  **Gmail Search**: The agent uses `get_recent_emails(query="subject:Interview")` to find relevant emails.
2.  **Information Extraction**: The agent reads the email snippet to find the proposed interview time (e.g., "Friday at 2 PM").
3.  **Drive Access**: The agent uses `get_resume(filename="resume")` to read your PDF resume and extracts your skills (e.g., "Python, AI, React").
4.  **Calendar Scheduling**: The agent uses `schedule_interview(...)` to create a calendar event:
    *   **Summary**: "Interview" (or similar)
    *   **Time**: The derived date and time converted to ISO format.
    *   **Description**: "Skills discussed: Python, AI, React..."

## Prerequisites

1.  **Email**: Send yourself an email with the subject "Interview" and body "Can we schedule an interview for next Friday at 10 AM?".
2.  **Resume**: Ensure a file named `resume.pdf` exists in your Google Drive.
