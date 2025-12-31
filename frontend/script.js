// --- CONFIGURATION ---
const socket = new WebSocket("ws://127.0.0.1:8000/ws");
const videoUpload = document.getElementById('videoUpload');
const inputVideo = document.getElementById('inputVideo');
const outputImage = document.getElementById('outputImage');
const repCountElement = document.getElementById('repCount');
const feedbackElement = document.getElementById('feedback');
const exerciseSelector = document.getElementById('exerciseType');
const camBtn = document.getElementById('camBtn');
const webcamVideo = document.getElementById('webcam');

let isProcessing = false;
let cameraActive = false;
let watchdogTimer = null;
let intervalId = null;
let frameCounter = 0; 
let lastRepCount = 0; 

// --- 1. WEBSOCKET CONNECTION ---
socket.onopen = () => console.log("✅ WebSocket Connected");

socket.onmessage = (event) => {
    try {
        const data = JSON.parse(event.data);
        if (!data.processed_image) { isProcessing = false; return; }

        // Update UI
        repCountElement.innerText = data.reps;
        if (data.reps > lastRepCount) {
            triggerFlash();
            lastRepCount = data.reps;
        }

        if (data.feedback) {
            feedbackElement.innerText = data.feedback;
            feedbackElement.style.color = data.color === "green" ? "#00f3ff" : 
                                          data.color === "red" ? "#ff0055" : "gray";
        }

        outputImage.src = `data:image/jpeg;base64,${data.processed_image}`;

        if (data.angle) {
            frameCounter++;
            if (frameCounter % 3 === 0) updateChart(data.angle);
        }

    } catch (e) { console.error(e); }
    isProcessing = false;
};

socket.onclose = () => {
    console.log("❌ WebSocket Disconnected");
};

// --- 2. UPLOAD VIDEO LOGIC ---
videoUpload.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // ⚡ AUTO-SAVE: Save previous session if reps exist
    if (!cameraActive && parseInt(repCountElement.innerText) > 0) {
        saveSessionToHistory();
    }

    // 1. Cleanup
    if (cameraActive) stopCamera();
    if (intervalId) clearInterval(intervalId);
    isProcessing = false; 

    // 2. Reset UI
    repCountElement.innerText = "0";
    lastRepCount = 0;
    document.getElementById('placeholder').style.display = 'none'; 
    outputImage.style.display = 'block'; 

    // 3. Load Video
    const url = URL.createObjectURL(file);
    inputVideo.src = url;
    inputVideo.muted = true;
    inputVideo.loop = false;

    // 4. Start only when loaded
    inputVideo.onloadeddata = () => {
        console.log("🎬 New Video Loaded");
        inputVideo.play();
        startAnalysis();
        intervalId = setInterval(processVideoFrame, 40); 
    };
    
    event.target.value = ''; 
});

inputVideo.onended = () => {
    console.log("🎬 Video Finished.");
    clearInterval(intervalId);
    feedbackElement.innerText = "COMPLETE";
    feedbackElement.style.color = "white";
    saveSessionToHistory();
};

// --- 3. CAMERA LOGIC ---
camBtn.addEventListener('click', async () => {
    if (!cameraActive) {
        try {
            // ⚡ AUTO-SAVE: Save video progress before starting cam
            if (parseInt(repCountElement.innerText) > 0) {
                saveSessionToHistory();
            }

            if (intervalId) clearInterval(intervalId);
            isProcessing = false;
            document.getElementById('placeholder').style.display = 'none';
            outputImage.style.display = 'block';
            
            repCountElement.innerText = "0";
            lastRepCount = 0;

            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            webcamVideo.srcObject = stream;
            await webcamVideo.play(); 

            cameraActive = true;
            camBtn.innerText = "⏹ Stop Camera";
            camBtn.classList.remove('bg-gym-yellow', 'text-black', 'border-gym-yellow');
            camBtn.classList.add('bg-red-600', 'text-white', 'border-red-600');
            
            startAnalysis(); 
            intervalId = setInterval(sendWebcamFrame, 50); 
            
        } catch (err) { alert(err); }
    } else {
        stopCamera();
    }
});

