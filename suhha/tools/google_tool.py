"""Gmail + Google Calendar via OAuth (installed-app flow).

Setup (one time):
  1. Google Cloud Console -> create OAuth client ID, type "Desktop app".
  2. Enable the Gmail API and Google Calendar API for the project.
  3. Download the client secret JSON, save it as credentials.json in the
     project root.
  4. First call here opens a browser to authorize; a token.json is cached
     afterwards so you don't need to log in again.
"""
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from ..config import GOOGLE_CREDENTIALS_FILE, GOOGLE_TOKEN_FILE

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/calendar",
]


def _get_credentials() -> Credentials:
    creds = None
    if GOOGLE_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(GOOGLE_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not GOOGLE_CREDENTIALS_FILE.exists():
                raise RuntimeError(
                    "credentials.json مش موجود. اعمليه من Google Cloud Console "
                    "(README فيه الخطوات) وحطيه في جذر المشروع."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(GOOGLE_CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)
        GOOGLE_TOKEN_FILE.write_text(creds.to_json(), encoding="utf-8")
    return creds


def list_recent_emails(max_results: int = 10) -> list[dict]:
    service = build("gmail", "v1", credentials=_get_credentials())
    resp = service.users().messages().list(userId="me", maxResults=max_results).execute()
    out = []
    for m in resp.get("messages", []):
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=m["id"], format="metadata", metadataHeaders=["Subject", "From"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
        out.append(
            {
                "id": m["id"],
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "snippet": msg.get("snippet", ""),
            }
        )
    return out


def send_email(to: str, subject: str, body: str) -> dict:
    service = build("gmail", "v1", credentials=_get_credentials())
    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return {"id": sent["id"]}


def list_upcoming_events(max_results: int = 10) -> list[dict]:
    import datetime

    service = build("calendar", "v3", credentials=_get_credentials())
    now = datetime.datetime.utcnow().isoformat() + "Z"
    resp = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    return [
        {
            "summary": e.get("summary", ""),
            "start": e["start"].get("dateTime", e["start"].get("date")),
            "id": e["id"],
        }
        for e in resp.get("items", [])
    ]


def create_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> dict:
    service = build("calendar", "v3", credentials=_get_credentials())
    event = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
    }
    created = service.events().insert(calendarId="primary", body=event).execute()
    return {"id": created["id"], "link": created.get("htmlLink", "")}
