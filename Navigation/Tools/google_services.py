
from __future__ import print_function
import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime
import io
from googleapiclient.http import MediaIoBaseDownload
from pypdf import PdfReader
from gtts import gTTS

# Scopes need to change if you need more permissions
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents'
]
class GoogleServiceManager:
    def __init__(self, credentials_path='credentials.json', token_path='token.json'):
        self.creds = None
        self.credentials_path = credentials_path
        self.token_path = token_path
        self._authenticate()
        
        # Build Services
        self._calendar_service = build('calendar', 'v3', credentials=self.creds)
        self._drive_service = build('drive', 'v3', credentials=self.creds)
        self._gmail_service = build('gmail', 'v1', credentials=self.creds)
        self._sheets_service = build('sheets', 'v4', credentials=self.creds)
        self._docs_service = build('docs', 'v1', credentials=self.creds)

    def _authenticate(self):
        """Authenticates with Google OAuth 2.0 flow."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Could not find {self.credentials_path}. Please download it from Google Cloud Console.")
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                self.creds = flow.run_local_server(port=8080)
                
            # Save the credentials for the next run
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

    # --- Drive Functions ---

    def search_files(self, query):
        """Searches for files in Google Drive."""
        try:
            results = self._drive_service.files().list(
                q=query, pageSize=10, fields="nextPageToken, files(id, name)").execute()
            return results.get('files', [])
        except HttpError as error:
            print(f"An error occurred searching files: {error}")
            return []

    def get_resume_text(self, filename: str = "resume") -> str:
        """Finds a PDF file with 'resume' (or specified name) in the title and returns its text."""
        # Find the file first
        # We look for PDF files matching the name
        q = f"name contains '{filename}' and mimeType = 'application/pdf'"
        
        files = self.search_files(q)
        if not files:
            return f"No PDF file found with name containing '{filename}'."
        
        # Pick the first one for now or maybe the most recently modified?
        file_id = files[0]['id']
        file_name = files[0]['name']
        print(f"Found file: {file_name} ({file_id})")

        # Download content
        try:
            request = self._drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        except HttpError as error:
            return f"Error downloading file: {error}"
            
        fh.seek(0)
        
        # Parse PDF
        try:
            reader = PdfReader(fh)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    # --- Calendar Functions ---

    def list_events(self, max_results=10):
        """Shows basic usage of the Google Calendar API."""
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = self._calendar_service.events().list(calendarId='primary', timeMin=now,
                                                  maxResults=max_results, singleEvents=True,
                                                  orderBy='startTime').execute()
            events_result = events_result.get('items', [])
            return events_result
        except HttpError as error:
            print(f"An error occurred listing events: {error}")
            return []

    def schedule_event(self, summary: str, start_datetime_iso: str, duration_minutes: int = 60, description: str = "", timezone: str = "Asia/Kolkata") -> str:
        """
        Schedules an event on the primary calendar.
        start_datetime_iso should be in ISO format, e.g., '2023-10-27T10:00:00'.
        """
        try:
            # Check if headers (like checks for date/time formats) are correct in prompt
            
            # If start_datetime_iso has no timezone info, it is assumed to be in the given timezone
            # If it has timezone info (e.g. +05:30), fromisoformat handles it.
            
            start_dt = datetime.datetime.fromisoformat(start_datetime_iso)
            end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)
            
            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': timezone, 
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': timezone,
                },
            }

            event = self._calendar_service.events().insert(calendarId='primary', body=event).execute()
            return f"Event created: {event.get('htmlLink')}"
        except Exception as e:
            return f"Error scheduling event: {str(e)}"

    # --- Gmail Functions ---

    def search_emails(self, query: str, max_results: int = 5):
        """
        Searches for emails matching the query.
        Returns a list of email dictionaries with 'id', 'snippet', 'subject', 'body', 'date'.
        """
        try:
            results = self._gmail_service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
            messages = results.get('messages', [])
            
            email_data = []
            for msg in messages:
                msg_id = msg['id']
                # Use format='metadata' for faster retrieval (headers + snippet, no body)
                full_msg = self._gmail_service.users().messages().get(userId='me', id=msg_id, format='metadata').execute()
                
                payload = full_msg.get('payload', {})
                headers = payload.get('headers', [])
                snippet = full_msg.get('snippet', '')
                
                subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
                date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown Date')
                
                # Body is not available in metadata format, use snippet as a fallback
                body = snippet 
                
                email_data.append({
                    'id': msg_id,
                    'subject': subject,
                    'sender': sender,
                    'date': date,
                    'snippet': snippet,
                    'body': body
                })
                
            return email_data

        except HttpError as error:
            print(f"An error occurred searching emails: {error}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred searching emails: {e}")
            return []

    def send_or_draft_email(self, to: str, subject: str, message_text: str, is_draft: bool = False) -> str:
        """
        Sends an email or saves it as a draft.
        """
        try:
            from email.message import EmailMessage
            message = EmailMessage()
            message.set_content(message_text)
            message['To'] = to
            message['Subject'] = subject

            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            body = {'raw': encoded_message}

            if is_draft:
                draft = {'message': body}
                draft = self._gmail_service.users().drafts().create(userId='me', body=draft).execute()
                print(f"Draft id: {draft['id']} created")
                return f"Draft created successfully with ID: {draft['id']}"
            else:
                sent_message = self._gmail_service.users().messages().send(userId='me', body=body).execute()
                print(f"Message Id: {sent_message['id']} sent")
                return f"Email sent successfully with ID: {sent_message['id']}"

        except HttpError as error:
            print(f"An error occurred sending/drafting email: {error}")
            return f"An error occurred: {error}"
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return f"An unexpected error occurred: {e}"

    def schedule_email(self, to: str, subject: str, message_text: str, send_at_iso: str) -> str:
        """
        Schedules an email to be sent at a specific time using a background thread.
        send_at_iso should be in ISO format (e.g., '2023-10-27T10:00:00').
        """
        try:
            import datetime
            import threading
            
            target_time = datetime.datetime.fromisoformat(send_at_iso)
            if target_time.tzinfo is not None:
                # Target time is timezone-aware
                now = datetime.datetime.now(datetime.timezone.utc).astimezone(target_time.tzinfo)
            else:
                # Target time is timezone-naive
                now = datetime.datetime.now()
            
            delay = (target_time - now).total_seconds()
            
            if delay <= 0:
                print("Scheduled time is in the past, sending immediately.")
                return self.send_or_draft_email(to, subject, message_text, is_draft=False)

            def delayed_send():
                print(f"Background thread sending scheduled email to {to} now.")
                self.send_or_draft_email(to, subject, message_text, is_draft=False)

            timer = threading.Timer(delay, delayed_send)
            timer.daemon = True # Allows program to exit if email is still pending
            timer.start()
            
            delay_minutes = delay / 60
            return f"Email successfully scheduled to {to}. It will go out in approx {delay_minutes:.1f} minutes."
        except Exception as e:
            print(f"Error scheduling email: {e}")
            return f"Error scheduling email: {e}"

    # --- Google Sheets Functions ---

    def get_sheet_data(self, spreadsheet_id: str, range_name: str):
        """
        Reads data from a Google Sheet.
        range_name example: 'Sheet1!A1:D10'
        """
        try:
            result = self._sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()
            values = result.get('values', [])
            
            if not values:
                return "No data found in the specified range."
                
            # Format as simple text string for LLM easily reading rows
            formatted_data = "\\n".join([" | ".join(map(str, row)) for row in values])
            return formatted_data
        except HttpError as error:
            return f"An error occurred getting sheet data: {error}"

    def update_sheet_data(self, spreadsheet_id: str, range_name: str, values: list):
        """
        Writes data to a Google Sheet.
        values should be a list of lists, e.g., [['Name', 'Age'], ['Alice', 30]]
        """
        try:
            body = {'values': values}
            result = self._sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, range=range_name,
                valueInputOption='USER_ENTERED', body=body).execute()
            return f"{result.get('updatedCells')} cells updated."
        except HttpError as error:
            return f"An error occurred updating sheet data: {error}"

    # --- Text to Speech (gTTS) ---

    def text_to_speech(self, text: str, output_filename: str = "output.mp3") -> str:
        """
        Converts text to speech using Google Translate TTS and saves as an audio file.
        """
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_filename)
            return f"Audio saved successfully to {os.path.abspath(output_filename)}"
        except Exception as e:
            return f"Error converting text to speech: {str(e)}"

    # --- Google Docs Functions ---

    def create_google_doc(self, title: str, content: str = "") -> str:
        """Creates a new Google Doc with optional content."""
        try:
            doc = self._docs_service.documents().create(body={"title": title}).execute()
            doc_id = doc["documentId"]

            if content:
                requests = [{
                    "insertText": {
                        "location": {"index": 1},
                        "text": content
                    }
                }]
                self._docs_service.documents().batchUpdate(
                    documentId=doc_id,
                    body={"requests": requests}
                ).execute()

            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            return f"Google Doc created!\nTitle: {title}\nID: {doc_id}\nURL: {doc_url}"
        except Exception as e:
            return f"Failed to create Google Doc: {str(e)}"

    def edit_google_doc(self, doc_id: str, action: str, content: str, index: int = 1) -> str:
        """
        Edits an existing Google Doc.
        action: 'append' | 'insert' | 'replace_all'
        - append: adds content at the end of the doc
        - insert: inserts content at the given index
        - replace_all: replaces all text with new content
        """
        try:
            if action == "replace_all":
                # First get doc to find end index
                doc = self._docs_service.documents().get(documentId=doc_id).execute()
                end_index = doc['body']['content'][-1]['endIndex'] - 1
                requests = [
                    {
                        "deleteContentRange": {
                            "range": {"startIndex": 1, "endIndex": end_index}
                        }
                    },
                    {
                        "insertText": {
                            "location": {"index": 1},
                            "text": content
                        }
                    }
                ]
            elif action == "append":
                doc = self._docs_service.documents().get(documentId=doc_id).execute()
                end_index = doc['body']['content'][-1]['endIndex'] - 1
                requests = [{
                    "insertText": {
                        "location": {"index": end_index},
                        "text": content
                    }
                }]
            elif action == "insert":
                requests = [{
                    "insertText": {
                        "location": {"index": index},
                        "text": content
                    }
                }]
            else:
                return f"Unknown action '{action}'. Use 'append', 'insert', or 'replace_all'."

            self._docs_service.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": requests}
            ).execute()

            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            return f"Google Doc updated successfully!\nURL: {doc_url}"
        except Exception as e:
            return f"Failed to edit Google Doc: {str(e)}"
if __name__ == '__main__':
    # Initial setup run
    agent = GoogleServiceManager()
    print("Authenticated successfully.")
