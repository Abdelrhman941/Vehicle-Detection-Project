# 🚀 Quick Start Guide

Get the Vehicle Detection System running in 3 minutes!

## ⚡ Fast Setup

### 1️⃣ Install Dependencies (First Time Only)

**Windows:**
```bash
# Open PowerShell or Command Prompt
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ Start Server

**Windows:**
```bash
.\run.bat
```

**Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

### 3️⃣ Open Browser
Navigate to: **http://localhost:8000**

---

## 📹 Process Your First Video

1. **Click "Get Started"**
2. **Drag & drop** a video file (or click to browse)
3. **Click "Process Video"**
4. **Watch progress** - real-time circular indicator
5. **Download** when complete!

---

## 🎨 What You'll See

### Road-Themed Interface
- **Black background** (asphalt)
- **Yellow accents** (road markings)
- **White text** (road paint)
- **Animated progress** (smooth transitions)

### Features
- ✅ Real-time progress updates
- ✅ Drag & drop upload
- ✅ Vehicle counting per lane
- ✅ Traffic intensity analysis
- ✅ Professional dark theme

---

## 🛠️ Troubleshooting Quick Fixes

### Server won't start?
```bash
# Make sure venv is activated
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

### Port already in use?
```bash
# Change port in run.bat/run.sh
# Replace 8000 with another port like 5000
```

### Model not found?
```
Ensure: runs/detect/train/weights/best.pt exists
```

---

## 📖 Full Documentation
See **README.md** for:
- Complete API documentation
- Configuration options
- Advanced features
- Performance tuning

---

**Built with YOLOv8, FastAPI & Modern Web Tech** 🛣️✨
