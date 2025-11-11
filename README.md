# Security_System
A complete security system project with video processing using openCV and optional web interface usign Django.
---
```
## 📁 Project Structure (top levels)

Security_System/
├── alerts/
│ ├── migrations/
│ ├── services/
│ │ ├── detector.py
│ │ ├── sample.py
│ │ ├── yolov8n.pt # (ignored)
│ ├── templates/
│ │ └── alerts/
│ ├── static/
│ │ └── alerts/
│ ├── models.py
│ ├── run_detector.py
│ ├── serializers.py
│ ├── urls.py
│ └── views.py
│
├── security_system/ # Django core configuration
│ ├── settings.py
│ ├── urls.py
│ ├── wsgi.py
│ └── asgi.py
│
├── snapshots/ # Auto-saved alert images
│ └── alerts/
│ └── alert_xxx.jpg # (many files - ignored)
│
├── manage.py
├── requirements.txt
├── README.md
└── .gitignore
```
## 🚀 Key Technologies (detected)
- Django, OpenCV (cv2), NumPy, Django REST Framework, Requests

## 🧰 Prerequisites
- Python 3.9+
- pip and virtualenv
- System deps for OpenCV (Linux/macOS may need extra packages)
- If using MySQL/PostgreSQL, install server/client libs

## 🔧 Setup (Local)
```bash
# 1) Clone your repo
git clone <your-repo-url>.git
cd Security_System

# 2) Create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

# 3) Install Python dependencies
pip install -r requirements.txt

# 4) (Optional) Copy env template and fill secrets
cp .env.example .env  # if present
```

## 🗄️ Django Setup
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

## ▶️ Running the App
- Entry commands:
  - python manage.py migrate
  - python manage.py createsuperuser
  - python manage.py runserver 0.0.0.0:8000

## ⚙️ Configuration
- Environment variables via `.env` or OS env.
- Common settings:
  - DEBUG (Django)
  - DATABASE_URL or DATABASES in settings.py
  - MEDIA/STATIC paths
  - Video source index (e.g., 0 for default webcam)
- Windows-only alerts use `winsound`; consider cross-platform alternatives for Linux/macOS.

## 🧱 Architecture & Flow (high level)
- **Capture/Input:** Webcam or video file via OpenCV (`cv2.VideoCapture`).
- **Processing:** Frame-wise analysis (motion/person detection logic).
- **Alerts/Logging:** Trigger siren/logs when events fire (e.g., `winsound`).
- **Web UI (Django):** Requests → URLs → Views → Templates; Models → DB; optional DRF for APIs.

> Update this section with your specific detectors, thresholds, and endpoints.

## 🧪 Testing
```bash
pytest -q  # if tests are present
```

## 🐳 Docker (optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

## 📦 Deployment Notes
- `python manage.py collectstatic` before deploy.
- Use a production server (e.g., gunicorn + reverse proxy). Set `DEBUG=False` and secure secrets.

## 🙌 Contributing
1. Fork & branch
2. Commit with clear messages
3. Open a PR with description and screenshots/gifs


