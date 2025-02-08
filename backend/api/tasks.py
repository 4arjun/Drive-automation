import os
import subprocess
import logging
import time
from celery import shared_task
from googleapiclient.http import MediaFileUpload
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Drive Credentials
SERVICE_ACCOUNT_FILE = "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build("drive", "v3", credentials=creds)

# Google Drive Folder ID
FOLDER_ID = "1wGGo8hZImY22bI_ySWDH4AtU4ExLQsLI"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_and_upload_video(self, file_path, file_name):
    """ Background task to process and upload video to Google Drive """
    try:
        logger.info(f"🎥 Processing video: {file_path}")

        # 🔹 Wait to ensure file system sync
        time.sleep(2)

        # 🔹 Verify file exists before processing
        if not os.path.exists(file_path):
            logger.error(f"❌ File not found: {file_path}")
            return {"status": "error", "message": f"File not found: {file_path}"}

        # Define MP4 output path
        mp4_path = file_path.replace(".webm", ".mp4")

        # 🔹 Optimize FFmpeg settings for better stability
        ffmpeg_command = [
            "ffmpeg", "-y", "-i", file_path,
            "-c:v", "libx264", "-preset", "fast",  # ✅ Reduce CPU usage
            "-crf", "23",  # ✅ Lower quality slightly to reduce file size
            "-b:v", "5000k",  # ✅ Lower bitrate for performance
            "-maxrate", "8000k", "-bufsize", "16000k",
            "-vf", "scale=trunc(iw/2)*2:1080",
            "-r", "30",  # ✅ Reduce FPS for lower CPU usage
            "-c:a", "aac", "-b:a", "192k",  # ✅ Lower audio bitrate
            mp4_path
        ]

        logger.info(f"🔹 Running FFmpeg: {' '.join(ffmpeg_command)}")

        # Run FFmpeg in a stable way (Prevent Broken Pipe errors)
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"❌ FFmpeg Error: {stderr}")
            return {"status": "error", "message": f"FFmpeg failed: {stderr}"}

        logger.info(f"✅ Video converted successfully: {mp4_path}")

        # Upload to Google Drive
        logger.info(f"📤 Uploading {mp4_path} to Google Drive...")
        file_metadata = {"name": file_name, "parents": [FOLDER_ID]}
        media = MediaFileUpload(mp4_path, mimetype="video/mp4")

        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()

        file_id = uploaded_file.get("id")
        file_link = f"https://drive.google.com/file/d/{file_id}/view"

        # 🔹 Share the file with your Gmail
        user_email = "arjunajith440@gmail.com"
        permission = {"type": "user", "role": "reader", "emailAddress": user_email}
        drive_service.permissions().create(fileId=file_id, body=permission).execute()

        logger.info(f"✅ File uploaded successfully: {file_link}")

        # 🔹 Clean up local files after successful upload
        try:
            os.remove(file_path)
            os.remove(mp4_path)
            logger.info("🗑️ Temporary files deleted.")
        except Exception as e:
            logger.warning(f"⚠️ Error deleting files: {str(e)}")

        return {"status": "success", "file_link": file_link}

    except Exception as e:
        logger.error(f"❌ Error processing video: {str(e)}")
        return {"status": "error", "message": str(e)}
