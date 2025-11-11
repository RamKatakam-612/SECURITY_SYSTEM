import cv2
import numpy as np
from ultralytics import YOLO
from norfair import Detection, Tracker
import time
import threading
import winsound
import requests
from twilio.rest import Client
import os

# from twilio.rest import Client   # optional

CONF_THRESHOLD = 0.35
DISTANCE_THRESHOLD = 80
SKIP_N = 10
LOITER_THRESHOLD = 3
COOLDOWN_TIME = 10

DJANGO_SERVER_URL = "http://127.0.0.1:8000/api/alerts/upload/"

model = YOLO("yolov8n.pt")

def euclidean_distance(det, trk):
    det_pt = det.points[0].astype(float)
    trk_pt = trk.estimate[0].astype(float)
    return np.linalg.norm(det_pt - trk_pt)

def bbox_to_center(b):
    x1, y1, x2, y2 = b
    return np.array([[(x1 + x2) / 2.0, (y1 + y2) / 2.0]])

def inside_roi(point, polygon):
    return cv2.pointPolygonTest(polygon, (int(point[0]), int(point[1])), False) >= 0

def play_sound():
    path = os.path.join(os.path.dirname(__file__), "siren.wav")
    winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)

def play_siren():
    threading.Thread(target=play_sound).start()

def send_twilio_message(duration):
    print('🚨 ALERT: Some one arrived and person loitering for {int(duration)}sec!')
    #print(f"[Twilio] would send: stayed {int(duration)} seconds")
    #client = Client("ACxxxxxxxxxxxxxxxx","xxxxxxxxxxxxx")
    #msg = f"🚨 ALERT: Some one arrived and person loitering for {int(duration)}sec!"
    #client.messages.create(body=msg, from_="+16502430443", to="+919154715354")

def send_alert_to_backend(track_id, duration, frame):
    try:
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            print("[Django] Could not encode snapshot")
            return
        files = {"image": ("alert.jpg", encoded.tobytes(), "image/jpeg")}
        data = {"track_id": track_id, "duration": duration}
        r = requests.post(DJANGO_SERVER_URL, data=data, files=files, timeout=5)
        if r.status_code == 201:
            print(f"[✅ Django] Logged ID={track_id} time={duration:.1f}s")
        else:
            print(f"[⚠ Django] Status={r.status_code} → {r.text[:120]}")
    except Exception as e:
        print("[❌ Django error]:", e)

tracker = Tracker(distance_function=euclidean_distance, distance_threshold=DISTANCE_THRESHOLD)

def run_detection(video_path, ROI_polygon=None):
    """
    video_path: "__WEBCAM__" to use camera 0, or an absolute path to a video file
    roi_points: list[[x,y],...] in ORIGINAL video resolution. If None → full-frame ROI.
    """
    use_webcam = (video_path == "__WEBCAM__")
    cap = cv2.VideoCapture(0 if use_webcam else video_path)
    if not cap.isOpened():
        print("❌ Unable to open video source:", video_path)
        return

    print("🎥 Starting detection on:", "Webcam(0)" if use_webcam else video_path)

    frame_count = 0
    entry_times = {}        # {track_id: first_time_in_roi}
    alert_cooldown = {}     # {track_id: last_alert_time}

    last_boxes = []
    last_confs = []
    last_tracked = []

    # Build ROI polygon once we know frame size
    ret, first = cap.read()
    if not ret:
        print("❌ Could not read first frame")
        cap.release(); return
    H, W = first.shape[:2]

    if ROI_polygon is None:
        ROI_polygon = np.array([[0,0],[W,0],[W,H],[0,H]], np.int32).reshape((-1,1,2))
    else:
        ROI_polygon = ROI_polygon.reshape((-1,1,2))     # ✅ NO SCALING


    # rewind for processing from the beginning if video
    if not use_webcam:
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Run YOLO every SKIP_N frames
        if frame_count % SKIP_N == 0:
            results = model(frame, conf=CONF_THRESHOLD, verbose=False)[0]

            if hasattr(results, "boxes") and len(results.boxes) > 0:
                boxes = results.boxes.xyxy.cpu().numpy()
                confs = results.boxes.conf.cpu().numpy()
                classes = results.boxes.cls.cpu().numpy().astype(int)
            else:
                boxes, confs, classes = [], [], []

            person_boxes, person_confs = [], []
            for b, c, cl in zip(boxes, confs, classes):
                if cl == 0 and c >= CONF_THRESHOLD:
                    x1, y1, x2, y2 = map(int, b)
                    person_boxes.append([x1, y1, x2, y2])
                    person_confs.append(float(c))

            detections = [
                Detection(points=bbox_to_center(b).astype(float), scores=np.array([c]))
                for b, c in zip(person_boxes, person_confs)
            ]

            tracked = tracker.update(detections=detections)
            last_tracked, last_boxes, last_confs = tracked, person_boxes, person_confs
        else:
            tracked, person_boxes, person_confs = last_tracked, last_boxes, last_confs

        cv2.polylines(frame, [ROI_polygon], True, (255, 0, 0), 2)

        centers = np.array([bbox_to_center(b).flatten() for b in person_boxes]) if len(person_boxes) else np.zeros((0, 2))

        for obj in tracked:
            tid = obj.id
            center = obj.estimate[0]
            color = (0, 255, 0)  # default

            if len(centers) > 0:
                d = np.linalg.norm(centers - center, axis=1)
                idx = int(np.argmin(d))

                if d[idx] < DISTANCE_THRESHOLD:
                    x1, y1, x2, y2 = person_boxes[idx]
                    conf = person_confs[idx]

                    if inside_roi(center, ROI_polygon):
                        if tid not in entry_times:
                            entry_times[tid] = time.time()

                        duration = time.time() - entry_times[tid]
                        now = time.time()
                        last_alert = alert_cooldown.get(tid, 0)

                        # show duration always
                        cv2.putText(frame, f"{int(duration)}s", (x1, y1 - 8),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

                        if duration > LOITER_THRESHOLD:
                            if now - last_alert > COOLDOWN_TIME:
                                #threading.Thread(target=send_twilio_message, args=(duration,), daemon=True).start()
                                threading.Thread(target=send_alert_to_backend, args=(tid, duration, frame.copy()), daemon=True).start()
                                alert_cooldown[tid] = now
                                play_siren()

                            cv2.putText(frame, f"ALERT! {int(duration)}s", (x1, y1 - 32),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            color = (0, 0, 255)
                        else:
                            color = (0, 255, 0)
                    else:
                        entry_times.pop(tid, None)
                        color = (0, 255, 0)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, f"ID {tid} {conf:.2f}", (x1, y1 - 48),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("YOLO + Norfair + Loitering", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("✅ Detection finished")