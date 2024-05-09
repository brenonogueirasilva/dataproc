import os.path
import io
import pandas as pd

from datetime import datetime, timezone, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload

class GoogleDrive:
    def __init__(self, credentials_path, token_path) -> None:
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.scopes = ["https://www.googleapis.com/auth/drive"]
        self.creds = self.get_creds()

    def get_creds(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.scopes
                )
                creds = flow.run_local_server(port=0)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
        return creds
    
    def list_files(self, query):
        try:
            service = build("drive", "v3", credentials=self.creds)
            response = service.files().list(q = query, fields="nextPageToken,files(id,name, createdTime, mimeType)").execute()
            files = response.get('files')
            next_page_token = response.get('nextPageToken')

            while next_page_token:
                response = service.files().list(q = query, fields="nextPageToken,files(id,name, createdTime, mimeType)").execute()
                files = response.get('files')
                next_page_token = response.get('nextPageToken')
            data_frame_list = pd.DataFrame(files)
            return data_frame_list
        except HttpError as error:
            print(f"An error occurred: {error}")
    
    def generate_query(self, folder_id = None, date_start = None):
        ls_query = []
        if folder_id is not None:
            folder_query = f"parents = '{folder_id}'"
            ls_query.append(folder_query)
        if date_start is not None:
            date = date_start
            tz = timezone(timedelta(hours=-3))
            date_start = datetime(date.year, date.month, date.day, date.hour, date.minute , date.second, tzinfo=tz)
            start_of_date_formatted = date_start.strftime('%Y-%m-%dT%H:%M:%S%z')
            date_start_query = f"createdTime > '{start_of_date_formatted}'"
            ls_query.append(date_start_query)
        query_final = 'and '.join(ls_query)
        return query_final
    
    def download_file(self, file_id, file_name, folder):
        try:
            service = build("drive", "v3", credentials=self.creds)
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"Download {int(status.progress() * 100)}.")

            fh.seek(0)
            return fh.read()
            
        except HttpError as error:
            print(f"An error occurred: {error}")
            file = None