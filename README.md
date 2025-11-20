# **Vehicle Detection System 🚗**

A real-time vehicle detection and traffic analysis web application powered by YOLOv8, FastAPI, and modern web technologies. Features a sleek road-themed dark interface with live WebSocket progress updates.

![Road Theme](https://img.shields.io/badge/Theme-Road%20Inspired-FFD700?style=for-the-badge) ![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python) ![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?style=for-the-badge&logo=fastapi) ![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00FFFF?style=for-the-badge)

<body>
    <div style = "
        width: 100%;
        height: 30px;
        background: linear-gradient(to right,rgba(70, 152, 155, 1),rgba(72, 187, 139, 1));">
    </div>
</body>

<p align="center">
  <a href="https://www.youtube.com/watch?v=f_7gi9ArWt0" target="_blank">
    <img src="https://img.youtube.com/vi/f_7gi9ArWt0/0.jpg" 
         alt="Vehicle Detection Demo" 
         style="width:70%; border-radius:10px;">
  </a>
</p>

<p align="center">
  <strong>▶ Watch the Demo Video</strong>
</p>


## **📁 Project Structure**
```
project/
├── app.py                          # FastAPI backend application
├── requirements.txt                # Python dependencies
├── run.bat                         # Windows launch script
├── run.sh                          # Linux/Mac launch script
├── Code.ipynb                      # Notebook for demo and testing
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
│
├── static/                         # Frontend files
│   ├── index.html                  # Main HTML page
│   ├── style.css                   # Road-themed styles
│   └── script.js                   # Frontend logic & WebSocket
│
├── uploads/                        # Uploaded videos (temporary)
│   └── .gitkeep
│
├── outputs/                        # Processed videos
│   ├── .gitkeep
│   └── *_processed.avi             # Output files
│
├── runs/                           # YOLO model directory
│   └── detect/
│       ├── train/
│       │   └── weights/
│       │       └── best.pt         # Trained model weights
│       └── val/
│
├── Dataset/                        # Training dataset
│   ├── data.yaml                   # Dataset configuration
│   ├── video/                      # saomple videos for training
│   ├── train/                      # Training images & labels
│   └── valid/                      # Validation images & labels
│
├── demo/                           # Demo notebooks
│   └── Vertices Extraction.ipynb
│
└── docs/                           # Documentation
    ├── Vehicle Detection Project.pptx
    └── Proposal.docx
```
<body>
    <div style = "
        width: 100%;
        height: 30px;
        background: linear-gradient(to right,rgba(70, 152, 155, 1),rgba(72, 187, 139, 1));">
    </div>
</body>

## **> Installation Guide**

### Step 1: Clone or Download
```bash
# Option A: Clone with Git
git clone <repository-url>
cd <repository-folder>
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Note:** Installation may take 5-10 minutes due to PyTorch and dependencies.

### Step 4: Verify Model Files
Ensure your trained YOLO model exists at:
```
runs/detect/train/weights/best.pt
```

If missing, you'll need to:
1. Train your own YOLOv8 model, or
2. Place a pre-trained model at this path

<body>
    <div style = "
        width: 100%;
        height: 30px;
        background: linear-gradient(to right,rgba(70, 152, 155, 1),rgba(72, 187, 139, 1));">
    </div>
</body>

## **> Usage**

### Quick Start (Recommended)

#### Windows
```bash
.\run.bat
```

#### Linux/Mac
```bash
chmod +x run.sh
./run.sh
```

### Manual Start
```bash
# Activate virtual environment first
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Start server
python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Access the Application
1. Open your browser
2. Navigate to: **http://localhost:8000**
3. You should see the Vehicle Detection System interface

### Supported Formats
- **Input**: MP4, AVI, MOV (H.264, MPEG-4, etc.)
- **Output**: AVI (XVID codec for maximum compatibility)
- **Max File Size**: 500 MB (configurable)
- **Resolution**: Any (will be preserved)

## **⚙️ Configuration**

### Server Settings
Edit `run.bat` or `run.sh`:

```bash
# Change port (default: 8000)
uvicorn app:app --host 0.0.0.0 --port 5000

# Disable auto-reload (production)
uvicorn app:app --host 0.0.0.0 --port 8000

# Workers (multi-process)
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### UI Theme
Edit `static/style.css` CSS variables:

```css
:root {
    --accent-primary: #ffd700;     /* Yellow */
    --bg-primary: #0a0a0a;         /* Black */
    --text-primary: #ffffff;       /* White */
    /* ... more variables ... */
}
```

<body>
    <div style = "
        width: 100%;
        height: 30px;
        background: linear-gradient(to right,rgba(70, 152, 155, 1),rgba(72, 187, 139, 1));">
    </div>
</body>

## **> How It Works**

### Video Processing Pipeline

1. **Upload Phase**
   - User selects video via drag-and-drop or file picker
   - Frontend validates file (type, size)
   - File uploaded to `/api/upload` endpoint
   - Server saves to `uploads/` directory

2. **Processing Phase**
   - User clicks "Process Video"
   - Backend creates async task
   - WebSocket connection established
   - Video opened with OpenCV

3. **Frame-by-Frame Analysis**
   ```
   For each frame:
   ├── Apply ROI mask (focus on road area)
   ├── Run YOLOv8 detection
   ├── Filter detections by confidence
   ├── Count vehicles per lane (left/right of threshold)
   ├── Draw bounding boxes, labels, counts
   ├── Update progress (every 10 frames via WebSocket)
   └── Write annotated frame to output video
   ```

4. **Traffic Classification**
   - Count total vehicles in final frame
   - If count >= 10: "Heavy Traffic" (Red)
   - If count < 10: "Smooth Traffic" (Green)
   - Display on video overlay

5. **Output Phase**
   - Save processed video as `{filename}_processed.avi`
   - Send completion message via WebSocket
   - Frontend displays download button

### Lane Detection Logic
```python
# Pseudo-code
for detection in yolo_results:
    center_x = (detection.x1 + detection.x2) / 2

    if center_x < LANE_THRESHOLD:
        left_lane_count += 1
    else:
        right_lane_count += 1
```

### ROI (Region of Interest)
- Defined as polygon vertices
- Masks non-road areas (sky, buildings, etc.)
- Improves accuracy by focusing on relevant region
- Customizable for different camera angles

<body>
    <div style = "
        width: 100%;
        height: 30px;
        background: linear-gradient(to right,rgba(70, 152, 155, 1),rgba(72, 187, 139, 1));">
    </div>
</body>

## **🐛 Troubleshooting**

#### 1. Server Won't Start
**Error:** `ModuleNotFoundError: No module named 'uvicorn'`

**Solution:**
```bash
# Ensure virtual environment is activated
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Reinstall dependencies
pip install -r requirements.txt
```

---

#### 2. Model Not Found
**Error:** `FileNotFoundError: runs/detect/train/weights/best.pt`

**Solution:**
- Train your own model using YOLOv8
- Or place a pre-trained model at the specified path
- Update path in `app.py` if model is elsewhere

---

#### 3. Video Won't Play
**Problem:** Download button works but video won't play in browser

**Solution:**
- Videos are saved as AVI (best compatibility)
- Use VLC or Windows Media Player to view
- For web playback, convert to H.264 MP4:
```bash
ffmpeg -i output.avi -c:v libx264 output.mp4
```

---

#### 4. Port Already in Use
**Error:** `Address already in use`

**Solution:**
```bash
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9

# Or change port in run script
```

<div style="background-color: black; color:rgb(163, 52, 52); width: 100%; height: 50px; text-align: center; font-weight: bold; line-height: 50px; margin: 10px 0; font-size: 50px;">
Thanks 🫡
</div>
