from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from email.mime.text import MIMEText
import base64
from app.config import Settings, GMAIL_SCOPE

settings = Settings()


def get_credentials():
    """Get Google OAuth credentials for Gmail."""
    creds = Credentials(
        token=settings.google_access_token,
        refresh_token=settings.google_refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=[GMAIL_SCOPE]
    )
    # Handle token refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def get_unread_emails(max_results=10):
    """Fetch unread emails from Gmail."""
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    query = "is:unread newer_than:30d"
    results = service.users().messages().list(
        userId='me', q=query, maxResults=max_results
    ).execute()

    messages = results.get('messages', [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}

        # Extract body (text/plain)
        body = get_body(msg_data['payload'])

        emails.append({
            'id': msg['id'],
            'subject': headers.get('Subject', ''),
            'from': headers.get('From', ''),
            'date': headers.get('Date', ''),
            'snippet': msg_data.get('snippet', ''),
            'body': body[:500]  # Limit for summary
        })

    return emails


def get_body(payload):
    """Extract plain text body from email payload."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body']['data']
                return base64.urlsafe_b64decode(data).decode('utf-8')
    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        return base64.urlsafe_b64decode(data).decode('utf-8')
    return ""
