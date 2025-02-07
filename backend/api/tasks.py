
import os
import subprocess
from celery import shared_task
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

FOLDER_ID = "1wGGo8hZImY22bI_ySWDH4AtU4ExLQsLI" 


@shared_task
def process_and_upload_video(file_path, file_name):
    """ Background task to process and upload video to Google Drive """
    try:
        mp4_path = file_path.replace(".webm", ".mp4")

        subprocess.run([
            "ffmpeg", "-i", file_path,
            "-c:v", "libx264", "-preset", "slow",
            "-crf", "18",
            "-b:v", "10000k",
            "-maxrate", "12000k", "-bufsize", "20000k",
            "-vf", "scale=trunc(iw/2)*2:1080",  
            "-r", "60",
            "-c:a", "aac", "-b:a", "320k",
            mp4_path
        ])

        file_metadata = {"name": file_name, "parents": [FOLDER_ID]}
        media = MediaFileUpload(mp4_path, mimetype="video/mp4")

        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded_file.get("id")
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        user_email = "arjunajith440@gmail.com"
        permission = {"type": "user", "role": "reader", "emailAddress": user_email}
        drive_service.permissions().create(fileId=file_id, body=permission).execute()

        os.remove(file_path)
        os.remove(mp4_path)

        return file_link

    except Exception as e:
        return str(e)
