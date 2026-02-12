
# Google Authentication Setup Guide for AgentX

This guide walks you through setting up the necessary Google Cloud credentials to allow AgentX to access your Gmail, Google Drive, and Google Calendar.

## Prerequisites

- A Google Account (Gmail).
- Python installed on your system.

## Step 1: Create a Google Cloud Project

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Click on the project dropdown at the top of the page.
3.  Click **"New Project"**.
4.  Give your project a name (e.g., "AgentX") and click **"Create"**.
5.  Select your new project from the dropdown.

## Step 2: Enable Google APIs

You need to enable the specific APIs that AgentX uses.

1.  In the Cloud Console, go to **"APIs & Services" > "Library"**.
2.  Search for and **Enable** the following APIs one by one:
    *   **Gmail API**
    *   **Google Drive API**
    *   **Google Calendar API**

## Step 3: Configure OAuth Consent Screen

1.  Go to **"APIs & Services" > "OAuth consent screen"**.
2.  Select **"External"** (unless you are in a Google Workspace organization and want it internal) and click **"Create"**.
3.  **App Information**:
    *   App name: "AgentX"
    *   User support email: Select your email.
    *   Developer contact information: Enter your email.
4.  Click **"Save and Continue"**.
5.  **Scopes**: You can skip adding scopes manually here (our code handles it) or add `.../auth/gmail.readonly`, `.../auth/calendar`, `.../auth/drive.readonly`. Click **"Save and Continue"**.
6.  **Test Users**:
    *   **IMPORTANT**: Since your app is "External" and in "Testing" mode, you **MUST** add your own email address here.
    *   Click **"Add Users"** and enter your Gmail address.
    *   Click **"Save and Continue"**.

## Step 4: Create Credentials (`credentials.json`)

1.  Go to **"APIs & Services" > "Credentials"**.
2.  Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**.
3.  **Application type**: Select **"Desktop app"**.
4.  **Name**: "AgentX Desktop" (or similar).
5.  Click **"Create"**.
6.  A popup will appear. Click **"DOWNLOAD JSON"**.
7.  **Rename** the downloaded file to `credentials.json`.
8.  **Move** `credentials.json` into the root folder of your `AgentX` project (the same folder as `app.py`).

## Step 5: First-Time Authentication

1.  Open your terminal in the `AgentX` project folder.
2.  Run the application:
    ```bash
    python app.py
    ```
3.  A browser window will automatically open asking you to sign in with your Google account.
4.  **"Google hasn't verified this app" Warning**:
    *   This is normal because you created a personal test app.
    *   Click **"Advanced"**.
    *   Click **"Go to AgentX (unsafe)"** (or whatever you named your app).
5.  Check the boxes to grant permissions for Gmail, Drive, and Calendar.
6.  Click **"Continue"**.
7.  The terminal should say `Google Services initialized successfully.`.

## Troubleshooting

*   **Error 403: Access Not Configured**: This means you forgot **Step 2**. Go back and ensure Gmail, Drive, and Calendar APIs are all enabled.
*   **Error 403: Access Denied**: This usually means you forgot to add your email as a **Test User** in **Step 3**.
*   **Token Issues**: If you change permissions (scopes), delete the `token.json` file in your project folder and run `python app.py` again to re-authenticate.
