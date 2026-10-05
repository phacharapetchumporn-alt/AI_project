// Frame capture logic
let captureInterval = null;
let captureCanvas = null;
let captureCtx = null;

function startCapture() {
    if (captureInterval) clearInterval(captureInterval);
    const video = document.getElementById('client-webcam');
    
    if (!captureCanvas) {
        captureCanvas = document.createElement('canvas');
        captureCtx = captureCanvas.getContext('2d');
    }
    
    // We send frames every 200ms
    captureInterval = setInterval(async () => {
        if (!video || video.paused || video.ended) return;
        
        // Scale down to save bandwidth
        captureCanvas.width = 640;
        captureCanvas.height = 480;
        
        // Draw video frame to canvas
        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
        
        const base64Image = captureCanvas.toDataURL('image/jpeg', 0.5);
        
        try {
            const response = await fetch('/api/process_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ image: base64Image })
            });
            const data = await response.json();
        } catch (e) {
            console.error("Error sending frame:", e);
        }
    }, 150); // ~6.6 FPS
}

function stopCapture() {
    if (captureInterval) {
        clearInterval(captureInterval);
        captureInterval = null;
    }
}
