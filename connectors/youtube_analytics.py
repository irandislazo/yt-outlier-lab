# connectors/youtube_analytics.py
"""
Conector OAuth para YouTube Analytics API.
Solo necesario para 'Mi Canal'.
"""
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TOKEN_FILE        = Path("token.json")
CLIENT_SECRET_FILE = Path("client_secret.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


class YouTubeAnalyticsConnector:

    def __init__(self):
        self.credentials = None
        self._load()

    def _load(self):
        if not TOKEN_FILE.exists():
            return
        try:
            from google.oauth2.credentials import Credentials
            from google.auth.transport.requests import Request

            with open(TOKEN_FILE) as f:
                data = json.load(f)
            self.credentials = Credentials.from_authorized_user_info(data, SCOPES)

            if self.credentials.expired and self.credentials.refresh_token:
                self.credentials.refresh(Request())
                self._save()
        except Exception as e:
            logger.warning(f"Error cargando token: {e}")
            self.credentials = None

    def _save(self):
        if self.credentials:
            with open(TOKEN_FILE, "w") as f:
                f.write(self.credentials.to_json())

    def is_authenticated(self) -> bool:
        return (
            self.credentials is not None and
            self.credentials.valid
        )

    def authenticate(self) -> bool:
        if not CLIENT_SECRET_FILE.exists():
            logger.error("No se encontró client_secret.json")
            return False
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CLIENT_SECRET_FILE), SCOPES
            )
            self.credentials = flow.run_local_server(port=8080)
            self._save()
            return True
        except Exception as e:
            logger.error(f"Error OAuth: {e}")
            return False