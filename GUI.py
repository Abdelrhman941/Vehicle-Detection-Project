import warnings
warnings.filterwarnings('ignore')

import os
import cv2                              # type: ignore
import json                             # type: ignore
import numpy as np                      # type: ignore
from ultralytics import YOLO            # type: ignore
import streamlit as st                  # type: ignore
from streamlit_lottie import st_lottie  # type: ignore

#################################################################### Streamlit App ####################################################################
if 'started' not in st.session_state or not st.session_state.started:  
    st.markdown("""
    <div style="text-align: center;">
        <h1><b> 🚓Vehicle Detection Project🚓 </b></h1>
    </div>
    """, unsafe_allow_html=True)    
    #------------------------------------------
    with open("./streamlit/Animation0.json", "r") as file:
        animation_data = json.load(file)
        st_lottie(animation_data, speed=1, width=600, height=400)
    #------------------------------------------
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <style>
        @keyframes borderAnimation {
            0% { border-color: #ff0000; }
            25% { border-color: #00ff00; }
            50% { border-color: #0000ff; }
            75% { border-color: #ffff00; }
            100% { border-color: #ff00ff; }  }
        .stButton button {
            font-size: 100px !important;
            padding: 1px 10px !important;
            margin: 0px 150px !important;
            color: #ffffff !important;
            transition: all 0.1s ease !important;
            background-color: #40a7fc !important;   }
        .stButton button:hover {
            color: #fafafa !important;
            animation: borderAnimation 2s infinite !important;
            background-color: rgba(64, 167, 252, 0.5) !important;  }
        </style> """, unsafe_allow_html=True)
        
        if st.button("Start 👀", key="start_button", use_container_width=True):
            st.session_state.started = True
            st.rerun()

########################################
else:
    st.markdown("""
    <div style="text-align: center;">
        <h1><b> 🚓Vehicle Detection Project🚓 </b></h1>
    </div>
    """, unsafe_allow_html=True)
    #------------------------------------------
    st.sidebar.title("Upload and Settings")
    # Upload video
    uploaded_file = st.sidebar.file_uploader("", type=["mp4", "avi"])
    
    ###################### Set up processing variables ######################
    heavy_traffic_threshold = 10    # thr for the number of cars as heavy or smooth traffic
    vertices_left  = np.array([(465, 350), (609, 350), (510, 630), (2, 630)], dtype=np.int32)        # ROI for the left  lane
    vertices_right = np.array([(678, 350), (815, 350), (1203, 630), (743, 630)], dtype=np.int32)     # ROI for the right lane
    x1, x2 = 325, 635               # this is the top and bottom region to be hidden not interested
    lane_threshold = 609            # this is the threshold to determine the lane of the car in {left or right}
    
    ###################### Preload model ######################
    post_training_files_path = r'runs\detect\train'
    best_model_path = os.path.join(post_training_files_path, 'weights/best.pt')
    best_model = YOLO(best_model_path)
    
    ###################### Process uploaded ######################
    if uploaded_file:
        temp_file = f"temp_{uploaded_file.name}"        # Save uploaded file locally
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())          # Write the file to the filesystem, getbuffer() returns the file as bytes, why: to avoid memory leaks 
        
        st.video(temp_file)                            
        #------------------------------------------
        st.markdown("""
        <style>
        @keyframes borderAnimation {
            0% { border-color:rgb(131, 18, 18);border-width: 3px; }
            25% { border-color:rgb(49, 214, 49); border-width: 3px;}
            50% { border-color:rgb(100, 100, 102); border-width: 3px;}
            75% { border-color:rgb(221, 30, 30); border-width: 3px;}
            100% { border-color:rgb(96, 221, 243); border-width: 3px;} }
        .stButton button {
            font-size: 100px !important;
            padding: 10px 100px !important;
            margin: 0px 200px !important;
            transition: 0.3s !important;
            background-color: #40a7fc !important; }
        .stButton button:hover {
            transform: scale(1.1) !important;
            color: #130d0d   !important;
            animation: borderAnimation 5s infinite !important;  
            background-color: #cccdc8 !important;  }
        </style>""", unsafe_allow_html=True)
        #------------------------------------------
        if st.button("Start Count"):
            output_file = "traffic_density_analysis.avi"
            mp4_file    = "traffic_density_analysis.mp4"
            
            animation_placeholder = st.empty()
            
            # Check if output video already exists
            if os.path.exists(mp4_file):
                animation_placeholder.empty()
                st.write("> # video loaded successfully 🎉.")
                st.video(mp4_file)
            else:
                with open("./streamlit/Animation.json", "r") as file:
                    ###################### Open the video file and compress "fourcc XVID" ######################
                    cap    = cv2.VideoCapture(temp_file)
                    fourcc = cv2.VideoWriter_fourcc(*'XVID')        # XVID codec for AVI format, there are other codecs like H264 ,DIVX, etc.
                    out    = cv2.VideoWriter(output_file, fourcc, 20.0, (int(cap.get(3)), int(cap.get(4))))
                    ##    >> cv2.VideoWriter(filename, fourcc, fps, frameSize, isColor=None) <<    ##
                    
                    animation_data = json.load(file)
                    animation_placeholder = st.empty()
                    
                    with animation_placeholder:
                        st_lottie(animation_data, speed=1, width=600, height=400)
                    ###################### Define the positions for the text annotations on the image ######################
                    text_position_left_lane  = (10, 50)
                    text_position_right_lane = (820, 50)
                    intensity_position_left_lane  = (10, 100)
                    intensity_position_right_lane = (820, 100)
                    font = cv2.FONT_HERSHEY_COMPLEX
                    font_scale = 1
                    font_color = (255, 255, 255)    # White color for text
                    background_color = (0, 0, 255)  # Red background for text
                    ###################### Process the video ######################
                    while cap.isOpened():
                        ret, frame = cap.read()
                        if not ret:
                            break
                        detection_frame = frame.copy()
                        detection_frame[:x1, :] = 0  # Black out top region
                        detection_frame[x2:, :] = 0  # Black out bottom region
                        ###################### Perform object detection & predict ######################
                        results = best_model.predict(detection_frame, imgsz=640, conf=0.4)
                        processed_frame = results[0].plot(line_width=1)
                        
                        # Restore original top and bottom parts : to display the region of interest
                        processed_frame[:x1, :] = frame[:x1, :].copy()
                        processed_frame[x2:, :] = frame[x2:, :].copy()
                        ###################### Draw ROI ######################
                        cv2.polylines(processed_frame, [vertices_left], isClosed=True, color=(0, 255, 0), thickness=2)
                        cv2.polylines(processed_frame, [vertices_right], isClosed=True, color=(255, 0, 0), thickness=2)
                        bounding_boxes = results[0].boxes
                        ###################### Count vehicles ######################
                        vehicles_in_left_lane  = 0
                        vehicles_in_right_lane = 0
                        for box in results[0].boxes.xyxy:
                            if box[0] < lane_threshold:
                                vehicles_in_left_lane += 1
                            else:
                                vehicles_in_right_lane += 1
                        
                        traffic_intensity_left  = "Heavy" if vehicles_in_left_lane > heavy_traffic_threshold else "Smooth"       # Determine the traffic intensity for the left lane
                        traffic_intensity_right = "Heavy" if vehicles_in_right_lane > heavy_traffic_threshold else "Smooth"      # Determine the traffic intensity for the right lane
                        
                        cv2.rectangle(processed_frame, (text_position_left_lane[0]-10, text_position_left_lane[1] - 25), 
                                    (text_position_left_lane[0] + 460, text_position_left_lane[1] + 10), background_color, -1)                  # Add a background rectangle for the left lane vehicle count
                        cv2.rectangle(processed_frame, (intensity_position_left_lane[0]-10, intensity_position_left_lane[1] - 25), 
                                    (intensity_position_left_lane[0] + 460, intensity_position_left_lane[1] + 10), background_color, -1)        # Add a background rectangle for the left lane traffic intensity
                        cv2.rectangle(processed_frame, (text_position_right_lane[0]-10, text_position_right_lane[1] - 25), 
                                    (text_position_right_lane[0] + 460, text_position_right_lane[1] + 10), background_color, -1)                # Add a background rectangle for the right lane vehicle count
                        cv2.rectangle(processed_frame, (intensity_position_right_lane[0]-10, intensity_position_right_lane[1] - 25), 
                                    (intensity_position_right_lane[0] + 460, intensity_position_right_lane[1] + 10), background_color, -1)      # Add a background rectangle for the right lane traffic intensity
                        
                        cv2.putText(processed_frame, f'Vehicles in Left Lane: {vehicles_in_left_lane}', text_position_left_lane, 
                                    font, font_scale, font_color, 2, cv2.LINE_AA)                                                               # Add the {vehicle count text} on {top of the rectangle} for the {left lane}
                        cv2.putText(processed_frame, f'Traffic Intensity: {traffic_intensity_left}', intensity_position_left_lane,          
                                    font, font_scale, font_color, 2, cv2.LINE_AA)                                                               # Add the {traffic intensity text} on {top of the rectangle} for the {left lane}
                        cv2.putText(processed_frame, f'Vehicles in Right Lane: {vehicles_in_right_lane}', text_position_right_lane, 
                                    font, font_scale, font_color, 2, cv2.LINE_AA)                                                               # Add the {vehicle count text} on {top of the rectangle} for the {right lane}
                        cv2.putText(processed_frame, f'Traffic Intensity: {traffic_intensity_right}', intensity_position_right_lane, 
                                    font, font_scale, font_color, 2, cv2.LINE_AA)                                                               # Add the {traffic intensity text} on {top of the rectangle} for the {right lane}
                        out.write(processed_frame)
                    ###################### to avoid memory leaks ######################
                    cap.release()
                    out.release()
                    ###################### Convert AVI to MP4 for Streamlit ######################
                    command = f"ffmpeg -i {output_file} {mp4_file}"
                    os.system(command)
                ###################### Display the processed video ######################
                animation_placeholder.empty()  
                st.write("> # video loaded successfully 🎉.")
                st.video(mp4_file)
#################################################################### END ####################################################################