# filepath: c:\Users\isha vijay lanjekar\email spam project\test_gmail.py
import os
import sys

print("=" * 60)
print("📧 GMAIL INTEGRATION TEST")
print("=" * 60)

errors = []

# --- Step 1: Check required files ---
print("\n🔍 Step 1: Checking required files...")
print("-" * 40)

files_to_check = {
    'credentials.json': False,
    'spam_model.pkl': False,
    'vectorizer.pkl': False,
    'gmail_integration.py': False,
}

for file in files_to_check:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"  ✅ {file} ({size} bytes)")
        files_to_check[file] = True
    else:
        print(f"  ❌ {file} - MISSING!")
        errors.append(f"{file} is missing")

# --- Step 2: Check credentials.json format ---
print("\n🔍 Step 2: Validating credentials.json...")
print("-" * 40)

if files_to_check['credentials.json']:
    try:
        import json
        with open('credentials.json', 'r') as f:
            creds = json.load(f)

        if 'installed' in creds:
            print(f"  ✅ Credential type: Desktop App (correct!)")
            print(f"  ✅ Client ID: {creds['installed'].get('client_id', 'N/A')[:40]}...")
            print(f"  ✅ Auth URI: {creds['installed'].get('auth_uri', 'N/A')}")
            print(f"  ✅ Token URI: {creds['installed'].get('token_uri', 'N/A')}")

            # Check required fields
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            for field in required_fields:
                if field not in creds['installed']:
                    print(f"  ❌ Missing field: {field}")
                    errors.append(f"credentials.json missing field: {field}")

        elif 'web' in creds:
            print(f"  ⚠️  Credential type: Web App")
            print(f"     ❌ You need 'Desktop App' credentials!")
            print(f"     ↳ Go to Google Cloud Console → Credentials")
            print(f"     ↳ Create OAuth Client ID → Application type: Desktop App")
            errors.append("credentials.json is Web App type, need Desktop App")
        else:
            print(f"  ❌ Unknown format! Keys: {list(creds.keys())}")
            errors.append("credentials.json has invalid format")

    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON! Re-download from Google Cloud Console")
        errors.append("credentials.json is not valid JSON")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        errors.append(f"credentials.json error: {e}")
else:
    print(f"  ⏭️  Skipped (file missing)")

# --- Step 3: Check required packages ---
print("\n🔍 Step 3: Checking required packages...")
print("-" * 40)

packages = {
    'google.auth': 'google-auth',
    'google.auth.transport.requests': 'google-auth',
    'google_auth_oauthlib.flow': 'google-auth-oauthlib',
    'googleapiclient.discovery': 'google-api-python-client',
    'google.auth.exceptions': 'google-auth',
    'joblib': 'joblib',
    'sklearn': 'scikit-learn',
    'pandas': 'pandas',
}

missing_packages = []
for module, pip_name in packages.items():
    try:
        __import__(module)
        print(f"  ✅ {pip_name}")
    except ImportError:
        print(f"  ❌ {pip_name} - NOT INSTALLED")
        missing_packages.append(pip_name)
        errors.append(f"Package missing: {pip_name}")

if missing_packages:
    unique_packages = list(set(missing_packages))
    print(f"\n  💡 Install missing packages:")
    print(f"     pip install {' '.join(unique_packages)}")

# --- Step 4: Validate model ---
print("\n🔍 Step 4: Validating spam model...")
print("-" * 40)

if files_to_check['spam_model.pkl'] and files_to_check['vectorizer.pkl']:
    try:
        import joblib
        model = joblib.load('spam_model.pkl')
        vectorizer = joblib.load('vectorizer.pkl')

        print(f"  ✅ Model type: {type(model).__name__}")
        print(f"  ✅ Vectorizer type: {type(vectorizer).__name__}")
        print(f"  ✅ Vocabulary size: {len(vectorizer.vocabulary_)}")

        # Test predictions
        test_messages = [
            ("Congratulations! You won $1000 free gift card click now!", "SPAM"),
            ("Hey, can we meet for lunch tomorrow?", "NOT SPAM"),
            ("URGENT: Verify your bank account immediately", "SPAM"),
            ("Please find attached the meeting notes from today", "NOT SPAM"),
        ]

        print(f"\n  🧪 Test Predictions:")
        for msg, expected in test_messages:
            vec = vectorizer.transform([msg])
            pred = model.predict(vec)[0]
            label = "SPAM" if pred == 1 else "NOT SPAM"
            match = "✅" if label == expected else "⚠️"
            print(f"     {match} [{label:>8}] {msg[:50]}...")

    except Exception as e:
        print(f"  ❌ Error loading model: {e}")
        errors.append(f"Model error: {e}")
else:
    print(f"  ⏭️  Skipped (files missing)")
    print(f"     ↳ Run: python save_model.py")

# --- Step 5: Check token.pickle (previous auth) ---
print("\n🔍 Step 5: Checking Gmail authentication...")
print("-" * 40)

