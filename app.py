"""
FastAPI Backend for Vehicle Detection Web Application
"""
import warnings
warnings.filterwarnings('ignore')

import os
import cv2
import json
import numpy as np
from ultralytics import YOLO
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pathlib import Path
import asyncio
from typing import Optional
from collections import deque

# Initialize FastAPI app
app = FastAPI(title="Vehicle Detection System")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create necessary directories
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
STATIC_DIR = Path("static")

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# WebSocket connections
active_connections: deque = deque()

# Global variables for processing
processing_status = {
    "is_processing": False,
    "progress": 0,
    "current_file": None,
    "error": None,
    "total_frames": 0,
    "processed_frames": 0
}

# Processing configuration
HEAVY_TRAFFIC_THRESHOLD = 10
VERTICES_LEFT = np.array([(465, 350), (609, 350), (510, 630), (2, 630)], dtype=np.int32)
VERTICES_RIGHT = np.array([(678, 350), (815, 350), (1203, 630), (743, 630)], dtype=np.int32)
X1, X2 = 325, 635
LANE_THRESHOLD = 609

# Load YOLO model
try:
    post_training_files_path = r'runs\detect\train'
    best_model_path = os.path.join(post_training_files_path, 'weights/best.pt')
    if not os.path.exists(best_model_path):
        raise FileNotFoundError(f"Model not found at {best_model_path}")
    model = YOLO(best_model_path)
    print("✓ Model loaded successfully")
except Exception as e:
    print(f"✗ Error loading model: {e}")
    model = None


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates"""
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive and send progress updates
            await asyncio.sleep(0.5)
            if processing_status["is_processing"]:
                await websocket.send_json({
                    "progress": processing_status["progress"],
                    "processed_frames": processing_status["processed_frames"],
                    "total_frames": processing_status["total_frames"],
                    "is_processing": True
                })
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        active_connections.remove(websocket)


async def broadcast_progress(data: dict):
    """Broadcast progress to all connected WebSocket clients"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(data)
        except:
            disconnected.append(connection)

    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


@app.get("/api/video/{filename}")
async def stream_video(filename: str):
    """Serve video file with proper headers for browser compatibility"""
    file_path = OUTPUT_DIR / filename

    # Try MP4 first, then AVI as fallback
    if not file_path.exists():
        # Try AVI version if MP4 doesn't exist
        if filename.endswith('.mp4'):
            avi_path = OUTPUT_DIR / filename.replace('.mp4', '.avi')
            if avi_path.exists():
                file_path = avi_path
                filename = filename.replace('.mp4', '.avi')

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Video not found: {filename}")

    # Determine media type
    media_type = "video/mp4" if filename.endswith('.mp4') else "video/x-msvideo"

    # Use FileResponse for proper range request support (required for video seeking)
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename
    )
@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("static/index.html")


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


