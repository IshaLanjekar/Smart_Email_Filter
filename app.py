import streamlit as st
import streamlit.components.v1 as components
import pickle
import re
import os
import json
import base64
import pandas as pd
import nltk
from datetime import datetime, timedelta
from nltk.corpus import stopwords
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

nltk.download('stopwords', quiet=True)

# ===================== PERSISTENCE FILES =====================
KEYWORDS_FILE = 'user_keywords.json'
REPORT_HISTORY_FILE = 'report_history.json'


def load_keywords():
    """Load user keywords from disk."""
    if os.path.exists(KEYWORDS_FILE):
        try:
            with open(KEYWORDS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_keywords(keywords):
    """Save user keywords to disk."""
    with open(KEYWORDS_FILE, 'w') as f:
        json.dump(keywords, f)


def load_report_history():
    """Load report history from disk."""
    if os.path.exists(REPORT_HISTORY_FILE):
        try:
            with open(REPORT_HISTORY_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_report_history(history):
    """Save report history to disk."""
    with open(REPORT_HISTORY_FILE, 'w') as f:
        json.dump(history, f)


def load_report_settings():
    """Load scheduled report settings from disk."""
    settings_file = 'report_settings.json'
    if os.path.exists(settings_file):
        try:
            with open(settings_file, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'frequency': 'Off', 'last_report': None}


def save_report_settings(settings):
    """Save scheduled report settings to disk."""
    with open('report_settings.json', 'w') as f:
        json.dump(settings, f)


def load_oauth_client_config():
    """Load Gmail OAuth client config from Streamlit secrets or local JSON."""
    # Try secrets path 1: [gmail].client_config (recommended)
    try:
        gmail_section = st.secrets.get('gmail', {})
        if gmail_section and hasattr(gmail_section, 'get'):
            raw_config = gmail_section.get('client_config')
            if raw_config:
                if isinstance(raw_config, str):
                    parsed = json.loads(raw_config)
                    return parsed
                elif hasattr(raw_config, 'get'):
                    return dict(raw_config)
    except Exception:
        pass

    # Try secrets path 2: top-level client_config (backup)
    try:
        raw_config = st.secrets.get('client_config')
        if raw_config:
            if isinstance(raw_config, str):
                return json.loads(raw_config)
            elif hasattr(raw_config, 'get'):
                return dict(raw_config)
    except Exception:
        pass

    if os.path.exists(CREDS_FILE):
        with open(CREDS_FILE, 'r') as f:
            return json.load(f)

    return None


def build_oauth_flow(client_config):
    """Create an OAuth flow from either installed or web client config."""
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)

    web_config = client_config.get('web', {})
    redirect_uris = web_config.get('redirect_uris', [])
    if redirect_uris:
        flow.redirect_uri = redirect_uris[0]

    return flow

# ===================== CONFIGURATION =====================
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TOKEN_FILE = 'token.pickle'
CREDS_FILE = 'credentials.json'
OAUTH_PORT = 8090  # Fixed port - won't conflict with Streamlit (8501)
AUTO_REFRESH_SECONDS = 30

# ===================== PAGE CONFIG =====================
st.set_page_config(
    page_title="Gmail Spam Detector",
    page_icon="G",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== CUSTOM CSS =====================
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #ffffff 0%, #f3f8ff 100%);
        border-right: 1px solid #cddcff;
    }
    [data-testid="stSidebar"] h2 {
        color: #1f3a8a;
        letter-spacing: 0.2px;
    }
    button[kind="primary"] {
        background: linear-gradient(90deg, #ff4d6d 0%, #e63946 100%) !important;
        border: none !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        box-shadow: 0 6px 16px rgba(230, 57, 70, 0.25);
    }
    .analyze-cta {
        background: linear-gradient(135deg, #fff4e6 0%, #ffe3c2 100%);
        border-left: 6px solid #ff7b00;
        padding: 14px 16px;
        border-radius: 10px;
        margin: 10px 0 12px 0;
    }
    .analyze-shell {
        background: linear-gradient(135deg, #fff6ea 0%, #ffe8cc 100%);
        border: 1px solid #ffd2a8;
        border-left: 6px solid #ff7b00;
        border-radius: 12px;
        padding: 14px 16px;
        margin: 8px 0 10px 0;
    }
    .analyze-chip {
        background: #eef4ff;
        border: 1px solid #d4e3ff;
        border-radius: 12px;
        padding: 10px 14px;
        min-height: 88px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .analyze-chip .n {
        font-size: 34px;
        font-weight: 700;
        color: #0d3f90;
        line-height: 1.05;
    }
    .analyze-chip .t {
        font-size: 13px;
        color: #31589f;
        margin-top: 4px;
    }
    .spam-card {
        background-color: #ffe0e0;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4444;
        margin: 10px 0;
    }
    .ham-card {
        background-color: #e0ffe0;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #44ff44;
        margin: 10px 0;
    }
    .alert-card {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 10px 0;
    }
    .info-card {
        background-color: #e0e7ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #4444ff;
        margin: 10px 0;
    }
    .big-number {
        font-size: 48px;
        font-weight: bold;
        text-align: center;
    }
    .center-text {
        text-align: center;
    }
    .report-notification {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        padding: 18px 20px;
        border-radius: 12px;
        margin: 12px 0;
        font-size: 16px;
        display: flex;
        align-items: center;
        animation: slideIn 0.5s ease-out;
        box-shadow: 0 4px 12px rgba(46,125,50,0.3);
    }
    .report-notification.daily {
        background: linear-gradient(135deg, #2196F3 0%, #1565C0 100%);
        box-shadow: 0 4px 12px rgba(21,101,192,0.3);
    }
    .report-notification.weekly {
        background: linear-gradient(135deg, #FF9800 0%, #E65100 100%);
        box-shadow: 0 4px 12px rgba(230,81,0,0.3);
    }
    .report-notification.monthly {
        background: linear-gradient(135deg, #9C27B0 0%, #6A1B9A 100%);
        box-shadow: 0 4px 12px rgba(106,27,154,0.3);
    }
    @keyframes slideIn {
        from { transform: translateY(-20px); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    .important-card {
        background-color: #fff0e0;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff8800;
        margin: 10px 0;
    }
    .keyword-tag {
        display: inline-block;
        background-color: #e0e7ff;
        color: #333;
        padding: 4px 12px;
        border-radius: 20px;
        margin: 3px;
        font-size: 14px;
    }
    .keyword-match {
        display: inline-block;
        background-color: #ff8800;
        color: white;
        padding: 2px 8px;
        border-radius: 10px;
        font-size: 12px;
        margin-left: 5px;
    }
    .report-card {
        background-color: #f0e6ff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #8844ff;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# MODEL LOADING (cached - loads only once)
# ============================================================
@st.cache_resource
def load_models():
    spam_model = pickle.load(open("spam_model.pkl", "rb"))
    vectorizer = pickle.load(open("vectorizer_spam.pkl", "rb"))
    category_model = pickle.load(open("category_model.pkl", "rb"))
    return spam_model, vectorizer, category_model


# ============================================================
# TEXT PREPROCESSING (must match train_model.py)
# ============================================================
_stop_words = set(stopwords.words('english'))


def clean_text(text):
    text = text.lower()
    text = re.sub(r'[^a-zA-Z]', ' ', text)
    words = text.split()
    words = [w for w in words if w not in _stop_words]
    return " ".join(words)


# ============================================================
# 3-STAGE EMAIL CLASSIFIER
# Stage 1: Spam / Not Spam  (ML model)
# Stage 2: Category          (ML model - Work/Promotional/Academic)
# Stage 3: Sub-category      (keyword rules for finer labels)
# ============================================================
def check_keyword_importance(email_data, user_keywords):
    """Check if email matches any user-defined keywords.
    Returns importance label and list of matched keywords."""
    if not user_keywords:
        return 'Not Important', []

    text = (email_data.get('subject', '') + ' ' + email_data.get('body', '') + ' ' + email_data.get('snippet', '')).lower()
    matched = [kw for kw in user_keywords if kw.lower() in text]

    if matched:
        return 'Important', matched
    return 'Not Important', []


def classify_email(spam_model, vectorizer, category_model, email_data, user_keywords=None):
    text = email_data.get('subject', '') + ' ' + email_data.get('body', '')
    cleaned = clean_text(text)
    vec = vectorizer.transform([cleaned])

    # Keyword importance check (runs for all emails)
    importance, matched_kw = check_keyword_importance(email_data, user_keywords or [])
    email_data['importance'] = importance
    email_data['matched_keywords'] = matched_kw

    # Stage 1: Spam detection
    prediction = spam_model.predict(vec)[0]
    confidence = spam_model.predict_proba(vec)[0]

    if prediction == 1:
        email_data['prediction'] = 'SPAM'
        email_data['confidence'] = confidence[1] * 100

        # Stage 3: Spam sub-categories (keyword rules)
        combined = text.lower()
        if any(w in combined for w in ['win', 'prize', 'lottery', 'gift card', 'congratulations', 'winner']):
            email_data['category'] = 'Lottery/Prize Scam'
        elif any(w in combined for w in ['bank', 'account', 'verify', 'password', 'login', 'security', 'suspended']):
            email_data['category'] = 'Phishing'
        elif any(w in combined for w in ['offer', 'discount', 'sale', 'buy', 'deal', 'limited time', 'free']):
            email_data['category'] = 'Promotional Spam'
        elif any(w in combined for w in ['investment', 'money', 'earn', 'income', 'profit', 'bitcoin', 'crypto']):
            email_data['category'] = 'Financial Scam'
        elif any(w in combined for w in ['pills', 'weight loss', 'pharmacy', 'medication']):
            email_data['category'] = 'Health Spam'
        else:
            email_data['category'] = 'General Spam'

        email_data['sub_category'] = email_data['category']

    else:
        email_data['prediction'] = 'NOT SPAM'
        email_data['confidence'] = confidence[0] * 100

        # Stage 2: ML-based category (Work / Promotional / Academic)
        try:
            cat = category_model.predict(vec)[0]
            cat_map = {'work': 'Work', 'promotional': 'Promotional', 'academic': 'Academic'}
            email_data['category'] = cat_map.get(cat, cat.title())
        except Exception:
            email_data['category'] = 'General'

        # Stage 3: Fine sub-category (keyword rules)
        combined = text.lower()
        if any(w in combined for w in ['meeting', 'schedule', 'calendar', 'appointment', 'agenda']):
            email_data['sub_category'] = 'Work/Meetings'
        elif any(w in combined for w in ['invoice', 'payment', 'receipt', 'order', 'shipping', 'delivery']):
            email_data['sub_category'] = 'Transactions'
        elif any(w in combined for w in ['newsletter', 'update', 'weekly', 'digest', 'subscribe']):
            email_data['sub_category'] = 'Newsletters'
        elif any(w in combined for w in ['friend', 'family', 'birthday', 'hi ', 'hello', 'hey']):
            email_data['sub_category'] = 'Personal'
        elif any(w in combined for w in ['github', 'code', 'deploy', 'server', 'error', 'bug']):
            email_data['sub_category'] = 'Technical'
        elif any(w in combined for w in ['noreply', 'notification', 'alert', 'confirm']):
            email_data['sub_category'] = 'Notifications'
        else:
            email_data['sub_category'] = email_data['category']

    return email_data


# ============================================================
# GMAIL AUTHENTICATION
# ============================================================
def get_gmail_service_silent():
    """Try to connect using saved token (no browser popup).
    Returns gmail service or None."""
    if not os.path.exists(TOKEN_FILE):
        return None

    try:
        with open(TOKEN_FILE, 'rb') as f:
            creds = pickle.load(f)
    except Exception:
        return None

    if creds and creds.valid:
        return build('gmail', 'v1', credentials=creds)

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            with open(TOKEN_FILE, 'wb') as f:
                pickle.dump(creds, f)
            return build('gmail', 'v1', credentials=creds)
        except Exception as e:
            # If the OAuth client was changed/deleted, the saved token becomes unusable.
            if os.path.exists(TOKEN_FILE):
                try:
                    os.remove(TOKEN_FILE)
                except Exception:
                    pass
            st.session_state['auth_error'] = str(e)
            return None

    return None


def handle_web_oauth_return(client_config):
    """Complete a web OAuth callback if Google has redirected back to the app."""
    code = st.query_params.get('code')
    state = st.query_params.get('state')
    pending_state = st.session_state.get('oauth_state')

    if not code or not state or not pending_state:
        return None

    if state != pending_state:
        st.error('OAuth state mismatch. Please click Connect Gmail again.')
        return None

    flow = build_oauth_flow(client_config)
    flow.fetch_token(code=code)
    creds = flow.credentials

    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)

    try:
        st.query_params.clear()
    except Exception:
        pass

    st.session_state.pop('oauth_state', None)
    st.session_state.pop('oauth_auth_url', None)

    return build('gmail', 'v1', credentials=creds)


def run_oauth_flow():
    """Full OAuth flow for local desktop login."""
    client_config = load_oauth_client_config()
    if not client_config:
        raise FileNotFoundError('No Gmail OAuth client config found in secrets or credentials.json.')

    flow = build_oauth_flow(client_config)

    if 'installed' in client_config:
        try:
            creds = flow.run_local_server(port=OAUTH_PORT)
        except OSError:
            # Fallback to any free local port if the preferred one is unavailable.
            creds = flow.run_local_server(port=0)
    else:
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true',
        )
        st.session_state['oauth_state'] = state
        st.session_state['oauth_auth_url'] = auth_url
        components.html(
            f"<script>window.location.href = {json.dumps(auth_url)};</script>",
            height=0,
        )
        st.stop()

    with open(TOKEN_FILE, 'wb') as f:
        pickle.dump(creds, f)
    return build('gmail', 'v1', credentials=creds)


# ============================================================
# GMAIL DATA FETCHING
# ============================================================
def get_user_profile(service):
    profile = service.users().getProfile(userId='me').execute()
    return {
        'email': profile.get('emailAddress', 'Unknown'),
        'total_messages': profile.get('messagesTotal', 0),
    }


def _parse_email_message(service, msg_id):
    """Parse a single Gmail message into a dict."""
    message = service.users().messages().get(
        userId='me', id=msg_id, format='full'
    ).execute()

    headers = message['payload']['headers']
    subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
    sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
    date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown')

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

    labels = message.get('labelIds', [])

    return {
        'id': msg_id,
        'subject': subject,
        'sender': sender,
        'date': date,
        'body': body,
        'snippet': message.get('snippet', ''),
        'is_unread': 'UNREAD' in labels,
    }


def fetch_emails_page(service, max_results=50, page_token=None):
    """Fetch one inbox page and return (emails, next_page_token)."""
    params = {
        'userId': 'me',
        'maxResults': max_results,
        'labelIds': ['INBOX'],
    }
    if page_token:
        params['pageToken'] = page_token

    results = service.users().messages().list(**params).execute()
    messages = results.get('messages', [])
    next_page_token = results.get('nextPageToken')

    emails = []
    for msg in messages:
        try:
            emails.append(_parse_email_message(service, msg['id']))
        except Exception:
            continue
    return emails, next_page_token


def fetch_new_emails(service, known_ids, max_results=20):
    """Fetch only emails whose IDs are NOT in known_ids."""
    results = service.users().messages().list(
        userId='me', maxResults=max_results, labelIds=['INBOX']
    ).execute()
    messages = results.get('messages', [])

    new_emails = []
    for msg in messages:
        if msg['id'] in known_ids:
            continue
        try:
            new_emails.append(_parse_email_message(service, msg['id']))
        except Exception:
            continue
    return new_emails


# ============================================================
# SESSION STATE DEFAULTS
# ============================================================
_defaults = {
    'gmail_connected': False,
    'service': None,
    'profile': {},
    'classified_emails': [],
    'new_alerts': [],
    'last_check': None,
    'auto_refresh': True,
    'emails_loaded': False,
    'ready_to_fetch': False,
    'inbox_next_page_token': None,
    'analyzed_count': 0,
    'user_keywords': load_keywords(),
    'report_settings': load_report_settings(),
    'report_history': load_report_history(),
    'report_notifications': [],
}
for _key, _val in _defaults.items():
    if _key not in st.session_state:
        st.session_state[_key] = _val


def disconnect_gmail_session():
    """Clear auth/session state and disconnect current Gmail account."""
    st.session_state.gmail_connected = False
    st.session_state.service = None
    st.session_state.ready_to_fetch = False
    st.session_state.emails_loaded = False
    st.session_state.classified_emails = []
    st.session_state.new_alerts = []
    st.session_state.inbox_next_page_token = None
    st.session_state.analyzed_count = 0
    if os.path.exists(TOKEN_FILE):
        os.remove(TOKEN_FILE)


# ============================================================
# LOAD MODELS
# ============================================================
try:
    spam_model, vectorizer, category_model = load_models()
except FileNotFoundError as e:
    st.error(f"Model files not found: {e}")
    st.info("Run `python train_model.py` first to train the models.")
    st.stop()
except Exception as e:
    st.error(f"Failed to load models: {e}")
    st.stop()


# ============================================================
# STEP 1: GMAIL CONNECTION
#   - Try silent auth from saved token (no popup)
#   - If no token, show "Connect Gmail" button
# ============================================================
oauth_client_config = load_oauth_client_config()

if not st.session_state.gmail_connected:
    st.title("Gmail Spam Detector")
    st.markdown("---")

    # Try silent connection first
    service = get_gmail_service_silent()
    if service:
        st.session_state.service = service
        st.session_state.gmail_connected = True
        try:
            st.session_state.profile = get_user_profile(service)
        except Exception:
            st.session_state.profile = {'email': 'Connected', 'total_messages': 0}
        st.rerun()
    elif oauth_client_config and 'web' in oauth_client_config:
        service = handle_web_oauth_return(oauth_client_config)
        if service:
            st.session_state.service = service
            st.session_state.gmail_connected = True
            try:
                st.session_state.profile = get_user_profile(service)
            except Exception:
                st.session_state.profile = {'email': 'Connected', 'total_messages': 0}
            st.rerun()
    else:
        # No valid token - user must click to authenticate
        st.markdown("### Connect Your Gmail Account")
        st.markdown(
            "Click the button below to securely connect your Gmail. "
            "A Google login page will open in your browser."
        )
        if oauth_client_config and 'web' in oauth_client_config:
            st.info(
                "Deploy mode detected. Gmail will use the Web OAuth client from Streamlit Secrets."
            )
        else:
            st.warning(
                "Make sure **credentials.json** is in the project folder "
                "and your email is added as a **test user** in Google Cloud Console."
            )

        auth_error = st.session_state.pop('auth_error', None)
        if auth_error:
            msg = str(auth_error)
            if 'deleted_client' in msg:
                st.error(
                    "Your previous Gmail token is linked to a deleted OAuth client. "
                    "Please click **Connect Gmail** to authorize again with current credentials."
                )
            else:
                st.error(f"Previous auth token was invalid and has been reset: {msg}")

        if st.button("Connect Gmail", type="primary", width='stretch'):
            with st.spinner("Opening Google login in your browser..."):
                try:
                    service = run_oauth_flow()
                    if service:
                        st.session_state.service = service
                        st.session_state.gmail_connected = True
                        st.session_state.profile = get_user_profile(service)
                        st.rerun()
                except Exception as e:
                    msg = str(e)
                    if 'deleted_client' in msg:
                        st.error(
                            "OAuth client appears deleted in Google Cloud. "
                            "Download a fresh OAuth client JSON and try again."
                        )
                    else:
                        st.error(f"Connection failed: {e}")

        st.stop()  # Don't render rest of page until connected


# ============================================================
# STEP 2: KEYWORD SETUP (FIRST PAGE AFTER CONNECT)
# ============================================================
if not st.session_state.emails_loaded and not st.session_state.ready_to_fetch:
    st.title("📧 Gmail Spam Detector")
    st.markdown(f"Connected to **{st.session_state.profile.get('email', '')}**")
    st.markdown("---")

    st.markdown("### 🔑 Set Your Keywords First")
    st.markdown(
        "Before fetching emails, set keywords that are important to you. "
        "Emails matching these keywords will be marked as Important for easy tracking."
    )
    st.info("💡 Examples: your name, project names, company name, meeting, invoice, etc.")

    st.markdown("**Your current keywords:**")
    current_kws = st.session_state.user_keywords
    if current_kws:
        kw_html = ""
        for kw in current_kws:
            kw_html += f'<span class="keyword-tag">{kw}</span> '
        st.markdown(kw_html, unsafe_allow_html=True)
    else:
        st.caption("No keywords yet. Add at least one to continue.")

    add_col, btn_col = st.columns([4, 1])
    with add_col:
        first_kw = st.text_input(
            "Add a keyword:",
            placeholder="e.g. meeting, invoice, project name...",
            key="first_page_keyword_input",
        )
    with btn_col:
        st.markdown("<br>", unsafe_allow_html=True)
        add_first_kw = st.button("Add Keyword", key="first_page_add_kw", width='stretch')

    if add_first_kw and first_kw.strip():
        kw = first_kw.strip().lower()
        if kw not in [k.lower() for k in st.session_state.user_keywords]:
            st.session_state.user_keywords.append(kw)
            save_keywords(st.session_state.user_keywords)
            st.rerun()

    if current_kws:
        remove_kw = st.multiselect(
            "Remove a keyword:",
            current_kws,
            key="first_page_remove_kw",
        )
        if st.button("Remove Selected", key="first_page_remove_btn") and remove_kw:
            st.session_state.user_keywords = [
                k for k in st.session_state.user_keywords if k not in remove_kw
            ]
            save_keywords(st.session_state.user_keywords)
            st.rerun()

    st.markdown("---")
    st.caption(
        f"You have {len(st.session_state.user_keywords)} keyword(s) set. "
        "Ready to fetch emails."
    )

    if st.button("Continue - Fetch and Analyze Emails", type="primary", width='stretch'):
        st.session_state.ready_to_fetch = True
        st.rerun()

    st.stop()


# ============================================================
# STEP 3: INITIAL EMAIL FETCH + CLASSIFY
# ============================================================
if not st.session_state.emails_loaded:
    st.title("Gmail Spam Detector")
    st.markdown(f"Connected to **{st.session_state.profile.get('email', '')}**")
    st.markdown("---")

    status_msg = st.empty()
    progress = st.progress(0, text="Fetching emails from Gmail...")

    try:
        status_msg.info("Fetching your inbox...")
        emails, next_page_token = fetch_emails_page(
            st.session_state.service,
            max_results=30,
            page_token=None,
        )
        progress.progress(0.4, text=f"Fetched {len(emails)} emails. Classifying...")

        if not emails:
            st.warning("No emails found in inbox.")
            st.session_state.emails_loaded = True
            st.session_state.last_check = datetime.now()
            st.rerun()

        classified = []
        total = len(emails)
        user_kw = st.session_state.user_keywords
        for idx, email in enumerate(emails):
            email = classify_email(spam_model, vectorizer, category_model, email, user_kw)
            classified.append(email)
            pct = 0.4 + (0.6 * (idx + 1) / total)
            progress.progress(pct, text=f"Classifying email {idx + 1}/{total}...")

        st.session_state.classified_emails = classified
        st.session_state.last_check = datetime.now()
        st.session_state.emails_loaded = True
        st.session_state.inbox_next_page_token = next_page_token
        st.session_state.analyzed_count = len(classified)
        progress.empty()
        status_msg.empty()
        st.rerun()

    except Exception as e:
        progress.empty()
        status_msg.error(f"Failed to fetch emails: {e}")
        if st.button("Retry"):
            st.rerun()
        st.stop()


# ============================================================
# STEP 4: AUTO-REFRESH FRAGMENT (non-blocking)
# Runs independently every N seconds without freezing the UI.
# ============================================================
@st.fragment(run_every=timedelta(seconds=AUTO_REFRESH_SECONDS))
def auto_check_new_emails():
    """Background fragment that polls for new emails."""
    if not st.session_state.auto_refresh:
        return
    if not st.session_state.gmail_connected:
        return

    try:
        service = st.session_state.service
        known_ids = set(e['id'] for e in st.session_state.classified_emails)
        new_emails = fetch_new_emails(service, known_ids, max_results=10)

        if new_emails:
            user_kw = st.session_state.user_keywords
            for email in new_emails:
                classify_email(spam_model, vectorizer, category_model, email, user_kw)

            st.session_state.new_alerts = new_emails + st.session_state.new_alerts
            st.session_state.classified_emails = new_emails + st.session_state.classified_emails
            st.session_state.last_check = datetime.now()

            # Toast with keyword match info
            kw_matches = [e for e in new_emails if e.get('matched_keywords')]
            if kw_matches:
                st.toast(f"{len(new_emails)} new email(s)! Important {len(kw_matches)} match your keywords!")
            else:
                st.toast(f"{len(new_emails)} new email(s) detected!")
        else:
            st.session_state.last_check = datetime.now()
    except Exception:
        pass  # Silently retry on next cycle


# Place the fragment (it runs in the background)
auto_check_new_emails()


# ============================================================
# STEP 5: SCHEDULED REPORT AUTO-CHECK
# Checks every 60 seconds if a scheduled report is due
# ============================================================
@st.fragment(run_every=timedelta(seconds=60))
def auto_scheduled_report():
    """Auto-generate reports based on user's frequency setting."""
    settings = st.session_state.report_settings
    freq = settings.get('frequency', 'Off')
    if freq == 'Off':
        return

    now = datetime.now()
    last_report_str = settings.get('last_report')

    if last_report_str:
        try:
            last_report_dt = datetime.strptime(last_report_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            last_report_dt = None
    else:
        last_report_dt = None

    # Determine if a report is due
    report_due = False
    if last_report_dt is None:
        report_due = True  # First ever report
    elif freq == 'Daily' and (now - last_report_dt) >= timedelta(days=1):
        report_due = True
    elif freq == 'Weekly' and (now - last_report_dt) >= timedelta(weeks=1):
        report_due = True
    elif freq == 'Monthly' and (now - last_report_dt) >= timedelta(days=30):
        report_due = True

    if not report_due:
        return

    # Generate the report
    emails = st.session_state.classified_emails
    total = len(emails)
    if total == 0:
        return

    spam_count = sum(1 for e in emails if e.get('prediction') == 'SPAM')
    safe_count = total - spam_count
    imp_count = sum(1 for e in emails if e.get('importance') == 'Important')
    spam_pct_val = (spam_count / total * 100) if total > 0 else 0

    cat_breakdown = {}
    for e in emails:
        c = e.get('category', 'Unknown')
        cat_breakdown[c] = cat_breakdown.get(c, 0) + 1

    kw_summary = {}
    for e in emails:
        for kw in e.get('matched_keywords', []):
            kw_summary[kw] = kw_summary.get(kw, 0) + 1

    report = {
        'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
        'total_emails': total,
        'spam_count': spam_count,
        'safe_count': safe_count,
        'important_count': imp_count,
        'spam_percentage': round(spam_pct_val, 1),
        'category_breakdown': cat_breakdown,
        'keyword_matches': kw_summary,
        'type': f'Scheduled ({freq})',
    }

    st.session_state.report_history.insert(0, report)
    save_report_history(st.session_state.report_history)
    st.session_state.report_settings['last_report'] = report['generated_at']
    save_report_settings(st.session_state.report_settings)

    # Add persistent notification
    notif = {
        'message': f"Your {freq} Spam Report is ready! Check it in the sidebar under Scheduled Reports.",
        'freq': freq,
        'time': report['generated_at'],
        'spam_count': spam_count,
        'safe_count': safe_count,
        'total': total,
        'spam_pct': round(spam_pct_val, 1),
    }
    st.session_state.report_notifications.insert(0, notif)
    st.toast(f"Report {freq} spam report generated! Check it in the sidebar.")


auto_scheduled_report()


# ============================================================
# MAIN DASHBOARD
# ============================================================
profile = st.session_state.profile
last_time = st.session_state.last_check
last_str = last_time.strftime('%I:%M:%S %p') if last_time else 'N/A'

# If auth succeeded but profile is empty, fetch it once to avoid showing "****".
if st.session_state.gmail_connected and not profile.get('email'):
    try:
        refreshed_profile = get_user_profile(st.session_state.service)
        st.session_state.profile = refreshed_profile
        profile = refreshed_profile
    except Exception:
        st.session_state.profile = {
            'email': 'Connected (account hidden)',
            'total_messages': profile.get('total_messages', 0),
        }
        profile = st.session_state.profile

hdr_left, hdr_right = st.columns([5, 1])
with hdr_left:
    st.markdown("# 📧 Gmail Spam Detector")
    st.markdown(
        f"Connected to: **{profile.get('email', '')}** &nbsp;|&nbsp; "
        f"Last checked: **{last_str}**"
    )
with hdr_right:
    st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
    if st.button("🔌 Disconnect Gmail", key="top_disconnect", width='stretch'):
        disconnect_gmail_session()
        st.rerun()

st.markdown("""
<div class="analyze-shell">
    <strong>🚀 Analyze Inbox in Batches</strong><br>
    Process emails in focused chunks of 30 for faster, cleaner review.
</div>
""", unsafe_allow_html=True)

total_messages = int(profile.get('total_messages', 0) or 0)
approx_remaining = max(total_messages - len(st.session_state.classified_emails), 0)
if st.button("🚀 Analyze Next 30", key="main_analyze_next_30", type="primary", width='stretch'):
    try:
        service = st.session_state.service
        page_token = st.session_state.inbox_next_page_token
        if not page_token:
            st.info("✅ All inbox pages have already been analyzed.")
        else:
            batch, next_page_token = fetch_emails_page(
                service,
                max_results=30,
                page_token=page_token,
            )

            known_ids = set(e['id'] for e in st.session_state.classified_emails)
            batch = [e for e in batch if e['id'] not in known_ids]

            if batch:
                user_kw = st.session_state.user_keywords
                for email in batch:
                    classify_email(spam_model, vectorizer, category_model, email, user_kw)
                st.session_state.classified_emails.extend(batch)
                st.session_state.analyzed_count += len(batch)
                st.session_state.last_check = datetime.now()
                st.success(
                    f"Analyzed {len(batch)} more emails (total analyzed: {st.session_state.analyzed_count})."
                )
            else:
                st.info("No unseen emails found in the next page.")

            st.session_state.inbox_next_page_token = next_page_token
            if not next_page_token:
                st.info("✅ Inbox analysis is complete. No more pages left.")
            st.rerun()
    except Exception as e:
        st.error(f"Analyze Next 30 failed: {e}")

all_emails = st.session_state.classified_emails
spam_emails = [e for e in all_emails if e.get('prediction') == 'SPAM']
safe_emails = [e for e in all_emails if e.get('prediction') == 'NOT SPAM']
unread_emails = [e for e in all_emails if e.get('is_unread', False)]
important_emails = [e for e in all_emails if e.get('importance') == 'Important']


# ============================================================
# TOP METRICS
# ============================================================
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="info-card">
        <div class="big-number">📨 {len(all_emails)}</div>
        <div class="center-text">Total Emails</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="spam-card">
        <div class="big-number">🚫 {len(spam_emails)}</div>
        <div class="center-text">Spam Detected</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="ham-card">
        <div class="big-number">✅ {len(safe_emails)}</div>
        <div class="center-text">Safe Emails</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="alert-card">
        <div class="big-number">📩 {len(unread_emails)}</div>
        <div class="center-text">Unread</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# INBOX HEALTH BAR
# ============================================================
if all_emails:
    spam_pct = (len(spam_emails) / len(all_emails)) * 100
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Inbox Health:** {100 - spam_pct:.0f}% clean")
        st.progress((100 - spam_pct) / 100)
    with col2:
        if spam_pct > 50:
            st.error(f"Warning: {spam_pct:.0f}% spam!")
        elif spam_pct > 20:
            st.warning(f"Warning: {spam_pct:.0f}% spam")
        else:
            st.success(f"Only {spam_pct:.0f}% spam")


# ============================================================
# REPORT NOTIFICATIONS
# ============================================================
if st.session_state.report_notifications:
    st.markdown("---")
    st.markdown("### Report Notifications")
    for i, notif in enumerate(st.session_state.report_notifications):
        freq_lower = notif.get('freq', 'daily').lower()
        freq_icon = {'daily': 'Daily', 'weekly': 'Weekly', 'monthly': 'Monthly'}.get(freq_lower, 'Report')
        st.markdown(f"""
        <div class="report-notification {freq_lower}">
            <div>
                <strong>{freq_icon} {notif['freq']} Report Ready!</strong><br>
                {notif['message']}<br>
                <small>Analytics {notif['total']} emails analyzed &nbsp;|&nbsp; 
                Spam: {notif['spam_count']} spam ({notif['spam_pct']}%) &nbsp;|&nbsp; 
                Safe {notif['safe_count']} safe &nbsp;|&nbsp;
                Generated: {notif['time']}</small>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.button("Dismiss Report Notifications", key="dismiss_report_notifs"):
        st.session_state.report_notifications = []
        st.rerun()

# ============================================================
# NEW EMAIL ALERTS
# ============================================================
if st.session_state.new_alerts:
    st.markdown("---")
    st.markdown("### New Email Alerts")
    for email in st.session_state.new_alerts:
        icon = "Spam" if email.get('prediction') == 'SPAM' else "Safe"
        card = "spam-card" if email.get('prediction') == 'SPAM' else "ham-card"
        st.markdown(f"""
        <div class="{card}">
            <strong>{icon} NEW: {email['subject']}</strong><br>
            From: {email['sender']}<br>
            Result: <strong>{email.get('prediction', '?')}</strong>
            ({email.get('confidence', 0):.1f}%) |
            Category: <strong>{email.get('category', '?')}</strong> |
            Sub: <strong>{email.get('sub_category', '?')}</strong>
            {'| <span class="keyword-match">Important ' + ', '.join(email.get('matched_keywords', [])) + '</span>' if email.get('matched_keywords') else ''}
        </div>
        """, unsafe_allow_html=True)

    if st.button("Clear Alerts"):
        st.session_state.new_alerts = []
        st.rerun()


# ============================================================
# TABS
# ============================================================
st.markdown("---")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📥 All Emails",
    "🚫 Spam Emails",
    "✅ Safe Emails",
    "🗂️ Categories",
    "🔑 Keywords",
    "📊 Analytics"
])


# --- Tab 1: All Emails ---
with tab1:
    st.markdown(f"### All Emails ({len(all_emails)})")

    search = st.text_input("Search emails:", placeholder="Search by subject, sender...")

    filtered = all_emails
    if search:
        search_lower = search.lower()
        filtered = [
            e for e in filtered
            if search_lower in e['subject'].lower()
            or search_lower in e['sender'].lower()
        ]

    for email in filtered:
        is_spam = email.get('prediction') == 'SPAM'
        card = "spam-card" if is_spam else "ham-card"
        icon = "Spam" if is_spam else "Safe"
        unread = "Unread: " if email.get('is_unread') else ""

        st.markdown(f"""
        <div class="{card}">
            {unread}<strong>{icon} {email['subject']}</strong><br>
            <strong>From:</strong> {email['sender']}<br>
            <strong>Date:</strong> {email.get('date', '')}<br>
            <strong>Result:</strong> {email.get('prediction', '?')}
            ({email.get('confidence', 0):.1f}%) |
            <strong>Category:</strong> {email.get('category', '?')} |
            <strong>Sub:</strong> {email.get('sub_category', '?')}
            {'| <span class="keyword-match">Important ' + ', '.join(email.get('matched_keywords', [])) + '</span>' if email.get('matched_keywords') else ''}<br>
            <strong>Preview:</strong> {email.get('snippet', '')[:150]}...
        </div>
        """, unsafe_allow_html=True)


# --- Tab 2: Spam Emails ---
with tab2:
    if spam_emails:
        st.error(f"### {len(spam_emails)} Spam Emails Detected")

        spam_cats = {}
        for e in spam_emails:
            cat = e.get('sub_category', 'General Spam')
            spam_cats.setdefault(cat, []).append(e)

        for cat, emails_list in spam_cats.items():
            with st.expander(f"{cat} ({len(emails_list)} emails)", expanded=True):
                for email in emails_list:
                    st.markdown(f"""
                    <div class="spam-card">
                        <strong>{email['subject']}</strong><br>
                        From: {email['sender']} | Date: {email.get('date', '')}<br>
                        Confidence: {email.get('confidence', 0):.1f}%<br>
                        Preview: {email.get('snippet', '')[:120]}...
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.success("No spam detected! Your inbox is clean!")


# --- Tab 3: Safe Emails ---
with tab3:
    if safe_emails:
        st.success(f"### {len(safe_emails)} Safe Emails")

        safe_cats = {}
        for e in safe_emails:
            cat = e.get('category', 'General')
            safe_cats.setdefault(cat, []).append(e)

        for cat, emails_list in safe_cats.items():
            with st.expander(f"{cat} ({len(emails_list)} emails)", expanded=False):
                for email in emails_list:
                    st.markdown(f"""
                    <div class="ham-card">
                        <strong>{email['subject']}</strong><br>
                        From: {email['sender']} | Date: {email.get('date', '')}<br>
                        Category: {email.get('category', '?')} |
                        Confidence: {email.get('confidence', 0):.1f}%<br>
                        Preview: {email.get('snippet', '')[:120]}...
                    </div>
                    """, unsafe_allow_html=True)
    else:
        st.warning("No safe emails found.")


# --- Tab 4: Categories ---
with tab4:
    st.markdown("### Email Categories")

    all_cats = {}
    for e in all_emails:
        cat = e.get('category', 'Unknown')
        all_cats.setdefault(cat, []).append(e)

    # Summary cards
    cols = st.columns(3)
    for idx, (cat, emails_list) in enumerate(sorted(all_cats.items())):
        spam_in_cat = sum(1 for e in emails_list if e.get('prediction') == 'SPAM')
        safe_in_cat = len(emails_list) - spam_in_cat

        with cols[idx % 3]:
            st.markdown(f"""
            <div class="info-card">
                <strong>{cat}</strong><br>
                Total: {len(emails_list)} |
                Spam: {spam_in_cat} spam |
                Safe {safe_in_cat} safe
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    selected_cat = st.selectbox("Select category to view:", list(all_cats.keys()))
    if selected_cat and selected_cat in all_cats:
        st.markdown(f"#### {selected_cat}")
        for email in all_cats[selected_cat]:
            is_spam = email.get('prediction') == 'SPAM'
            card = "spam-card" if is_spam else "ham-card"
            icon = "Spam" if is_spam else "Safe"
            st.markdown(f"""
            <div class="{card}">
                <strong>{icon} {email['subject']}</strong><br>
                From: {email['sender']} |
                {email.get('prediction', '?')} ({email.get('confidence', 0):.1f}%)<br>
                Sub-category: {email.get('sub_category', '?')}<br>
                Preview: {email.get('snippet', '')[:120]}...
            </div>
            """, unsafe_allow_html=True)


# --- Tab 5: Keywords ---
with tab5:
    st.markdown("### Keyword-Based Importance")

    st.markdown(
        "Set keywords that matter to you. Emails matching these keywords "
        "will be tagged as **Important**. Keywords are saved and persist across sessions."
    )

    # --- Add keywords ---
    kw_col1, kw_col2 = st.columns([3, 1])
    with kw_col1:
        new_kw = st.text_input(
            "Add keyword:",
            placeholder="e.g. meeting, deadline, invoice, professor...",
            key="new_keyword_input"
        )
    with kw_col2:
        st.markdown("<br>", unsafe_allow_html=True)
        add_clicked = st.button("Add Keyword", width='stretch')

    if add_clicked and new_kw.strip():
        kw = new_kw.strip().lower()
        if kw not in [k.lower() for k in st.session_state.user_keywords]:
            st.session_state.user_keywords.append(kw)
            save_keywords(st.session_state.user_keywords)
            st.success(f"Added keyword: **{kw}**")
            # Re-classify all emails with updated keywords
            for email in st.session_state.classified_emails:
                imp, matched = check_keyword_importance(email, st.session_state.user_keywords)
                email['importance'] = imp
                email['matched_keywords'] = matched
            st.rerun()
        else:
            st.warning(f"Keyword **{kw}** already exists.")

    # --- Display current keywords ---
    current_kws = st.session_state.user_keywords
    if current_kws:
        st.markdown("#### Your Keywords:")
        kw_html = ""
        for kw in current_kws:
            kw_html += f'<span class="keyword-tag">{kw}</span> '
        st.markdown(kw_html, unsafe_allow_html=True)

        st.markdown("")
        # Delete keywords
        kw_to_delete = st.multiselect(
            "Select keywords to remove:",
            current_kws,
            key="kw_delete_select"
        )
        if st.button("Delete Selected Keywords"):
            if kw_to_delete:
                st.session_state.user_keywords = [
                    k for k in st.session_state.user_keywords if k not in kw_to_delete
                ]
                save_keywords(st.session_state.user_keywords)
                # Re-classify
                for email in st.session_state.classified_emails:
                    imp, matched = check_keyword_importance(email, st.session_state.user_keywords)
                    email['importance'] = imp
                    email['matched_keywords'] = matched
                st.success(f"Deleted {len(kw_to_delete)} keyword(s).")
                st.rerun()

        # --- Show important emails ---
        st.markdown("---")
        st.markdown(f"#### Important Emails ({len(important_emails)})")

        if important_emails:
            for email in important_emails:
                is_spam = email.get('prediction') == 'SPAM'
                card = "spam-card" if is_spam else "important-card"
                icon = "Spam" if is_spam else "Important"
                matched_str = ", ".join(email.get('matched_keywords', []))
                st.markdown(f"""
                <div class="{card}">
                    <strong>{icon} {email['subject']}</strong>
                    <span class="keyword-match">Keywords: {matched_str}</span><br>
                    <strong>From:</strong> {email['sender']}<br>
                    <strong>Date:</strong> {email.get('date', '')}<br>
                    <strong>Result:</strong> {email.get('prediction', '?')}
                    ({email.get('confidence', 0):.1f}%) |
                    <strong>Category:</strong> {email.get('category', '?')}<br>
                    <strong>Preview:</strong> {email.get('snippet', '')[:150]}...
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No emails match your keywords yet. Add keywords above!")
    else:
        st.info("No keywords set. Add keywords above to start filtering important emails.")


# --- Tab 6: Analytics ---
with tab6:
    st.markdown("### Email Analytics")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Spam vs Safe")
        chart_data = pd.DataFrame({
            'Type': ['Spam', 'Safe'],
            'Count': [len(spam_emails), len(safe_emails)]
        })
        st.bar_chart(chart_data.set_index('Type'))

    with col2:
        st.markdown("#### Category Distribution")
        cat_counts = {}
        for e in all_emails:
            c = e.get('category', 'Unknown')
            cat_counts[c] = cat_counts.get(c, 0) + 1
        cat_df = pd.DataFrame({
            'Category': list(cat_counts.keys()),
            'Count': list(cat_counts.values())
        })
        st.bar_chart(cat_df.set_index('Category'))

    st.markdown("---")

    # Confidence scores table
    st.markdown("#### Confidence Scores")
    conf_data = pd.DataFrame({
        'Email': [e['subject'][:40] for e in all_emails],
        'Confidence': [e.get('confidence', 0) for e in all_emails],
        'Type': [e.get('prediction', '?') for e in all_emails],
        'Category': [e.get('category', '?') for e in all_emails],
    })
    st.dataframe(conf_data, width='stretch')

    st.markdown("---")

    # Full report table
    st.markdown("#### Complete Email Report")
    table_data = []
    for e in all_emails:
        table_data.append({
            'Subject': e['subject'][:50],
            'From': e['sender'][:30],
            'Classification': e.get('prediction', '?'),
            'Category': e.get('category', '?'),
            'Sub-Category': e.get('sub_category', '?'),
            'Confidence': f"{e.get('confidence', 0):.1f}%",
            'Unread': 'Yes' if e.get('is_unread') else 'No'
        })

    df = pd.DataFrame(table_data)
    st.dataframe(df, width='stretch', height=400)

    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Report as CSV",
        data=csv,
        file_name=f"spam_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )


# ============================================================
# SIDEBAR: CONTROLS
# ============================================================
with st.sidebar:
    st.header("👤 Account")
    st.markdown(f"**{profile.get('email', '')}**")
    st.markdown(f"Total messages: {profile.get('total_messages', 'N/A')}")

    st.markdown(
        f"<div style='font-weight:700; color:#1f4ed8; margin:8px 0 4px 0;'>📊 Analyzed so far: {len(st.session_state.classified_emails)}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f"<div style='font-weight:700; color:#15803d; margin:0 0 8px 0;'>📬 Approx remaining: {approx_remaining}</div>",
        unsafe_allow_html=True,
    )

    st.divider()

    st.header("📡 Real-time Monitor")
    st.session_state.auto_refresh = st.toggle(
        "Auto-check new emails",
        value=st.session_state.auto_refresh,
        help=f"Automatically checks for new emails every {AUTO_REFRESH_SECONDS} seconds"
    )

    if st.button("Check Now", width='stretch'):
        try:
            service = st.session_state.service
            known_ids = set(e['id'] for e in st.session_state.classified_emails)
            new = fetch_new_emails(service, known_ids)
            if new:
                user_kw = st.session_state.user_keywords
                for email in new:
                    classify_email(spam_model, vectorizer, category_model, email, user_kw)
                st.session_state.new_alerts = new + st.session_state.new_alerts
                st.session_state.classified_emails = new + st.session_state.classified_emails
                st.session_state.last_check = datetime.now()
                st.success(f"{len(new)} new emails found!")
                st.rerun()
            else:
                st.session_state.last_check = datetime.now()
                st.info("No new emails.")
        except Exception as e:
            st.error(f"Error: {e}")

    if st.button("Re-scan All Emails", width='stretch'):
        st.session_state.ready_to_fetch = False
        st.session_state.emails_loaded = False
        st.session_state.classified_emails = []
        st.session_state.new_alerts = []
        st.session_state.inbox_next_page_token = None
        st.session_state.analyzed_count = 0
        st.rerun()
    st.divider()

    # Keyword management shortcut in sidebar
    st.header("🔑 Keywords")
    if st.session_state.user_keywords:
        kw_sidebar_html = ""
        for kw in st.session_state.user_keywords:
            kw_sidebar_html += f'<span class="keyword-tag">{kw}</span> '
        st.markdown(kw_sidebar_html, unsafe_allow_html=True)
    else:
        st.caption("No keywords set")

    sidebar_kw = st.text_input("Quick add keyword:", key="sidebar_kw_input", placeholder="e.g. meeting")
    if st.button("Add", key="sidebar_kw_btn"):
        if sidebar_kw.strip():
            kw = sidebar_kw.strip().lower()
            if kw not in [k.lower() for k in st.session_state.user_keywords]:
                st.session_state.user_keywords.append(kw)
                save_keywords(st.session_state.user_keywords)
                for email in st.session_state.classified_emails:
                    imp, matched = check_keyword_importance(email, st.session_state.user_keywords)
                    email['importance'] = imp
                    email['matched_keywords'] = matched
                st.rerun()

    st.divider()

    # Report schedule status
    st.header("🗓️ Scheduled Reports")

    freq_options = ['Off', 'Daily', 'Weekly', 'Monthly']
    current_freq = st.session_state.report_settings.get('frequency', 'Off')
    selected_freq = st.selectbox(
        "Report frequency:",
        freq_options,
        index=freq_options.index(current_freq) if current_freq in freq_options else 0,
        key="sidebar_report_freq"
    )
    if selected_freq != current_freq:
        st.session_state.report_settings['frequency'] = selected_freq
        save_report_settings(st.session_state.report_settings)
        st.success(f"Set to **{selected_freq}**")

    last_rpt = st.session_state.report_settings.get('last_report')
    st.caption(f"Last report: {last_rpt or 'Never'}")

    if st.button("Generate Report Now", key="sidebar_gen_report", width='stretch'):
        now = datetime.now()
        total = len(all_emails)
        spam_count = len(spam_emails)
        safe_count = len(safe_emails)
        imp_count = len(important_emails)
        spam_pct_val = (spam_count / total * 100) if total > 0 else 0

        cat_breakdown = {}
        for e in all_emails:
            c = e.get('category', 'Unknown')
            cat_breakdown[c] = cat_breakdown.get(c, 0) + 1

        kw_summary = {}
        for e in all_emails:
            for kw in e.get('matched_keywords', []):
                kw_summary[kw] = kw_summary.get(kw, 0) + 1

        report = {
            'generated_at': now.strftime('%Y-%m-%d %H:%M:%S'),
            'total_emails': total,
            'spam_count': spam_count,
            'safe_count': safe_count,
            'important_count': imp_count,
            'spam_percentage': round(spam_pct_val, 1),
            'category_breakdown': cat_breakdown,
            'keyword_matches': kw_summary,
            'type': 'Manual',
        }

        st.session_state.report_history.insert(0, report)
        save_report_history(st.session_state.report_history)
        st.session_state.report_settings['last_report'] = report['generated_at']
        save_report_settings(st.session_state.report_settings)

        # Add notification for manual report too
        notif = {
            'message': f"Your Manual Spam Report is ready! Check the summary below.",
            'freq': 'Manual',
            'time': report['generated_at'],
            'spam_count': spam_count,
            'safe_count': safe_count,
            'total': total,
            'spam_pct': round(spam_pct_val, 1),
        }
        st.session_state.report_notifications.insert(0, notif)
        st.success("Report generated!")
        st.rerun()

    # Show latest report summary in sidebar
    reports = st.session_state.report_history
    if reports:
        latest = reports[0]
        st.caption(f"Latest: {latest['spam_count']} spam / {latest['safe_count']} safe ({latest['spam_percentage']}% spam)")
        report_df = pd.DataFrame([{
            'Generated': latest['generated_at'],
            'Total': latest['total_emails'],
            'Spam': latest['spam_count'],
            'Safe': latest['safe_count'],
            'Spam %': latest['spam_percentage'],
        }])
        st.download_button(
            "Download Latest Report",
            data=report_df.to_csv(index=False),
            file_name=f"spam_report_{latest['generated_at'].replace(':', '-').replace(' ', '_')}.csv",
            mime="text/csv",
            key="sidebar_dl_report"
        )

        if st.button("Clear History", key="sidebar_clear_reports"):
            st.session_state.report_history = []
            save_report_history([])
            st.rerun()

    st.divider()

    # Manual quick test
    st.header("🧪 Quick Test")
    test_text = st.text_area(
        "Test any text:", height=80,
        placeholder="Paste any email text to classify..."
    )
    if st.button("Classify", width='stretch'):
        if test_text.strip():
            cleaned = clean_text(test_text)
            vec = vectorizer.transform([cleaned])
            pred = spam_model.predict(vec)[0]
            conf = spam_model.predict_proba(vec)[0]
            if pred == 1:
                st.error(f"SPAM ({conf[1] * 100:.1f}%)")
            else:
                cat = category_model.predict(vec)[0]
                cat_map = {'work': 'Work', 'promotional': 'Promotional', 'academic': 'Academic'}
                cat_name = cat_map.get(cat, cat.title())
                st.success(f"NOT SPAM ({conf[0] * 100:.1f}%)")
                st.info(f"Category: {cat_name}")
