# backend/gmail_connect.py

import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


# ── Connects to Gmail (caches credentials in token.json) ─────
def get_gmail_service():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    token_path = os.path.join(current_dir, 'token.json')
    credentials_path = os.path.join(current_dir, 'credentials.json')
    
    creds = None
    # Load cached token if it exists
    if os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception as e:
            print(f"⚠️ Failed to load token.json, re-authenticating: {e}")

    # If there are no valid credentials, run the flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"⚠️ Failed to refresh token, running full login: {e}")
                flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Required file 'credentials.json' not found in {current_dir}. "
                    "Please download OAuth client ID secrets from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Cache credentials for next execution
        try:
            with open(token_path, 'w') as token_file:
                token_file.write(creds.to_json())
            print("✅ OAuth token cached successfully in backend/token.json")
        except Exception as e:
            print(f"⚠️ Failed to save token.json: {e}")
            
    return build('gmail', 'v1', credentials=creds)


# ── NEW: fetches recent emails and returns them as a list ────
def fetch_recent_emails(max_results=20):
    service = get_gmail_service()

    # Step 1: get list of recent email IDs
    results = service.users().messages().list(
        userId='me',
        maxResults=max_results,
        labelIds=['INBOX']
    ).execute()

    messages = results.get('messages', [])
    emails = []

    # Step 2: for each ID, fetch the actual email content
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        # Extract subject and sender from headers
        headers = msg_data['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender  = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date    = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

        # Extract body text
        body = extract_body(msg_data['payload'])

        emails.append({
            'id':      msg['id'],
            'subject': subject,
            'from':    sender,
            'date':    date,
            'body':    body
        })

    return emails


# ── Helper: recursively extracts text body from email payload ──
def extract_body(payload):
    body = ""

    # If there are nested parts, traverse recursively
    if 'parts' in payload:
        for part in payload['parts']:
            part_body = extract_body(part)
            if part_body:
                # Prioritize plain text body over HTML
                if part.get('mimeType') == 'text/plain':
                    return part_body
                elif not body:
                    body = part_body
    else:
        # Base case: leaf part
        mime_type = payload.get('mimeType', '')
        if mime_type in ['text/plain', 'text/html']:
            data = payload.get('body', {}).get('data', '')
            if data:
                try:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                except Exception as e:
                    print(f"⚠️ Failed to decode email body part: {e}")

    return body[:2000]  # limit to first 2000 chars to save memory/context