function stopCamera() {
    console.log("⏹ Stopping Camera...");
    cameraActive = false;
    clearInterval(intervalId);

    const stream = webcamVideo.srcObject;
    if (stream) stream.getTracks().forEach(track => track.stop());
    webcamVideo.srcObject = null;
    
    camBtn.innerText = "Start Live Cam";
    camBtn.classList.add('bg-gym-yellow', 'text-black', 'border-gym-yellow');
    camBtn.classList.remove('bg-red-600', 'text-white', 'border-red-600');
    
    feedbackElement.innerText = "READY";
    saveSessionToHistory();
}

// --- 4. HISTORY HELPER  ---
function saveSessionToHistory() {
    const reps = parseInt(repCountElement.innerText);
    const mode = exerciseSelector.value;
    
    if (reps > 0) {
        addToHistory(reps, mode);
    }
}

function addToHistory(reps, mode) {
    const list = document.getElementById('historyList');
    const text = list.innerText.toLowerCase();

    // ⚡ FIX: Checks for "no data recorded" to clear the placeholder correctly
    if (text.includes('no data') || text.includes('no sessions')) {
        list.innerHTML = '';
    }
    
    const item = document.createElement('div');
    item.className = 'bg-white/5 p-3 rounded-lg border-l-4 border-gym-yellow mb-2 animate-pulse';
    item.innerHTML = `
        <div class="flex justify-between text-[10px] font-bold text-gray-400 mb-1">
            <span>${new Date().toLocaleTimeString()}</span>
            <span class="text-gym-yellow">${mode.toUpperCase()}</span>
        </div>
        <div class="text-xl font-mono text-white font-bold">${reps} REPS</div>
    `;
    
    setTimeout(() => item.classList.remove('animate-pulse'), 1000);
    list.prepend(item);
}

function clearHistory() { 
    document.getElementById('historyList').innerHTML = '<div class="text-center font-display text-xl text-gray-700 mt-10 uppercase">No data recorded</div>'; 
}

// --- 5. FRAME SENDING ---
function processVideoFrame() {
    if (inputVideo.paused || inputVideo.ended) return;
    sendFrame(inputVideo);
}

function sendWebcamFrame() {
    if (!cameraActive) return;
    if (webcamVideo.videoWidth > 0) sendFrame(webcamVideo);
}

function sendFrame(source) {
    if (socket.readyState !== WebSocket.OPEN || isProcessing) return;
    if (source.videoWidth === 0) return;

    isProcessing = true;
    const canvas = document.getElementById('hiddenCanvas');
    const ctx = canvas.getContext('2d');

    const MAX_WIDTH = 480; 
    const scale = Math.min(1, MAX_WIDTH / source.videoWidth);
    
    canvas.width = source.videoWidth * scale;
    canvas.height = source.videoHeight * scale;

    if (source === webcamVideo) {
        ctx.translate(canvas.width, 0);
        ctx.scale(-1, 1);
    }
    
    ctx.drawImage(source, 0, 0, canvas.width, canvas.height);

    const frameData = canvas.toDataURL('image/jpeg', 0.6); 
    socket.send(frameData);

    if (watchdogTimer) clearTimeout(watchdogTimer);
    watchdogTimer = setTimeout(() => { isProcessing = false; }, 1000);
}

// --- 6. HELPERS ---
function startAnalysis() {
    if (socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ "config": true, "mode": exerciseSelector.value }));
    }
}

exerciseSelector.addEventListener('change', startAnalysis);

// --- 7. CHARTS & ANIMATION ---
function triggerFlash() {
    const videoContainer = document.getElementById('videoContainer'); 
    
    if (videoContainer) {
        videoContainer.classList.remove('flash-success');
        void videoContainer.offsetWidth; 
        videoContainer.classList.add('flash-success');
    }
}

const ctx = document.getElementById('angleChart').getContext('2d');
const angleChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(30).fill(''),
        datasets: [{
            label: 'Angle',
            data: Array(30).fill(0),
            borderColor: '#EDFF00',
            borderWidth: 2,
            tension: 0.4,
            pointRadius: 0
        }]
    },
    options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { min: 40, max: 180, grid: { color: '#333' } },
            x: { display: false }
        },
        plugins: { legend: { display: false } }
    }
});

function updateChart(value) {
    const data = angleChart.data.datasets[0].data;
    data.shift();
    data.push(value);
    angleChart.update();
}