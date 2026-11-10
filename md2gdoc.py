#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-api-python-client",
#     "google-auth-oauthlib",
#     "google-auth-httplib2",
# ]
# ///
"""md2gdoc — upload a Markdown file as a Google Doc using Drive's native conversion.

This uses Drive's import-on-upload path (the same code path as File > Open in
Google Docs), NOT the clipboard-paste path. The result is a properly formatted
Google Doc with real headings, lists, tables, code blocks, and links.
"""

import argparse
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# drive.file is the minimal scope: this app can only see files it created.
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

CONFIG_DIR = Path.home() / ".config" / "md2gdoc"
CLIENT_SECRETS = CONFIG_DIR / "client_secrets.json"

SETUP_HELP = f"""\
Missing OAuth client secrets at {CLIENT_SECRETS}.

One-time setup (5 minutes):
  1. Open https://console.cloud.google.com/
  2. Create a new project (or pick an existing one)
  3. APIs & Services > Library > enable "Google Drive API"
  4. APIs & Services > OAuth consent screen
       - User type: External
       - App name: md2gdoc (or whatever)
       - Add yourself (and any other Google accounts you'll use) as test users
  5. APIs & Services > Credentials > Create Credentials > OAuth client ID
       - Application type: Desktop app
       - Name: md2gdoc
  6. Download the JSON, then:
       mkdir -p {CONFIG_DIR}
       mv ~/Downloads/client_secret_*.json {CLIENT_SECRETS}

The same client_secrets.json works for ALL accounts you sign in with — the
account is chosen at sign-in time, not at credential-creation time.

Full walkthrough: https://github.com/benstein/md2gdoc#one-time-google-cloud-setup
"""


def get_credentials(account: str) -> Credentials:
    token_path = CONFIG_DIR / f"token-{account}.json"
    creds = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if creds and creds.valid:
        return creds

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            token_path.write_text(creds.to_json())
            return creds
        except Exception as e:
            print(f"Token refresh failed ({e}); re-running browser auth.", file=sys.stderr)

    if not CLIENT_SECRETS.exists():
        sys.exit(SETUP_HELP)

    print(f"No valid token for account '{account}'. Launching browser...", file=sys.stderr)
    print(
        f"  >> Sign in with the Google account you want to bind to '{account}'. <<",
        file=sys.stderr,
    )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRETS), SCOPES)
    creds = flow.run_local_server(port=0, open_browser=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    print(f"Saved token to {token_path}", file=sys.stderr)
    return creds


def upload(src: Path, title: str, account: str, folder_id: str | None) -> str:
    creds = get_credentials(account)
    service = build("drive", "v3", credentials=creds, cache_discovery=False)

    metadata: dict = {
        "name": title,
        # The magic: target mimeType triggers Drive's markdown-import path.
        "mimeType": "application/vnd.google-apps.document",
    }
    if folder_id:
        metadata["parents"] = [folder_id]

    media = MediaFileUpload(str(src), mimetype="text/markdown", resumable=False)

    try:
        result = (
            service.files()
            .create(
                body=metadata,
                media_body=media,
                fields="id, webViewLink",
                supportsAllDrives=True,
            )
            .execute()
        )
    except HttpError as e:
        sys.exit(f"Drive API error: {e}")

    return result["webViewLink"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a Markdown file as a properly-formatted Google Doc.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Account profiles let you switch between Google accounts. The first time\n"
            "you use an account name, a browser window opens for you to sign in; the\n"
            "token is then cached at ~/.config/md2gdoc/token-<account>.json.\n\n"
            "Examples:\n"
            "  md2gdoc draft.md\n"
            "  md2gdoc draft.md --account work\n"
            "  md2gdoc draft.md -a personal --name 'Q2 Plan'\n"
            "  md2gdoc draft.md -a work --folder 1AbCdEfGhIjKlMnOpQrStUv\n"
        ),
    )
    parser.add_argument("file", help="Path to the .md file to upload")
    parser.add_argument(
        "--account",
        "-a",
        default=os.environ.get("MD2GDOC_DEFAULT_ACCOUNT", "personal"),
        help="Account profile name (default: 'personal' or $MD2GDOC_DEFAULT_ACCOUNT). "
        "Use any name you like, e.g. 'personal', 'work', 'gmail', 'client'.",
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Document title (default: filename without extension)",
    )
    parser.add_argument(
        "--folder",
        "-f",
        help="Drive folder ID to place the doc in",
    )
    args = parser.parse_args()

    src = Path(args.file).expanduser().resolve()
    if src.is_dir():
        sys.exit(f"Not a file (is a directory): {src}")
    if not src.is_file():
        sys.exit(f"File not found: {src}")
    if src.suffix.lower() not in (".md", ".markdown", ".txt"):
        print(
            f"Warning: {src.name} doesn't look like a Markdown file; uploading anyway.",
            file=sys.stderr,
        )

    title = args.name or src.stem
    url = upload(src, title, args.account, args.folder)
    print(url)


if __name__ == "__main__":
    main()
