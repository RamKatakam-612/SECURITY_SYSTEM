from django.urls import path
from .views import (
    home_page,
    upload_video_page,
    video_upload_view,
    set_roi_view,
    show_alerts_page,
    list_alerts,
    AlertUploadView,
    webcam_frame_view,
    webcam_first_frame
)

urlpatterns = [
    path('', home_page),

    # UI
    path('upload-page/', upload_video_page),
    path('alerts/', show_alerts_page),

    # API
    path('api/upload-video/', video_upload_view),
    path('api/set-roi/', set_roi_view),
    path('api/alerts/', list_alerts),

    # ✅ This must match detector POST URL
    path('api/alerts/upload/', AlertUploadView.as_view()),
    path("api/webcam-frame/", webcam_frame_view),
    path("api/webcam-frame/", webcam_first_frame),

  
]
