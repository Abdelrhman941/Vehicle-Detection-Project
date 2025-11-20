// Global variables
let selectedFile = null;
let processInterval = null;
let outputFilename = null;
let ws = null;

// ==================== Initialization ====================
document.addEventListener('DOMContentLoaded', () => {
    checkSystemHealth();
    setupDragAndDrop();
    connectWebSocket();
});

// ==================== WebSocket Connection ====================
function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.progress !== undefined) {
            updateProgress(data.progress, data.processed_frames, data.total_frames);
        }

        if (data.output_file) {
            outputFilename = data.output_file;
            console.log('Output filename set to:', outputFilename);
            showResults();
        }

        if (data.error) {
            showToast(`Processing error: ${data.error}`, 'error');
            resetApp();
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting...');
        setTimeout(connectWebSocket, 3000);
    };
}

// ==================== System Health Check ====================
async function checkSystemHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();

        const statusIndicator = document.getElementById('systemStatus');
        if (data.status === 'healthy' && data.model_loaded) {
            statusIndicator.innerHTML = `
                <span class="status-dot"></span>
                <span class="status-text">System Ready</span>
            `;
        } else {
            statusIndicator.innerHTML = `
                <span class="status-dot" style="background: var(--accent-error);"></span>
                <span class="status-text">Model Not Loaded</span>
            `;
            showToast('Warning: YOLO model not loaded. Please check model path.', 'warning');
        }
    } catch (error) {
        showToast('Error connecting to server', 'error');
    }
}

// ==================== Navigation ====================
function showUploadSection() {
    document.getElementById('welcomeScreen').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');
}

// ==================== Drag and Drop ====================
function setupDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('drag-over');
        });
    });

    uploadArea.addEventListener('drop', handleDrop);
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;

    if (files.length > 0) {
        const file = files[0];
        if (validateFile(file)) {
            selectedFile = file;
            displayFileInfo(file);
        }
    }
}

// ==================== File Selection ====================
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file && validateFile(file)) {
        selectedFile = file;
        displayFileInfo(file);
    }
}

function validateFile(file) {
    const validTypes = ['video/mp4', 'video/avi', 'video/quicktime'];
    const maxSize = 500 * 1024 * 1024; // 500MB

    if (!validTypes.includes(file.type) && !file.name.match(/\.(mp4|avi|mov)$/i)) {
        showToast('Invalid file type. Please upload MP4, AVI, or MOV file.', 'error');
        return false;
    }

    if (file.size > maxSize) {
        showToast('File size too large. Maximum size is 500MB.', 'error');
        return false;
    }

    return true;
}

function displayFileInfo(file) {
    document.getElementById('uploadArea').classList.add('hidden');
    document.getElementById('fileInfo').classList.remove('hidden');

    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = formatFileSize(file.size);
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ==================== Video Processing ====================
async function processVideo() {
    if (!selectedFile) {
        showToast('Please select a video file first', 'error');
        return;
    }

    try {
        // Upload file
        showToast('Uploading video...', 'success');
        const formData = new FormData();
        formData.append('file', selectedFile);

        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadResponse.ok) {
            const error = await uploadResponse.json();
            throw new Error(error.detail || 'Upload failed');
        }

        const uploadData = await uploadResponse.json();

        // Start processing
        const processResponse = await fetch(`/api/process/${uploadData.filename}`, {
            method: 'POST'
        });

        if (!processResponse.ok) {
            const error = await processResponse.json();
            throw new Error(error.detail || 'Processing failed');
        }

        // Show progress card
        document.getElementById('fileInfo').classList.add('hidden');
        document.getElementById('progressCard').classList.remove('hidden');

    } catch (error) {
        showToast(error.message, 'error');
    }
}

function updateProgress(percent, processedFrames = 0, totalFrames = 0) {
    const progressCircle = document.getElementById('progressCircle');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');

    // Circle circumference = 2 * PI * radius = 2 * 3.14159 * 85 = 534.07
    const circumference = 534.07;
    const offset = circumference - (percent / 100) * circumference;

    progressCircle.style.strokeDashoffset = offset;
    progressPercent.textContent = `${percent}%`;

    if (totalFrames > 0) {
        if (percent < 30) {
            progressStatus.textContent = `Initializing... (${processedFrames}/${totalFrames} frames)`;
        } else if (percent < 70) {
            progressStatus.textContent = `Detecting vehicles... (${processedFrames}/${totalFrames} frames)`;
        } else if (percent < 95) {
            progressStatus.textContent = `Rendering video... (${processedFrames}/${totalFrames} frames)`;
        } else {
            progressStatus.textContent = `Finalizing... (${processedFrames}/${totalFrames} frames)`;
        }
    } else {
        if (percent < 30) {
            progressStatus.textContent = 'Initializing video processing...';
        } else if (percent < 70) {
            progressStatus.textContent = 'Analyzing frames and detecting vehicles...';
        } else if (percent < 95) {
            progressStatus.textContent = 'Rendering output video...';
        } else {
            progressStatus.textContent = 'Finalizing...';
        }
    }
}

function showResults() {
    document.getElementById('progressCard').classList.add('hidden');
    document.getElementById('resultsSection').classList.remove('hidden');
    // Video removed - user downloads or opens in new tab
    showToast('Video processing complete!', 'success');
}

function formatDuration(seconds) {
    if (isNaN(seconds)) return '00:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// ==================== Download ====================
function openVideoInNewTab() {
    console.log('openVideoInNewTab called, outputFilename:', outputFilename);

    if (!outputFilename) {
        alert('No video available. Please process a video first.');
        return;
    }

    const aviFilename = outputFilename.replace('.mp4', '.avi');
    const videoUrl = `/outputs/${aviFilename}`;

    console.log('Opening video URL:', videoUrl);

    // Open video file directly in new tab
    const newTab = window.open(videoUrl, '_blank');

    if (newTab) {
        showToast('Opening video in new tab', 'success');
    } else {
        alert('Pop-ups blocked! Please allow pop-ups and try again.');
    }
}

function downloadVideo() {
    console.log('downloadVideo called, outputFilename:', outputFilename);

    if (!outputFilename) {
        alert('No video available. Please process a video first.');
        return;
    }

    const aviFilename = outputFilename.replace('.mp4', '.avi');
    const link = document.createElement('a');
    link.href = `/outputs/${aviFilename}`;
    link.download = aviFilename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('Download started', 'success');
}

// ==================== Reset ====================
function resetApp() {
    selectedFile = null;
    outputFilename = null;

    if (processInterval) {
        clearInterval(processInterval);
        processInterval = null;
    }

    document.getElementById('videoInput').value = '';
    document.getElementById('uploadArea').classList.remove('hidden');
    document.getElementById('fileInfo').classList.add('hidden');
    document.getElementById('progressCard').classList.add('hidden');
    document.getElementById('resultsSection').classList.add('hidden');

    const progressCircle = document.getElementById('progressCircle');
    progressCircle.style.strokeDashoffset = '534.07';
    document.getElementById('progressPercent').textContent = '0%';

    // Clear video source
    const resultVideo = document.getElementById('resultVideo');
    const videoSource = document.getElementById('videoSource');
    resultVideo.pause();
    videoSource.src = '';
    resultVideo.load();
}// ==================== Toast Notifications ====================
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');

    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.remove('hidden');

    setTimeout(() => {
        toast.classList.add('hidden');
    }, 4000);
}
