# ⚡ Iron Sight | AI Virtual Spotter

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)
![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-magenta?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Frontend-Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)
![Status](https://img.shields.io/badge/Status-Live-yellow?style=for-the-badge)

> **\"Your personal AI spotter that never blinks.\"**

**Iron Sight** is a real-time **Computer Vision powered AI Personal Trainer**.  
Using **YOLOv8 Pose Estimation**, it analyzes gym movements at **30 FPS**, counts reps, and delivers **instant visual + textual feedback** to improve form, reduce injury risk, and maximize gains.

---

## 🎬 Live Demo

![Demo Preview](assets/demo.gif)

*AI detecting squats, tracking depth, and counting reps in real time.*

---

## 🚀 Key Features

### 🧠 Intelligent Form Correction
Iron Sight doesn’t just detect movement, it **understands biomechanics**.

- **Squats**
  - Tracks hip depth & torso angle
  - Alerts **“CHEST UP!”** if torso lean exceeds **50°**
- **Bicep Curls**
  - Detects elbow drift
  - Warns **“LOCK ELBOWS”** when cheating is detected

---

### ⚡ Volt Visual Feedback System
Designed to feel **alive, reactive, and motivating**.

- **Dynamic Skeleton Overlay**
  - 🟡 Yellow → tracking  
  - 🟢 Green → perfect rep
- **Rep Flash Effect**
  - Full-screen “Volt pulse” when a rep is completed
- **Live Telemetry Graph**
  - Frame-by-frame joint angle tracking for deep analysis

---

### 🛡️ Crash-Proof Architecture
Built on **FastAPI WebSockets** with fault tolerance:
- Auto-recovers from corrupted video frames
- Handles dropped connections gracefully
- No session crashes mid-workout

---

## 🛠️ Tech Stack

| Component | Technology | Description |
|--------|-----------|-------------|
| **Core AI** | Ultralytics YOLOv8 | Pose Estimation (`yolov8n-pose`) |
| **Backend** | Python, FastAPI | High-performance WebSocket server |
| **CV Engine** | OpenCV, NumPy | Image processing & vector math |
| **Frontend** | HTML5, JavaScript | Real-time UI & WebSocket client |
| **Styling** | Tailwind CSS | Modern cyber / gym aesthetic |
| **Charts** | Chart.js | Real-time angle telemetry |

---

## 📦 Installation & Setup

### ✅ Prerequisites
- Python **3.8+**
- Webcam (for live mode)

---

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Ahadasim08/AI-Gym-Trainer.git
cd AI-Gym-Trainer
```

---

### 2️⃣ Backend Setup
Navigate to the backend folder and install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

---

### 3️⃣ Run the AI Brain 🧠
Start the FastAPI server:
```bash
uvicorn main:app --reload
```

On first run, YOLOv8 weights will download automatically.

You should see:
```
✅ Model Loaded!
✅ Application startup complete.
```

---

### 4️⃣ Launch the UI 💻
No frontend server required.

- Open `frontend/index.html` directly in **Chrome / Edge**
- **Upload Video** → Test with recorded gym clips
- **Live Cam** → Click **Start Live Cam** for real-time tracking

---

## 📂 Project Structure

```plaintext
AI-Gym-Trainer/
│
├── backend/                # 🐍 Python server & AI logic
│   ├── main.py             # FastAPI WebSocket + Pose logic
│   ├── yolov8n-pose.pt     # Model weights (auto-downloaded)
│   └── requirements.txt
│
├── frontend/               # 💻 Web interface
│   ├── index.html          # Dashboard UI
│   └── script.js           # WebSocket client & charts
```

---

---

## 🤝 Contributing

Want to add **Deadlifts**, **Bench Press**, or new metrics?

1. Fork the repository  
2. Create a feature branch  
   ```bash
   git checkout -b feature/NewExercise
   ```
3. Commit your changes  
4. Push to your branch  
5. Open a Pull Request 🚀

---


---

## 🌟 Show Your Support
If you like this project, please ⭐ star the repo — it helps a lot!
