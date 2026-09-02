document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const clientWebcam = document.getElementById('client-webcam');
    const flaskStream = document.getElementById('flask-stream');
    const statusText = document.getElementById('status-text');
    const statusDot = document.getElementById('status-dot');
    const predictionWord = document.getElementById('prediction-word');
    const predictionConfidence = document.getElementById('prediction-confidence');
    const sentenceOutput = document.getElementById('sentence-output');
    const transOverlay = document.getElementById('trans-overlay');
    const btnToggleTranslate = document.getElementById('btn-toggle-translate');
    const btnClear = document.getElementById('btn-clear-sentence');
    const btnBackspace = document.getElementById('btn-backspace-sentence');
    const toast = document.getElementById('toast-notification');
    const toastText = document.getElementById('toast-text');

    // App state
    let isTranslationActive = true;
    let isBackendConnected = false;
    let apiInterval = null;
    let mockInterval = null;
    let localStream = null;

    // Mock classes for fallback demo mode
    const mockWords = ["1", "2", "3", "4", "5", "สวัสดี", "ขอบคุณ", "สบายดี", "ยินดี"];
    let mockSentence = [];

    // Check if we are running via Flask server or file protocol
    const serverUrl = window.location.origin;
    const isLocalFile = window.location.protocol === 'file:';

    // Show a premium toast notification
    function showToast(message) {
        toastText.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Initialize camera stream
    async function initCamera() {
        if (isLocalFile) {
            startClientWebcam();
        } else {
            // Check if Flask backend is responsive
            try {
                const response = await fetch(`${serverUrl}/api/prediction`, { method: 'GET' });
                if (response.ok) {
                    isBackendConnected = true;
                    startBackendStream();
                } else {
                    startClientWebcam();
                }
            } catch (err) {
                console.log("Cannot connect to Flask server, running in Client Mock mode:", err);
                startClientWebcam();
            }
        }
    }

    // Mode 1: Connect to Flask backend
    function startBackendStream() {
        // Hide local video, show backend stream image
        clientWebcam.style.display = 'none';
        flaskStream.style.display = 'block';
        flaskStream.src = `${serverUrl}/video_feed`;

        // Update Status indicator
        statusText.textContent = 'ONLINE (REAL-TIME MODEL)';
        statusDot.className = 'indicator-dot active';

        showToast('เชื่อมต่อเซิร์ฟเวอร์โมเดลภาษามือแล้ว');

        // Stop client webcam if it was active
        stopClientWebcam();

        // Start polling API for translation text
        if (apiInterval) clearInterval(apiInterval);
        apiInterval = setInterval(pollBackendPrediction, 200);
    }

    // Mode 2: Client webcam fallback with simulated predictions
    async function startClientWebcam() {
        flaskStream.style.display = 'none';
        clientWebcam.style.display = 'block';

        statusText.textContent = 'FRONTEND ONLY (DEMO)';
        statusDot.className = 'indicator-dot active';
        statusDot.style.backgroundColor = '#fbbf24'; // Yellow color for demo
        statusDot.style.boxShadow = '0 0 8px #fbbf24';

        try {
            localStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 640, height: 480, facingMode: 'user' }
            });
            clientWebcam.srcObject = localStream;
            showToast('เข้าถึงกล้องเว็บแคมผ่านเบราว์เซอร์สำเร็จ');

            // Start mock predictions
            startMockPredictions();
        } catch (err) {
            console.error("Camera access blocked:", err);
            statusText.textContent = 'CAMERA BLOCKED';
            statusDot.className = 'indicator-dot';
            statusDot.style.backgroundColor = '#ef4444';
            statusDot.style.boxShadow = 'none';
            predictionWord.textContent = 'เข้าถึงกล้องไม่ได้';
            showToast('ไม่สามารถเปิดใช้งานกล้องได้ โปรนอนุญาตให้เข้าถึงกล้อง');
        }
    }

    function stopClientWebcam() {
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
    }

    // Poll predictions from Flask backend
    async function pollBackendPrediction() {
        if (!isTranslationActive) return;

        try {
            const response = await fetch(`${serverUrl}/api/prediction`);
            if (response.ok) {
                const data = await response.json();
                updateUI(data.prediction, data.confidence, data.sentence);
            }
        } catch (err) {
            console.error("Error polling prediction:", err);
            // If backend connection fails suddenly, switch to offline mode
            isBackendConnected = false;
            clearInterval(apiInterval);
            startClientWebcam();
        }
    }

    // Simulate predictions for Demo Mode
    function startMockPredictions() {
        if (mockInterval) clearInterval(mockInterval);

        let lastMockWord = "";

        mockInterval = setInterval(() => {
            if (!isTranslationActive) return;

            // 70% chance to detect something, 30% chance to remain "Blank"
            if (Math.random() > 0.4) {
                const randomWord = mockWords[Math.floor(Math.random() * mockWords.length)];
                const randomConfidence = (85 + Math.random() * 14).toFixed(1);

                // Only trigger sentence append if it's different from the last word
                if (randomWord !== lastMockWord) {
                    lastMockWord = randomWord;

                    // Add word to mock sentence
                    if (mockSentence.length === 0 || mockSentence[mockSentence.length - 1] !== randomWord) {
                        mockSentence.push(randomWord);
                        if (mockSentence.length > 8) mockSentence.shift();
                    }
                }

                updateUI(randomWord, `${randomConfidence}%`, mockSentence.join(' '));
            } else {
                // Background state
                updateUI("รอกลุ่มท่าทาง...", "0.0%", mockSentence.join(' ') || "...");
            }
        }, 2500); // Trigger mock translation updates every 2.5 seconds
    }

    // Update UI Elements with smooth animation feedback
    let prevWord = "";
    function updateUI(word, confidence, sentence) {
        // Trigger micro-animation if the word changes
        if (word !== prevWord && word !== "รอกลุ่มท่าทาง..." && word !== "กำลังรอสัญญาณมือ...") {
            predictionWord.style.transform = 'scale(1.1)';
            predictionWord.style.transition = 'transform 0.15s ease-out';
            setTimeout(() => {
                predictionWord.style.transform = 'scale(1)';
            }, 150);

            // Subtle glow on overlay when prediction happens
            transOverlay.style.borderColor = 'rgba(99, 102, 241, 0.4)';
            setTimeout(() => {
                transOverlay.style.borderColor = 'rgba(255, 255, 255, 0.08)';
            }, 300);
        }

        prevWord = word;
        predictionWord.textContent = word;
        predictionConfidence.textContent = confidence;
        sentenceOutput.textContent = sentence || '...';
    }

    // Send control actions to the backend (or handle locally if in demo mode)
    async function handleControlAction(action) {
        if (isBackendConnected) {
            try {
                const response = await fetch(`${serverUrl}/api/control`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ action: action })
                });
                if (response.ok) {
                    const data = await response.json();
                    updateUI(data.prediction, data.confidence, data.sentence);
                }
            } catch (err) {
                console.error("Control action error:", err);
            }
        } else {
            // Local fallback handling
            if (action === 'clear') {
                mockSentence = [];
                updateUI("ล้างประโยคแล้ว", "0.0%", "...");
                showToast('ล้างประโยคทั้งหมดสำเร็จ');
            } else if (action === 'backspace') {
                if (mockSentence.length > 0) {
                    mockSentence.pop();
                    updateUI("ลบคำล่าสุดแล้ว", "0.0%", mockSentence.join(' ') || "...");
                    showToast('ลบคำล่าสุดเรียบร้อย');
                }
            }
        }
    }

    // Button Click Handlers
    btnClear.addEventListener('click', () => handleControlAction('clear'));
    btnBackspace.addEventListener('click', () => handleControlAction('backspace'));

    // Toggle Translate Visibility (white circular translation button)
    btnToggleTranslate.addEventListener('click', () => {
        isTranslationActive = !isTranslationActive;

        if (isTranslationActive) {
            transOverlay.classList.remove('hidden');
            btnToggleTranslate.style.backgroundColor = '#ffffff';
            btnToggleTranslate.style.boxShadow = '0 10px 20px rgba(255, 255, 255, 0.15)';
            btnToggleTranslate.querySelector('i').style.color = '#0a0b10';
            showToast('เปิดระบบตรวจจับภาษามือ');
        } else {
            transOverlay.classList.add('hidden');
            btnToggleTranslate.style.backgroundColor = '#ef4444'; // Red background when off
            btnToggleTranslate.style.boxShadow = '0 10px 20px rgba(239, 68, 68, 0.3)';
            btnToggleTranslate.querySelector('i').style.color = '#ffffff';
            showToast('ปิดระบบตรวจจับภาษามือชั่วคราว');
        }
    });

    // Profile Click - Easter egg
    document.getElementById('btn-profile').addEventListener('click', () => {
        showToast('เปิดใช้งานหน้าโปรไฟล์ของโบสถ์');
    });

    // Plan your visit click
    document.getElementById('btn-plan').addEventListener('click', () => {
        showToast('ระบบส่งคุณไปยังหน้านัดหมายและวางแผนเข้าชมโบสถ์');
    });

    // Give click
    document.getElementById('btn-give').addEventListener('click', () => {
        showToast('ขอบคุณสำหรับการบริจาคถวายให้กับคริสตจักร');
    });

    // Start App
    initCamera();
});
