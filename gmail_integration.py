import os
import base64
import pickle
import joblib
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service


def get_emails(service, max_results=10, page_token=None):
    kwargs = {
        'userId': 'me',
        'maxResults': max_results,
        'labelIds': ['INBOX'],
    }
    if page_token:
        kwargs['pageToken'] = page_token
    results = service.users().messages().list(**kwargs).execute()
    messages = results.get('messages', [])
    next_page_token = results.get('nextPageToken', None)

    emails = []
    for msg in messages:
        message = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()

        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

        body = ''
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(
                        part['body'].get('data', '')
                    ).decode('utf-8', errors='ignore')
                    break
        elif 'body' in message['payload'] and 'data' in message['payload']['body']:
            body = base64.urlsafe_b64decode(
                message['payload']['body']['data']
            ).decode('utf-8', errors='ignore')

        emails.append({
            'id': msg['id'],
            'subject': subject,
            'sender': sender,
            'body': body,
            'snippet': message.get('snippet', '')
        })

    return emails, next_page_token


def classify_emails(emails):
    model = joblib.load('spam_model.pkl')
    vectorizer = joblib.load('vectorizer.pkl')

    for email in emails:
        text = email['subject'] + ' ' + email['body']
        text_vectorized = vectorizer.transform([text])
        prediction = model.predict(text_vectorized)[0]
        email['spam_prediction'] = 'SPAM' if prediction == 1 else 'NOT SPAM'

    return emails


if __name__ == '__main__':
    print("=" * 60)
    print("       Gmail Spam Detector")
    print("=" * 60)

    print("\n[1/3] Authenticating with Gmail...")
    service = authenticate_gmail()
    print("       Authentication successful!")

    print("\n[2/3] Fetching emails...")
    emails = get_emails(service, max_results=10)
    print(f"       Fetched {len(emails)} emails!")

    print("\n[3/3] Classifying emails...")
    classified_emails = classify_emails(emails)

    print(f"\n{'=' * 60}")
    for i, email in enumerate(classified_emails, 1):
        status = "SPAM" if email['spam_prediction'] == 'SPAM' else "NOT SPAM"
        icon = "[!]" if status == "SPAM" else "[OK]"
        print(f"\n  Email {i}: {icon} {status}")
        print(f"  From:       {email['sender']}")
        print(f"  Subject:    {email['subject']}")
        print(f"  Preview:    {email['snippet'][:100]}...")
        print(f"  {'-' * 56}")

    spam_count = sum(1 for e in classified_emails if e['spam_prediction'] == 'SPAM')
    ham_count = len(classified_emails) - spam_count

    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"  Total Emails:  {len(classified_emails)}")
    print(f"  Spam:          {spam_count}")
    print(f"  Not Spam:      {ham_count}")
    print(f"{'=' * 60}")