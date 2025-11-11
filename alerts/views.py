from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

import os, cv2, base64, json, threading
import numpy as np

from .models import Alert
from .serializers import AlertSerializer
from .services.detector import run_detection
from django.utils.decorators import method_decorator


# ===========================
# ✅ HOME PAGE
# ===========================
def home_page(request):
    return render(request, "alerts/home.html")


# ===========================
# ✅ UPLOAD PAGE (UI)
# ===========================
def upload_video_page(request):
    return render(request, "alerts/upload_video.html")


# ===========================
# ✅ VIEW ALERTS (UI)
# ===========================
def show_alerts_page(request):
    alerts = Alert.objects.order_by("-created_at")
    return render(request, "alerts/alerts_list.html", {"alerts": alerts})



# ===========================
# ✅ GET ALERTS (API)
# ===========================
@api_view(["GET"])
def list_alerts(request):
    alerts = Alert.objects.order_by("-created_at")
    serializer = AlertSerializer(alerts, many=True)
    return Response(serializer.data)


# ===========================
# ✅ STORE ALERT FROM DETECTOR
# ===========================
@method_decorator(csrf_exempt, name="dispatch")
class AlertUploadView(APIView):
    def post(self, request):
        serializer = AlertSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Alert stored"}, status=201)
        return Response(serializer.errors, status=400)


# ===========================
# ✅ UPLOAD VIDEO + RETURN FIRST FRAME
# ===========================
@csrf_exempt
def video_upload_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    video = request.FILES.get("video")
    if not video:
        return JsonResponse({"error": "No video file provided"}, status=400)

    # Save video
    video_folder = os.path.join(settings.MEDIA_ROOT, "videos")
    os.makedirs(video_folder, exist_ok=True)
    video_path = os.path.join(video_folder, video.name)

    with open(video_path, "wb") as out:
        for chunk in video.chunks():
            out.write(chunk)

    # Read first frame
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return JsonResponse({"error": "Could not read frame"}, status=400)

    h, w = frame.shape[:2]
    _, buf = cv2.imencode(".jpg", frame)
    frame_b64 = base64.b64encode(buf).decode("utf-8")

    return JsonResponse({
        "video_path": video_path,
        "frame": frame_b64,
        "frame_width": w,
        "frame_height": h
    })


# ===========================
# ✅ SET ROI + START DETECTION
# ===========================
@csrf_exempt
def set_roi_view(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
    except:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    use_webcam = data.get("use_webcam", False)
    roi = data.get("roi")

    # ✅ ROI array → polygon
    polygon = None
    if roi:
        try:
            polygon = np.array(roi, dtype=np.int32).reshape((-1, 1, 2))
        except:
            return JsonResponse({"error": "ROI malformed"}, status=400)

    # ✅ WEBCAM MODE
    if use_webcam:
        threading.Thread(
            target=run_detection,
            args=(0, polygon),
            daemon=True
        ).start()

        return JsonResponse({"status": "Webcam detection started"}, status=200)

    # ✅ VIDEO MODE
    video_path = data.get("video_path")
    if not video_path:
        return JsonResponse({"error": "Missing video_path"}, status=400)

    if roi is None:
        return JsonResponse({"error": "ROI missing"}, status=400)

    threading.Thread(
        target=run_detection,
        args=(video_path, polygon),
        daemon=True
    ).start()

    return JsonResponse({"status": "Video detection started"}, status=200)



@csrf_exempt
def webcam_frame_view(request):

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return JsonResponse({"error": "Cannot read webcam"}, status=400)

    h, w = frame.shape[:2]
    _, buf = cv2.imencode(".jpg", frame)
    frame_b64 = base64.b64encode(buf).decode("utf-8")

    return JsonResponse({
        "frame": frame_b64,
        "frame_width": w,
        "frame_height": h
    })

@csrf_exempt
def webcam_first_frame(request):
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return JsonResponse({"error": "Cannot capture webcam"}, status=400)

    h, w = frame.shape[:2]
    _, buffer = cv2.imencode(".jpg", frame)
    b64 = base64.b64encode(buffer).decode("utf-8")

    return JsonResponse({
        "frame": b64,
        "frame_width": w,
        "frame_height": h
    })

