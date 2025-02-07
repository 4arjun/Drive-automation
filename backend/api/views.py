import os


from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from .tasks import process_and_upload_video

UPLOAD_FOLDER = "uploads/"  

@api_view(["POST"])
def upload_video(request):
    try:
        file = request.FILES["video"]
        file_name = file.name
        file_path = os.path.join(UPLOAD_FOLDER, file.name)

        with default_storage.open(file_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        process_and_upload_video.delay(file_path, file_name)

        return Response({"message": "Upload started! Your video is being processed in the background."})

    except Exception as e:
        return Response({"error": str(e)}, status=500)