@app.get("/api/status")
async def get_status():
    """Get current processing status"""
    return processing_status


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload video file for processing"""
    global processing_status

    # Validate file type
    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov')):
        raise HTTPException(status_code=400, detail="Invalid file type. Only MP4, AVI, and MOV are supported.")

    # Check if already processing
    if processing_status["is_processing"]:
        raise HTTPException(status_code=409, detail="Another video is currently being processed.")

    # Save uploaded file
    file_path = UPLOAD_DIR / file.filename
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    processing_status["current_file"] = file.filename

    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "path": str(file_path)
    }


@app.post("/api/process/{filename}")
async def process_video(filename: str):
    """Process the uploaded video"""
    global processing_status

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    if processing_status["is_processing"]:
        raise HTTPException(status_code=409, detail="Another video is currently being processed.")

    input_path = UPLOAD_DIR / filename
    if not input_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Start processing in background
    asyncio.create_task(process_video_task(str(input_path), filename))

    return {"message": "Processing started", "filename": filename}


async def process_video_task(input_path: str, filename: str):
    """Background task to process video with real-time progress"""
    global processing_status

    processing_status["is_processing"] = True
    processing_status["progress"] = 0
    processing_status["error"] = None
    processing_status["processed_frames"] = 0
    processing_status["total_frames"] = 0

    try:
        # Generate output filename
        output_basename = Path(filename).stem + "_processed"
        output_mp4 = OUTPUT_DIR / f"{output_basename}.mp4"

        # Open video and get total frames
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        processing_status["total_frames"] = total_frames

        # Setup video writer - write directly to MP4
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(str(output_mp4), fourcc, fps, (width, height))        # Text settings
        text_position_left_lane = (10, 50)
        text_position_right_lane = (820, 50)
        intensity_position_left_lane = (10, 100)
        intensity_position_right_lane = (820, 100)
        font = cv2.FONT_HERSHEY_COMPLEX
        font_scale = 1
        font_color = (255, 255, 255)
        background_color = (0, 0, 255)

        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Update progress
            frame_count += 1
            processing_status["processed_frames"] = frame_count
            processing_status["progress"] = int((frame_count / total_frames) * 100)

            # Broadcast progress every 10 frames to avoid overwhelming the client
            if frame_count % 10 == 0:
                await broadcast_progress({
                    "progress": processing_status["progress"],
                    "processed_frames": frame_count,
                    "total_frames": total_frames,
                    "is_processing": True
                })

            # Create detection frame
            detection_frame = frame.copy()
            detection_frame[:X1, :] = 0
            detection_frame[X2:, :] = 0

            # Perform detection
            results = model.predict(detection_frame, imgsz=640, conf=0.4, verbose=False)
            processed_frame = results[0].plot(line_width=1)

            # Restore original regions
            processed_frame[:X1, :] = frame[:X1, :].copy()
            processed_frame[X2:, :] = frame[X2:, :].copy()

            # Draw ROI
            cv2.polylines(processed_frame, [VERTICES_LEFT], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.polylines(processed_frame, [VERTICES_RIGHT], isClosed=True, color=(255, 0, 0), thickness=2)

            # Count vehicles
            vehicles_in_left_lane = 0
            vehicles_in_right_lane = 0
            for box in results[0].boxes.xyxy:
                if box[0] < LANE_THRESHOLD:
                    vehicles_in_left_lane += 1
                else:
                    vehicles_in_right_lane += 1

            # Determine traffic intensity
            traffic_intensity_left = "Heavy" if vehicles_in_left_lane > HEAVY_TRAFFIC_THRESHOLD else "Smooth"
            traffic_intensity_right = "Heavy" if vehicles_in_right_lane > HEAVY_TRAFFIC_THRESHOLD else "Smooth"

            # Draw background rectangles
            cv2.rectangle(processed_frame, (text_position_left_lane[0]-10, text_position_left_lane[1] - 25),
                         (text_position_left_lane[0] + 460, text_position_left_lane[1] + 10), background_color, -1)
            cv2.rectangle(processed_frame, (intensity_position_left_lane[0]-10, intensity_position_left_lane[1] - 25),
                         (intensity_position_left_lane[0] + 460, intensity_position_left_lane[1] + 10), background_color, -1)
            cv2.rectangle(processed_frame, (text_position_right_lane[0]-10, text_position_right_lane[1] - 25),
                         (text_position_right_lane[0] + 460, text_position_right_lane[1] + 10), background_color, -1)
            cv2.rectangle(processed_frame, (intensity_position_right_lane[0]-10, intensity_position_right_lane[1] - 25),
                         (intensity_position_right_lane[0] + 460, intensity_position_right_lane[1] + 10), background_color, -1)

            # Add text annotations
            cv2.putText(processed_frame, f'Vehicles in Left Lane: {vehicles_in_left_lane}', text_position_left_lane,
                       font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(processed_frame, f'Traffic Intensity: {traffic_intensity_left}', intensity_position_left_lane,
                       font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(processed_frame, f'Vehicles in Right Lane: {vehicles_in_right_lane}', text_position_right_lane,
                       font, font_scale, font_color, 2, cv2.LINE_AA)
            cv2.putText(processed_frame, f'Traffic Intensity: {traffic_intensity_right}', intensity_position_right_lane,
                       font, font_scale, font_color, 2, cv2.LINE_AA)

            out.write(processed_frame)

        cap.release()
        out.release()

        # Verify the file was created
        if not output_mp4.exists():
            raise Exception("Failed to create output video file")

        processing_status["progress"] = 100
        processing_status["output_file"] = f"{output_basename}.mp4"        # Send final progress
        await broadcast_progress({
            "progress": 100,
            "processed_frames": total_frames,
            "total_frames": total_frames,
            "is_processing": False,
            "output_file": f"{output_basename}.mp4"
        })

    except Exception as e:
        processing_status["error"] = str(e)
        await broadcast_progress({
            "error": str(e),
            "is_processing": False
        })
        print(f"Error processing video: {e}")
    finally:
        processing_status["is_processing"] = False
@app.get("/api/download/{filename}")
async def download_video(filename: str):
    """Download processed video"""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="video/mp4"
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
