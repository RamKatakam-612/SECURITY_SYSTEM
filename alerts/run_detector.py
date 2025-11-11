from .services.detector import run_detection_core

def run_detection(video_path):
    print("⚙️  Running detector on:", video_path)
    run_detection_core(video_path)