if os.path.exists('token.pickle'):
    try:
        import pickle
        from google.auth.transport.requests import Request

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        if creds and creds.valid:
            print(f"  ✅ token.pickle exists and is VALID")
            print(f"  ✅ No login required (already authenticated)")
        elif creds and creds.expired and creds.refresh_token:
            print(f"  ⚠️  Token expired, attempting refresh...")
            try:
                creds.refresh(Request())
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
                print(f"  ✅ Token refreshed successfully!")
            except Exception as e:
                print(f"  ❌ Token refresh failed: {e}")
                print(f"     ↳ Delete token.pickle and re-authenticate")
                errors.append("Token refresh failed")
        else:
            print(f"  ❌ Token is invalid")
            print(f"     ↳ Delete token.pickle and re-authenticate")
    except Exception as e:
        print(f"  ❌ Error reading token: {e}")
        print(f"     ↳ Delete token.pickle and re-authenticate")
else:
    print(f"  ⚪ token.pickle not found (first time setup)")
    print(f"     ↳ Browser will open for login when you run gmail_integration.py")

# --- Step 6: Test Gmail connection ---
print("\n🔍 Step 6: Testing Gmail API connection...")
print("-" * 40)

if os.path.exists('token.pickle') and not missing_packages:
    try:
        import pickle
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build

        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

        if creds and creds.valid:
            service = build('gmail', 'v1', credentials=creds)

            # Get profile
            profile = service.users().getProfile(userId='me').execute()
            email_address = profile.get('emailAddress', 'Unknown')
            total_messages = profile.get('messagesTotal', 0)

            print(f"  ✅ Connected to Gmail successfully!")
            print(f"  📧 Email: {email_address}")
            print(f"  📊 Total messages: {total_messages}")

            # Fetch 1 email as test
            results = service.users().messages().list(userId='me', maxResults=1, labelIds=['INBOX']).execute()
            messages = results.get('messages', [])

            if messages:
                print(f"  ✅ Can fetch emails from inbox")

                # Get email details
                import base64
                msg = service.users().messages().get(userId='me', id=messages[0]['id'], format='full').execute()
                headers = msg['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

                print(f"\n  📩 Latest email:")
                print(f"     From: {sender[:50]}")
                print(f"     Subject: {subject[:50]}")

                # Classify it
                if files_to_check['spam_model.pkl'] and files_to_check['vectorizer.pkl']:
                    body = ''
                    if 'parts' in msg['payload']:
                        for part in msg['payload']['parts']:
                            if part['mimeType'] == 'text/plain':
                                body = base64.urlsafe_b64decode(
                                    part['body'].get('data', '')).decode('utf-8', errors='ignore')
                                break
                    elif 'body' in msg['payload'] and 'data' in msg['payload']['body']:
                        body = base64.urlsafe_b64decode(
                            msg['payload']['body']['data']).decode('utf-8', errors='ignore')

                    text = subject + ' ' + body
                    text_vec = vectorizer.transform([text])
                    pred = model.predict(text_vec)[0]
                    label = "🚨 SPAM" if pred == 1 else "✅ NOT SPAM"
                    print(f"     Prediction: {label}")
            else:
                print(f"  ⚠️  Inbox is empty")

        else:
            print(f"  ⏭️  Token not valid, need to authenticate first")
            print(f"     ↳ Run: python gmail_integration.py")

    except Exception as e:
        print(f"  ❌ Gmail connection failed: {e}")
        errors.append(f"Gmail connection error: {e}")
else:
    if missing_packages:
        print(f"  ⏭️  Skipped (missing packages)")
    else:
        print(f"  ⏭️  Skipped (not authenticated yet)")
        print(f"     ↳ Run: python gmail_integration.py (browser will open)")

# --- Step 7: Check gmail_integration.py content ---
print("\n🔍 Step 7: Validating gmail_integration.py...")
print("-" * 40)

if files_to_check['gmail_integration.py']:
    try:
        with open('gmail_integration.py', 'r') as f:
            content = f.read()

        required_items = {
            'authenticate_gmail': 'Authentication function',
            'get_emails': 'Email fetching function',
            'classify_emails': 'Email classification function',
            'credentials.json': 'Credentials file reference',
            'spam_model.pkl': 'Model file reference',
            'vectorizer.pkl': 'Vectorizer file reference',
            'token.pickle': 'Token storage reference',
        }

        for item, desc in required_items.items():
            if item in content:
                print(f"  ✅ {desc} ({item})")
            else:
                print(f"  ⚠️  {desc} ({item}) not found in script")

    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
else:
    print(f"  ⏭️  Skipped (file missing)")

# --- Final Summary ---
print(f"\n{'=' * 60}")
if not errors:
    print("🎉 ALL CHECKS PASSED! Gmail integration is ready!")
    print(f"\n📌 Run your project:")
    print(f"   Terminal:  python gmail_integration.py")
    print(f"   Web UI:    streamlit run app.py")
else:
    print(f"⚠️  {len(errors)} ISSUE(S) FOUND:\n")
    for i, err in enumerate(errors, 1):
        print(f"   {i}. {err}")

    print(f"\n📌 How to fix:")
    if any('missing' in e.lower() and 'package' in e.lower() for e in errors):
        pkgs = list(set(missing_packages))
        print(f"   1. Install packages: pip install {' '.join(pkgs)}")
    if any('spam_model' in e or 'vectorizer' in e for e in errors):
        print(f"   2. Train model: python save_model.py")
    if any('credentials' in e.lower() for e in errors):
        print(f"   3. Fix credentials.json from Google Cloud Console")
    if any('token' in e.lower() for e in errors):
        print(f"   4. Delete token.pickle and re-run: python gmail_integration.py")

print(f"{'=' * 60}")