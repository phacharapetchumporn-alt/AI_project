<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', () => {
=======
﻿document.addEventListener('DOMContentLoaded', () => {
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    // DOM Elements - Camera & Translation
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
    const cameraCard = document.getElementById('camera-translator');
    const btnExpandCam = document.getElementById('btn-expand-cam');
    const expandIcon = document.getElementById('expand-icon');
    const expandText = document.getElementById('expand-text');
    const toast = document.getElementById('toast-notification');
    const toastText = document.getElementById('toast-text');

    // Mobile & Camera Controls
    const btnFlipCam = document.getElementById('btn-flip-cam');
    const btnFlipCamBottom = document.getElementById('btn-flip-cam-bottom');
    const btnCameraPower = document.getElementById('btn-camera-power');
    const iconCamPower = document.getElementById('icon-cam-power');
    const btnMobileFullscreen = document.getElementById('btn-mobile-fullscreen');
    const iconMobileFs = document.getElementById('icon-mobile-fs');
    const btnSpeakSentence = document.getElementById('btn-speak-sentence');
    const btnSpeakInline = document.getElementById('btn-speak-inline');
    const cameraFallbackScreen = document.getElementById('camera-fallback-screen');
    const btnStartCamera = document.getElementById('btn-start-camera');
    const fallbackTitle = document.getElementById('fallback-title');
    const fallbackDesc = document.getElementById('fallback-desc');
    const fallbackIconI = document.getElementById('fallback-icon-i');
    const mobileHttpsTip = document.getElementById('mobile-https-tip');
    const linkSwitchHttps = document.getElementById('link-switch-https');
    const scannerHud = document.getElementById('scanner-hud');
    const btnStreamSource = document.getElementById('btn-stream-source');
    const streamSourceIcon = document.getElementById('stream-source-icon');
    const streamSourceText = document.getElementById('stream-source-text');
    const skeletonCanvas = document.getElementById('skeleton-canvas');
    const skeletonCtx = skeletonCanvas && typeof skeletonCanvas.getContext === 'function' ? skeletonCanvas.getContext('2d') : null;

    // Mobile Connect Modal Elements
    const btnOpenMobileModal = document.getElementById('btn-open-mobile-modal');
    const mobileModalOverlay = document.getElementById('mobile-modal-overlay');
    const btnCloseMobileModal = document.getElementById('btn-close-mobile-modal');
    const qrCodeImage = document.getElementById('qr-code-image');
    const qrLoading = document.getElementById('qr-loading');
    const mobileUrlInput = document.getElementById('mobile-url-input');
    const btnCopyUrl = document.getElementById('btn-copy-url');

    // App state
    let isTranslationActive = true;
    let isBackendConnected = false;
    let isCameraRunning = false;
    let currentFacingMode = 'user'; // 'user' (front) or 'environment' (back)
    let currentStreamMode = 'client'; // 'client' or 'server'
    let isFrameSending = false;
    let frameCaptureInterval = null;
    let captureCanvas = document.createElement('canvas');
    let captureCtx = captureCanvas.getContext('2d');
    let apiInterval = null;
    let mockInterval = null;
    let localStream = null;

    // Realistic Thai sign language words
<<<<<<< HEAD
    const mockWords = ["สวัสดี", "ขอบคุณ", "สบายดี", "ยินดีต้อนรับ", "ฉันรักคุณ", "เข้าใจแล้ว", "ขอความช่วยเหลือ", "โบสถ์", "1", "2", "3", "ใช่", "ตกลง"];
=======
    const mockWords = ["à¸ªà¸§à¸±à¸ªà¸”à¸µ", "à¸‚à¸­à¸šà¸„à¸¸à¸“", "à¸ªà¸šà¸²à¸¢à¸”à¸µ", "à¸¢à¸´à¸™à¸”à¸µà¸•à¹‰à¸­à¸™à¸£à¸±à¸š", "à¸‰à¸±à¸™à¸£à¸±à¸à¸„à¸¸à¸“", "à¹€à¸‚à¹‰à¸²à¹ƒà¸ˆà¹à¸¥à¹‰à¸§", "à¸‚à¸­à¸„à¸§à¸²à¸¡à¸Šà¹ˆà¸§à¸¢à¹€à¸«à¸¥à¸·à¸­", "à¹‚à¸šà¸ªà¸–à¹Œ", "1", "2", "3", "à¹ƒà¸Šà¹ˆ", "à¸•à¸à¸¥à¸‡"];
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    let mockSentence = [];

    // Server origin
    const serverUrl = window.location.origin;
    const isLocalFile = window.location.protocol === 'file:';

    // Show a premium toast notification
    function showToast(message) {
        if (!toast || !toastText) return;
        toastText.textContent = message;
        toast.classList.add('show');
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    // Thai Text-to-Speech (TTS)
    function speakText(text) {
<<<<<<< HEAD
        if (!text || text === '...' || text === 'กำลังรอสัญญาณมือ...') {
            showToast('ยังไม่มีข้อความสำหรับการอ่านออกเสียง');
=======
        if (!text || text === '...' || text === 'à¸à¸³à¸¥à¸±à¸‡à¸£à¸­à¸ªà¸±à¸à¸à¸²à¸“à¸¡à¸·à¸­...') {
            showToast('à¸¢à¸±à¸‡à¹„à¸¡à¹ˆà¸¡à¸µà¸‚à¹‰à¸­à¸„à¸§à¸²à¸¡à¸ªà¸³à¸«à¸£à¸±à¸šà¸à¸²à¸£à¸­à¹ˆà¸²à¸™à¸­à¸­à¸à¹€à¸ªà¸µà¸¢à¸‡');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            return;
        }
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'th-TH';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
<<<<<<< HEAD
            showToast(`🔊 กำลังอ่านออกเสียง: "${text}"`);
        } else {
            showToast('อุปกรณ์ของคุณไม่รองรับฟังก์ชัน Text-to-Speech');
=======
            showToast(`ðŸ”Š à¸à¸³à¸¥à¸±à¸‡à¸­à¹ˆà¸²à¸™à¸­à¸­à¸à¹€à¸ªà¸µà¸¢à¸‡: "${text}"`);
        } else {
            showToast('à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸‚à¸­à¸‡à¸„à¸¸à¸“à¹„à¸¡à¹ˆà¸£à¸­à¸‡à¸£à¸±à¸šà¸Ÿà¸±à¸‡à¸à¹Œà¸Šà¸±à¸™ Text-to-Speech');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        }
    }

    // Stop current media stream tracks
    function stopStreamTracks() {
        if (localStream) {
            localStream.getTracks().forEach(track => {
                track.stop();
            });
            localStream = null;
        }
    }

    // Display camera fallback screen with message
    function showCameraFallback(title, desc, iconClass = 'fa-solid fa-video-slash') {
        if (clientWebcam) clientWebcam.style.display = 'none';
        if (flaskStream) flaskStream.style.display = 'none';
        if (scannerHud) scannerHud.style.display = 'none';
        if (cameraFallbackScreen) {
            cameraFallbackScreen.style.display = 'flex';
            if (fallbackTitle) fallbackTitle.textContent = title;
            if (fallbackDesc) fallbackDesc.textContent = desc;
            if (fallbackIconI) fallbackIconI.className = iconClass;
        }
        statusText.textContent = 'CAMERA PAUSED';
        statusDot.className = 'indicator-dot';
        statusDot.style.backgroundColor = '#ef4444';
        statusDot.style.boxShadow = 'none';

        if (btnCameraPower) btnCameraPower.classList.remove('active');
        if (iconCamPower) iconCamPower.className = 'fa-solid fa-video-slash';
    }

    // Initialize camera stream
    async function initCamera() {
        // Detect if mobile browser in insecure context
        const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
        const isSecure = window.isSecureContext;
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        const isHttp = window.location.protocol === 'http:';

        // Show HTTPS tip immediately if on HTTP and not localhost
        if ((isHttp || !isSecure) && !isLocal) {
            if (mobileHttpsTip) {
                mobileHttpsTip.style.display = 'flex';
                if (linkSwitchHttps) {
                    linkSwitchHttps.href = `https://${window.location.hostname}:5000${window.location.pathname}`;
                }
            }
        }

        // On mobile: show fallback screen with open-camera button first
        // (require user gesture for camera permission on mobile browsers)
        if (isMobile) {
            showCameraFallback(
<<<<<<< HEAD
                'แตะเพื่อเปิดกล้อง',
                'กดปุ่มด้านล่างเพื่ออนุญาตให้เว็บไซต์เข้าถึงกล้องโทรศัพท์ของคุณ',
=======
                'à¹à¸•à¸°à¹€à¸žà¸·à¹ˆà¸­à¹€à¸›à¸´à¸”à¸à¸¥à¹‰à¸­à¸‡',
                'à¸à¸”à¸›à¸¸à¹ˆà¸¡à¸”à¹‰à¸²à¸™à¸¥à¹ˆà¸²à¸‡à¹€à¸žà¸·à¹ˆà¸­à¸­à¸™à¸¸à¸à¸²à¸•à¹ƒà¸«à¹‰à¹€à¸§à¹‡à¸šà¹„à¸‹à¸•à¹Œà¹€à¸‚à¹‰à¸²à¸–à¸¶à¸‡à¸à¸¥à¹‰à¸­à¸‡à¹‚à¸—à¸£à¸¨à¸±à¸žà¸—à¹Œà¸‚à¸­à¸‡à¸„à¸¸à¸“',
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                'fa-solid fa-camera'
            );
            // Show the fallback screen (override the display:none)
            if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'flex';
            return; // Wait for user to tap the button
        }

        // Check backend prediction endpoint
        if (!isLocalFile) {
            try {
                const response = await fetch(`${serverUrl}/api/prediction`, { method: 'GET' });
                if (response.ok) {
                    isBackendConnected = true;
                }
            } catch (err) {
                console.log("Cannot connect to Flask server prediction API:", err);
                isBackendConnected = false;
            }
        }

        // Start client camera stream directly (PC)
        await startClientWebcam('user');
    }

    // Start Client Webcam (Mobile & PC WebRTC)
    async function startClientWebcam(facingMode = currentFacingMode) {
        currentFacingMode = facingMode;

        // Check WebRTC / secure context support
        const isHttp = window.location.protocol === 'http:';
        const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showCameraFallback(
<<<<<<< HEAD
                'ไม่สามารถเปิดกล้องได้',
                isHttp && !isLocal
                    ? 'เบราว์เซอร์บนมือถือต้องการ HTTPS เพื่อเปิดกล้อง กรุณาเปิดผ่าน HTTPS (แตะลิงก์ด้านล่าง)'
                    : 'เบราว์เซอร์ของคุณไม่รองรับการเปิดกล้องผ่าน WebRTC กรุณาอัปเดตเบราว์เซอร์',
=======
                'à¹„à¸¡à¹ˆà¸ªà¸²à¸¡à¸²à¸£à¸–à¹€à¸›à¸´à¸”à¸à¸¥à¹‰à¸­à¸‡à¹„à¸”à¹‰',
                isHttp && !isLocal
                    ? 'à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œà¸šà¸™à¸¡à¸·à¸­à¸–à¸·à¸­à¸•à¹‰à¸­à¸‡à¸à¸²à¸£ HTTPS à¹€à¸žà¸·à¹ˆà¸­à¹€à¸›à¸´à¸”à¸à¸¥à¹‰à¸­à¸‡ à¸à¸£à¸¸à¸“à¸²à¹€à¸›à¸´à¸”à¸œà¹ˆà¸²à¸™ HTTPS (à¹à¸•à¸°à¸¥à¸´à¸‡à¸à¹Œà¸”à¹‰à¸²à¸™à¸¥à¹ˆà¸²à¸‡)'
                    : 'à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œà¸‚à¸­à¸‡à¸„à¸¸à¸“à¹„à¸¡à¹ˆà¸£à¸­à¸‡à¸£à¸±à¸šà¸à¸²à¸£à¹€à¸›à¸´à¸”à¸à¸¥à¹‰à¸­à¸‡à¸œà¹ˆà¸²à¸™ WebRTC à¸à¸£à¸¸à¸“à¸²à¸­à¸±à¸›à¹€à¸”à¸•à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œ',
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                'fa-solid fa-triangle-exclamation'
            );
            if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'flex';

            if (isHttp && !isLocal && mobileHttpsTip) {
                mobileHttpsTip.style.display = 'flex';
                if (linkSwitchHttps) {
                    linkSwitchHttps.href = `https://${window.location.hostname}:5000${window.location.pathname}`;
                }
            }
            return;
        }

        // Stop prior tracks
        stopStreamTracks();

        // Hide fallback screen
        if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'none';
        if (clientWebcam) clientWebcam.style.display = 'block';
        if (flaskStream) flaskStream.style.display = 'none';

        // Fallback constraint attempts
        const attempts = [
            {
                video: {
                    facingMode: { ideal: facingMode },
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            },
            {
                video: {
                    facingMode: facingMode
                },
                audio: false
            },
            {
                video: true,
                audio: false
            }
        ];

        let streamObtained = null;
        let lastErr = null;

        for (const constraints of attempts) {
            try {
                streamObtained = await navigator.mediaDevices.getUserMedia(constraints);
                if (streamObtained) break;
            } catch (err) {
                lastErr = err;
            }
        }

        if (streamObtained) {
            localStream = streamObtained;
            isCameraRunning = true;
            clientWebcam.srcObject = localStream;

            // Critical for iOS Safari & Android mobile autoplay
            clientWebcam.setAttribute('playsinline', 'true');
            clientWebcam.setAttribute('webkit-playsinline', 'true');
            clientWebcam.muted = true;
            try {
                await clientWebcam.play();
            } catch (pErr) {
                console.warn('Autoplay prevented:', pErr);
            }

            if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'none';
            if (scannerHud) scannerHud.style.display = 'block';

<<<<<<< HEAD
            const camName = facingMode === 'user' ? 'กล้องหน้า' : 'กล้องหลัง';
=======
            const camName = facingMode === 'user' ? 'à¸à¸¥à¹‰à¸­à¸‡à¸«à¸™à¹‰à¸²' : 'à¸à¸¥à¹‰à¸­à¸‡à¸«à¸¥à¸±à¸‡';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            statusText.textContent = isBackendConnected ? `AI CONNECTED (${camName})` : `LIVE (${camName})`;
            statusDot.className = 'indicator-dot active';
            statusDot.style.backgroundColor = '#10b981';
            statusDot.style.boxShadow = '0 0 8px #10b981';

            if (btnCameraPower) btnCameraPower.classList.add('active');
            if (iconCamPower) iconCamPower.className = 'fa-solid fa-video';

<<<<<<< HEAD
            showToast(`เปิด${camName}สำเร็จแล้ว เชื่อมต่อ AI TSL LSTM เรียบร้อย`);
=======
            showToast(`à¹€à¸›à¸´à¸”${camName}à¸ªà¸³à¹€à¸£à¹‡à¸ˆà¹à¸¥à¹‰à¸§ à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­ AI TSL LSTM à¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢`);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9

            if (isBackendConnected) {
                startFrameCapture();
            } else {
                startMockPredictions();
            }
        } else {
            console.error("Camera access failed:", lastErr);
            isCameraRunning = false;
<<<<<<< HEAD
            let errMsg = 'ไม่สามารถเปิดกล้องได้';
            let errDesc = 'โปรดตรวจสอบการอนุญาตสิทธิ์กล้องในการตั้งค่าของเบราว์เซอร์';

            if (lastErr) {
                if (lastErr.name === 'NotAllowedError' || lastErr.name === 'PermissionDeniedError') {
                    errMsg = 'สิทธิ์การใช้กล้องถูกปฏิเสธ';
                    errDesc = 'โปรดแตะอนุญาต (Allow) การเข้าถึงกล้องในการตั้งค่าเบราว์เซอร์ แล้วแตะปุ่มด้านล่างเพื่อลองใหม่';
                } else if (lastErr.name === 'NotFoundError' || lastErr.name === 'DevicesNotFoundError') {
                    errMsg = 'ไม่พบอุปกรณ์กล้อง';
                    errDesc = 'อุปกรณ์นี้ไม่มีกล้อง หรือกล้องไม่ได้เชื่อมต่ออยู่';
                } else if (lastErr.name === 'NotReadableError' || lastErr.name === 'TrackStartError') {
                    errMsg = 'กล้องกำลังถูกใช้งานอยู่';
                    errDesc = 'กล้องอาจถูกใช้งานโดยแอปพลิเคชันอื่น โปรดปิดแอปอื่นแล้วลองใหม่อีกครั้ง';
=======
            let errMsg = 'à¹„à¸¡à¹ˆà¸ªà¸²à¸¡à¸²à¸£à¸–à¹€à¸›à¸´à¸”à¸à¸¥à¹‰à¸­à¸‡à¹„à¸”à¹‰';
            let errDesc = 'à¹‚à¸›à¸£à¸”à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸à¸²à¸£à¸­à¸™à¸¸à¸à¸²à¸•à¸ªà¸´à¸—à¸˜à¸´à¹Œà¸à¸¥à¹‰à¸­à¸‡à¹ƒà¸™à¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¸‚à¸­à¸‡à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œ';

            if (lastErr) {
                if (lastErr.name === 'NotAllowedError' || lastErr.name === 'PermissionDeniedError') {
                    errMsg = 'à¸ªà¸´à¸—à¸˜à¸´à¹Œà¸à¸²à¸£à¹ƒà¸Šà¹‰à¸à¸¥à¹‰à¸­à¸‡à¸–à¸¹à¸à¸›à¸à¸´à¹€à¸ªà¸˜';
                    errDesc = 'à¹‚à¸›à¸£à¸”à¹à¸•à¸°à¸­à¸™à¸¸à¸à¸²à¸• (Allow) à¸à¸²à¸£à¹€à¸‚à¹‰à¸²à¸–à¸¶à¸‡à¸à¸¥à¹‰à¸­à¸‡à¹ƒà¸™à¸à¸²à¸£à¸•à¸±à¹‰à¸‡à¸„à¹ˆà¸²à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œ à¹à¸¥à¹‰à¸§à¹à¸•à¸°à¸›à¸¸à¹ˆà¸¡à¸”à¹‰à¸²à¸™à¸¥à¹ˆà¸²à¸‡à¹€à¸žà¸·à¹ˆà¸­à¸¥à¸­à¸‡à¹ƒà¸«à¸¡à¹ˆ';
                } else if (lastErr.name === 'NotFoundError' || lastErr.name === 'DevicesNotFoundError') {
                    errMsg = 'à¹„à¸¡à¹ˆà¸žà¸šà¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸à¸¥à¹‰à¸­à¸‡';
                    errDesc = 'à¸­à¸¸à¸›à¸à¸£à¸“à¹Œà¸™à¸µà¹‰à¹„à¸¡à¹ˆà¸¡à¸µà¸à¸¥à¹‰à¸­à¸‡ à¸«à¸£à¸·à¸­à¸à¸¥à¹‰à¸­à¸‡à¹„à¸¡à¹ˆà¹„à¸”à¹‰à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸­à¸¢à¸¹à¹ˆ';
                } else if (lastErr.name === 'NotReadableError' || lastErr.name === 'TrackStartError') {
                    errMsg = 'à¸à¸¥à¹‰à¸­à¸‡à¸à¸³à¸¥à¸±à¸‡à¸–à¸¹à¸à¹ƒà¸Šà¹‰à¸‡à¸²à¸™à¸­à¸¢à¸¹à¹ˆ';
                    errDesc = 'à¸à¸¥à¹‰à¸­à¸‡à¸­à¸²à¸ˆà¸–à¸¹à¸à¹ƒà¸Šà¹‰à¸‡à¸²à¸™à¹‚à¸”à¸¢à¹à¸­à¸›à¸žà¸¥à¸´à¹€à¸„à¸Šà¸±à¸™à¸­à¸·à¹ˆà¸™ à¹‚à¸›à¸£à¸”à¸›à¸´à¸”à¹à¸­à¸›à¸­à¸·à¹ˆà¸™à¹à¸¥à¹‰à¸§à¸¥à¸­à¸‡à¹ƒà¸«à¸¡à¹ˆà¸­à¸µà¸à¸„à¸£à¸±à¹‰à¸‡';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                }
            }

            showCameraFallback(errMsg, errDesc, 'fa-solid fa-video-slash');
        }
    }

    // Stop Client Webcam
    function stopClientWebcam() {
        stopStreamTracks();
        if (clientWebcam) clientWebcam.srcObject = null;
        isCameraRunning = false;
        stopFrameCapture();
        if (skeletonCtx && skeletonCanvas) {
            skeletonCtx.clearRect(0, 0, skeletonCanvas.width, skeletonCanvas.height);
        }
        if (apiInterval) clearInterval(apiInterval);
        if (mockInterval) clearInterval(mockInterval);
<<<<<<< HEAD
        showCameraFallback('กล้องถูกปิดอยู่', 'แตะปุ่มด้านล่างหรือไอคอนกล้องเพื่อเปิดการทำงานใหม่');
        showToast('ปิดการทำงานของกล้องแล้ว');
=======
        showCameraFallback('à¸à¸¥à¹‰à¸­à¸‡à¸–à¸¹à¸à¸›à¸´à¸”à¸­à¸¢à¸¹à¹ˆ', 'à¹à¸•à¸°à¸›à¸¸à¹ˆà¸¡à¸”à¹‰à¸²à¸™à¸¥à¹ˆà¸²à¸‡à¸«à¸£à¸·à¸­à¹„à¸­à¸„à¸­à¸™à¸à¸¥à¹‰à¸­à¸‡à¹€à¸žà¸·à¹ˆà¸­à¹€à¸›à¸´à¸”à¸à¸²à¸£à¸—à¸³à¸‡à¸²à¸™à¹ƒà¸«à¸¡à¹ˆ');
        showToast('à¸›à¸´à¸”à¸à¸²à¸£à¸—à¸³à¸‡à¸²à¸™à¸‚à¸­à¸‡à¸à¸¥à¹‰à¸­à¸‡à¹à¸¥à¹‰à¸§');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    }

    // Toggle Camera On/Off
    function toggleCameraPower() {
        if (isCameraRunning) {
            stopClientWebcam();
        } else {
            if (currentStreamMode === 'server') {
                switchStreamMode('server');
            } else {
                startClientWebcam(currentFacingMode);
            }
        }
    }

    // Flip Camera Front/Rear (for Mobile Phone)
    function flipCamera() {
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';

        if (btnFlipCam) btnFlipCam.classList.add('rotating');
        if (btnFlipCamBottom) btnFlipCamBottom.classList.add('rotating');
        setTimeout(() => {
            if (btnFlipCam) btnFlipCam.classList.remove('rotating');
            if (btnFlipCamBottom) btnFlipCamBottom.classList.remove('rotating');
        }, 600);

<<<<<<< HEAD
        showToast(`กำลังสลับไปยัง${currentFacingMode === 'user' ? 'กล้องหน้า' : 'กล้องหลัง'}...`);
=======
        showToast(`à¸à¸³à¸¥à¸±à¸‡à¸ªà¸¥à¸±à¸šà¹„à¸›à¸¢à¸±à¸‡${currentFacingMode === 'user' ? 'à¸à¸¥à¹‰à¸­à¸‡à¸«à¸™à¹‰à¸²' : 'à¸à¸¥à¹‰à¸­à¸‡à¸«à¸¥à¸±à¸‡'}...`);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        startClientWebcam(currentFacingMode);
    }

    // -------------------------------------------------------------------------
    // AI Frame Capture & Skeleton Landmark Rendering (MediaPipe TSL 150)
    // -------------------------------------------------------------------------

    // Hand connections
    const HAND_CONNECTIONS = [
        [0, 1], [1, 2], [2, 3], [3, 4],       // Thumb
        [0, 5], [5, 6], [6, 7], [7, 8],       // Index
        [0, 9], [9, 10], [10, 11], [11, 12],  // Middle
        [0, 13], [13, 14], [14, 15], [15, 16],// Ring
        [0, 17], [17, 18], [18, 19], [19, 20] // Pinky
    ];

    // Upper body Pose connections
    const POSE_CONNECTIONS = [
        [11, 12], [11, 13], [13, 15], [12, 14], [14, 16],
        [11, 23], [12, 24], [23, 24]
    ];

    function drawSkeleton(landmarks) {
        if (!skeletonCanvas || !skeletonCtx || !clientWebcam) return;

<<<<<<< HEAD
        const w = clientWebcam.videoWidth || clientWebcam.clientWidth || 640;
        const h = clientWebcam.videoHeight || clientWebcam.clientHeight || 480;

        if (skeletonCanvas.width !== w || skeletonCanvas.height !== h) {
            skeletonCanvas.width = w;
            skeletonCanvas.height = h;
        }

        skeletonCtx.clearRect(0, 0, w, h);
        if (!landmarks) return;

=======
        // Container visible dimensions
        const container = clientWebcam.parentElement;
        const containerW = (container ? container.clientWidth : 0) || clientWebcam.clientWidth || 640;
        const containerH = (container ? container.clientHeight : 0) || clientWebcam.clientHeight || 480;

        // Video intrinsic stream dimensions
        const videoW = clientWebcam.videoWidth || 640;
        const videoH = clientWebcam.videoHeight || 480;

        // Sync canvas internal resolution with CSS display size (1:1 mapping)
        if (skeletonCanvas.width !== containerW || skeletonCanvas.height !== containerH) {
            skeletonCanvas.width = containerW;
            skeletonCanvas.height = containerH;
        }

        skeletonCtx.clearRect(0, 0, containerW, containerH);
        if (!landmarks) return;

        // Calculate object-fit: cover scaling and cropping offsets
        const videoAspect = videoW / videoH;
        const containerAspect = containerW / containerH;
        let scale = 1, offsetX = 0, offsetY = 0;

        if (containerAspect > videoAspect) {
            // Container is wider: video is scaled to width and cropped top/bottom
            scale = containerW / videoW;
            offsetY = (containerH - videoH * scale) / 2;
        } else {
            // Container is taller: video is scaled to height and cropped left/right
            scale = containerH / videoH;
            offsetX = (containerW - videoW * scale) / 2;
        }

        // Coordinate transformer: converts normalized (0..1) coords to exact pixel position on canvas
        function mapCoord(normX, normY) {
            // Backend process_base64_image flips horizontally (display_frame = cv2.flip(frame, 1))
            // So landmarks returned are already mirrored for front camera display
            const px = normX * videoW * scale + offsetX;
            const py = normY * videoH * scale + offsetY;
            return { x: px, y: py };
        }

>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        // Draw Pose Connections
        if (landmarks.pose && landmarks.pose.length > 0) {
            skeletonCtx.strokeStyle = 'rgba(99, 102, 241, 0.85)';
            skeletonCtx.lineWidth = 3;
            skeletonCtx.shadowColor = '#6366f1';
            skeletonCtx.shadowBlur = 8;

            for (const [startIdx, endIdx] of POSE_CONNECTIONS) {
                const p1 = landmarks.pose[startIdx];
                const p2 = landmarks.pose[endIdx];
                if (p1 && p2 && (p1.v === undefined || p1.v > 0.35) && (p2.v === undefined || p2.v > 0.35)) {
<<<<<<< HEAD
                    skeletonCtx.beginPath();
                    skeletonCtx.moveTo(p1.x * w, p1.y * h);
                    skeletonCtx.lineTo(p2.x * w, p2.y * h);
=======
                    const c1 = mapCoord(p1.x, p1.y);
                    const c2 = mapCoord(p2.x, p2.y);
                    skeletonCtx.beginPath();
                    skeletonCtx.moveTo(c1.x, c1.y);
                    skeletonCtx.lineTo(c2.x, c2.y);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                    skeletonCtx.stroke();
                }
            }

            // Pose Joints
            skeletonCtx.shadowBlur = 4;
            for (let i = 11; i <= 16; i++) {
                const p = landmarks.pose[i];
                if (p && (p.v === undefined || p.v > 0.35)) {
<<<<<<< HEAD
                    skeletonCtx.beginPath();
                    skeletonCtx.arc(p.x * w, p.y * h, 4.5, 0, 2 * Math.PI);
=======
                    const c = mapCoord(p.x, p.y);
                    skeletonCtx.beginPath();
                    skeletonCtx.arc(c.x, c.y, 4.5, 0, 2 * Math.PI);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                    skeletonCtx.fillStyle = '#c084fc';
                    skeletonCtx.fill();
                }
            }
        }

<<<<<<< HEAD
        function drawHand(points, lineColor, dotColor) {
            if (!points || points.length === 0) return;
            skeletonCtx.strokeStyle = lineColor;
            skeletonCtx.lineWidth = 2.5;
            skeletonCtx.shadowColor = lineColor;
            skeletonCtx.shadowBlur = 6;
=======
        function drawHand(points, lineColor, dotColor, glowColor) {
            if (!points || points.length === 0) return;
            skeletonCtx.strokeStyle = lineColor;
            skeletonCtx.lineWidth = 3;
            skeletonCtx.shadowColor = glowColor || lineColor;
            skeletonCtx.shadowBlur = 8;
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9

            for (const [s, e] of HAND_CONNECTIONS) {
                const p1 = points[s];
                const p2 = points[e];
                if (p1 && p2) {
<<<<<<< HEAD
                    skeletonCtx.beginPath();
                    skeletonCtx.moveTo(p1.x * w, p1.y * h);
                    skeletonCtx.lineTo(p2.x * w, p2.y * h);
=======
                    const c1 = mapCoord(p1.x, p1.y);
                    const c2 = mapCoord(p2.x, p2.y);
                    skeletonCtx.beginPath();
                    skeletonCtx.moveTo(c1.x, c1.y);
                    skeletonCtx.lineTo(c2.x, c2.y);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                    skeletonCtx.stroke();
                }
            }

<<<<<<< HEAD
            skeletonCtx.shadowBlur = 3;
            for (const p of points) {
                if (!p) continue;
                skeletonCtx.beginPath();
                skeletonCtx.arc(p.x * w, p.y * h, 3.5, 0, 2 * Math.PI);
=======
            skeletonCtx.shadowBlur = 4;
            for (let idx = 0; idx < points.length; idx++) {
                const p = points[idx];
                if (!p) continue;
                const c = mapCoord(p.x, p.y);
                skeletonCtx.beginPath();
                const radius = (idx === 4 || idx === 8 || idx === 12 || idx === 16 || idx === 20) ? 5 : 3.5;
                skeletonCtx.arc(c.x, c.y, radius, 0, 2 * Math.PI);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                skeletonCtx.fillStyle = dotColor;
                skeletonCtx.fill();
            }
        }

<<<<<<< HEAD
        // Left Hand (Cyan)
        if (landmarks.leftHand && landmarks.leftHand.length > 0) {
            drawHand(landmarks.leftHand, 'rgba(6, 182, 212, 0.9)', '#67e8f9');
        }

        // Right Hand (Neon Green)
        if (landmarks.rightHand && landmarks.rightHand.length > 0) {
            drawHand(landmarks.rightHand, 'rgba(16, 185, 129, 0.9)', '#34d399');
=======
        // Left Hand (Cyan glow)
        if (landmarks.leftHand && landmarks.leftHand.length > 0) {
            drawHand(landmarks.leftHand, 'rgba(6, 182, 212, 0.95)', '#67e8f9', '#06b6d4');
        }

        // Right Hand (Neon Green glow)
        if (landmarks.rightHand && landmarks.rightHand.length > 0) {
            drawHand(landmarks.rightHand, 'rgba(16, 185, 129, 0.95)', '#34d399', '#10b981');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        }
    }

    function startFrameCapture() {
        if (frameCaptureInterval) clearInterval(frameCaptureInterval);

        frameCaptureInterval = setInterval(async () => {
            if (!isTranslationActive || !isCameraRunning || currentStreamMode !== 'client') return;
            if (!clientWebcam || clientWebcam.paused || clientWebcam.ended || isFrameSending) return;

            isFrameSending = true;
            try {
                captureCanvas.width = 480;
                captureCanvas.height = 360;
                captureCtx.drawImage(clientWebcam, 0, 0, captureCanvas.width, captureCanvas.height);
                const b64 = captureCanvas.toDataURL('image/jpeg', 0.65);

                const response = await fetch(`${serverUrl}/api/process_frame`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ image: b64 })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        updateUI(data.prediction, data.confidence, data.sentence);
                        if (data.landmarks) {
                            drawSkeleton(data.landmarks);
                        }
                    }
                }
            } catch (err) {
                console.debug("Frame processing tick skipped:", err);
            } finally {
                isFrameSending = false;
            }
        }, 100); // 10 FPS real-time
    }

    function stopFrameCapture() {
        if (frameCaptureInterval) {
            clearInterval(frameCaptureInterval);
            frameCaptureInterval = null;
        }
        isFrameSending = false;
    }

    // Switch between Browser Webcam (Client) and OpenCV Server Stream (/video_feed)
    function switchStreamMode(mode) {
        currentStreamMode = mode;
        if (mode === 'server') {
            stopFrameCapture();
            stopStreamTracks();
            isCameraRunning = true;
            if (clientWebcam) clientWebcam.style.display = 'none';
            if (skeletonCanvas) skeletonCanvas.style.display = 'none';
            if (flaskStream) {
                flaskStream.src = `${serverUrl}/video_feed?t=${Date.now()}`;
                flaskStream.style.display = 'block';
            }
            if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'none';
            if (scannerHud) scannerHud.style.display = 'block';
            if (btnCameraPower) btnCameraPower.classList.add('active');
            if (iconCamPower) iconCamPower.className = 'fa-solid fa-video';

<<<<<<< HEAD
            if (streamSourceText) streamSourceText.textContent = 'กล้อง OpenCV';
=======
            if (streamSourceText) streamSourceText.textContent = 'à¸à¸¥à¹‰à¸­à¸‡ OpenCV';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            if (streamSourceIcon) streamSourceIcon.className = 'fa-solid fa-server';
            statusText.textContent = 'SERVER STREAM (OpenCV)';
            statusDot.className = 'indicator-dot active';
            statusDot.style.backgroundColor = '#6366f1';
            statusDot.style.boxShadow = '0 0 8px #6366f1';

            if (apiInterval) clearInterval(apiInterval);
            apiInterval = setInterval(pollBackendPrediction, 250);

<<<<<<< HEAD
            showToast('สลับไปยังกล้องเซิร์ฟเวอร์ OpenCV Direct เรียบร้อย');
=======
            showToast('à¸ªà¸¥à¸±à¸šà¹„à¸›à¸¢à¸±à¸‡à¸à¸¥à¹‰à¸­à¸‡à¹€à¸‹à¸´à¸£à¹Œà¸Ÿà¹€à¸§à¸­à¸£à¹Œ OpenCV Direct à¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        } else {
            if (flaskStream) {
                flaskStream.src = '';
                flaskStream.style.display = 'none';
            }
            if (clientWebcam) clientWebcam.style.display = 'block';
            if (skeletonCanvas) skeletonCanvas.style.display = 'block';
<<<<<<< HEAD
            if (streamSourceText) streamSourceText.textContent = 'กล้องเว็บ';
=======
            if (streamSourceText) streamSourceText.textContent = 'à¸à¸¥à¹‰à¸­à¸‡à¹€à¸§à¹‡à¸š';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            if (streamSourceIcon) streamSourceIcon.className = 'fa-solid fa-desktop';

            if (apiInterval) clearInterval(apiInterval);
            startClientWebcam(currentFacingMode);
<<<<<<< HEAD
            showToast('สลับไปยังกล้องเบราว์เซอร์ เรียบร้อย');
=======
            showToast('à¸ªà¸¥à¸±à¸šà¹„à¸›à¸¢à¸±à¸‡à¸à¸¥à¹‰à¸­à¸‡à¹€à¸šà¸£à¸²à¸§à¹Œà¹€à¸‹à¸­à¸£à¹Œ à¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
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
        }
    }

    // Simulate predictions for Demo Mode (only if completely offline / local file)
    function startMockPredictions() {
        if (mockInterval) clearInterval(mockInterval);

        let lastMockWord = "";

        mockInterval = setInterval(() => {
            if (!isTranslationActive || !isCameraRunning) return;

            if (Math.random() > 0.35) {
                const randomWord = mockWords[Math.floor(Math.random() * mockWords.length)];
                const randomConfidence = (88 + Math.random() * 11.5).toFixed(1);

                if (randomWord !== lastMockWord) {
                    lastMockWord = randomWord;

                    if (mockSentence.length === 0 || mockSentence[mockSentence.length - 1] !== randomWord) {
                        mockSentence.push(randomWord);
                        if (mockSentence.length > 8) mockSentence.shift();
                    }
                }

                updateUI(randomWord, `${randomConfidence}%`, mockSentence.join(' '));
            } else {
<<<<<<< HEAD
                updateUI("รอกลุ่มท่าทาง...", "0.0%", mockSentence.join(' ') || "...");
=======
                updateUI("à¸£à¸­à¸à¸¥à¸¸à¹ˆà¸¡à¸—à¹ˆà¸²à¸—à¸²à¸‡...", "0.0%", mockSentence.join(' ') || "...");
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            }
        }, 2200);
    }

    // Update UI Elements with smooth animation feedback
    let prevWord = "";
    function updateUI(word, confidence, sentence) {
<<<<<<< HEAD
        if (word !== prevWord && word !== "รอกลุ่มท่าทาง..." && word !== "กำลังรอสัญญาณมือ...") {
=======
        if (word !== prevWord && word !== "à¸£à¸­à¸à¸¥à¸¸à¹ˆà¸¡à¸—à¹ˆà¸²à¸—à¸²à¸‡..." && word !== "à¸à¸³à¸¥à¸±à¸‡à¸£à¸­à¸ªà¸±à¸à¸à¸²à¸“à¸¡à¸·à¸­...") {
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            predictionWord.style.transform = 'scale(1.08)';
            predictionWord.style.transition = 'transform 0.15s ease-out';
            setTimeout(() => {
                predictionWord.style.transform = 'scale(1)';
            }, 150);

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
            if (action === 'clear') {
                mockSentence = [];
<<<<<<< HEAD
                updateUI("ล้างประโยคแล้ว", "0.0%", "...");
                showToast('ล้างประโยคทั้งหมดสำเร็จ');
            } else if (action === 'backspace') {
                if (mockSentence.length > 0) {
                    mockSentence.pop();
                    updateUI("ลบคำล่าสุดแล้ว", "0.0%", mockSentence.join(' ') || "...");
                    showToast('ลบคำล่าสุดเรียบร้อย');
=======
                updateUI("à¸¥à¹‰à¸²à¸‡à¸›à¸£à¸°à¹‚à¸¢à¸„à¹à¸¥à¹‰à¸§", "0.0%", "...");
                showToast('à¸¥à¹‰à¸²à¸‡à¸›à¸£à¸°à¹‚à¸¢à¸„à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”à¸ªà¸³à¹€à¸£à¹‡à¸ˆ');
            } else if (action === 'backspace') {
                if (mockSentence.length > 0) {
                    mockSentence.pop();
                    updateUI("à¸¥à¸šà¸„à¸³à¸¥à¹ˆà¸²à¸ªà¸¸à¸”à¹à¸¥à¹‰à¸§", "0.0%", mockSentence.join(' ') || "...");
                    showToast('à¸¥à¸šà¸„à¸³à¸¥à¹ˆà¸²à¸ªà¸¸à¸”à¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                }
            }
        }
    }

    // Camera Event Listeners
    if (btnClear) btnClear.addEventListener('click', () => handleControlAction('clear'));
    if (btnBackspace) btnBackspace.addEventListener('click', () => handleControlAction('backspace'));
    if (btnFlipCam) btnFlipCam.addEventListener('click', flipCamera);
    if (btnFlipCamBottom) btnFlipCamBottom.addEventListener('click', flipCamera);
    if (btnCameraPower) btnCameraPower.addEventListener('click', toggleCameraPower);
    if (btnStreamSource) {
        btnStreamSource.addEventListener('click', () => {
            const nextMode = currentStreamMode === 'client' ? 'server' : 'client';
            switchStreamMode(nextMode);
        });
    }
    if (btnStartCamera) btnStartCamera.addEventListener('click', async () => {
        // On first camera open: also check backend connection
        if (!isBackendConnected && !isLocalFile) {
            try {
                const response = await fetch(`${serverUrl}/api/prediction`, { method: 'GET' });
                if (response.ok) isBackendConnected = true;
            } catch (err) {
                isBackendConnected = false;
            }
        }
        startClientWebcam(currentFacingMode);
    });

    // Speak Button Listeners
    if (btnSpeakSentence) {
        btnSpeakSentence.addEventListener('click', () => {
            const textToSpeak = sentenceOutput.textContent !== '...' ? sentenceOutput.textContent : predictionWord.textContent;
            speakText(textToSpeak);
        });
    }
    if (btnSpeakInline) {
        btnSpeakInline.addEventListener('click', () => {
            const textToSpeak = sentenceOutput.textContent !== '...' ? sentenceOutput.textContent : predictionWord.textContent;
            speakText(textToSpeak);
        });
    }

    // Toggle Translate Visibility
    if (btnToggleTranslate) {
        btnToggleTranslate.addEventListener('click', () => {
            isTranslationActive = !isTranslationActive;

            if (isTranslationActive) {
                transOverlay.classList.remove('hidden');
                btnToggleTranslate.style.backgroundColor = '#ffffff';
                btnToggleTranslate.style.boxShadow = '0 10px 20px rgba(255, 255, 255, 0.15)';
                btnToggleTranslate.querySelector('i').style.color = '#0a0b10';
<<<<<<< HEAD
                showToast('เปิดระบบตรวจจับภาษามือ');
=======
                showToast('à¹€à¸›à¸´à¸”à¸£à¸°à¸šà¸šà¸•à¸£à¸§à¸ˆà¸ˆà¸±à¸šà¸ à¸²à¸©à¸²à¸¡à¸·à¸­');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            } else {
                transOverlay.classList.add('hidden');
                btnToggleTranslate.style.backgroundColor = '#ef4444';
                btnToggleTranslate.style.boxShadow = '0 10px 20px rgba(239, 68, 68, 0.3)';
                btnToggleTranslate.querySelector('i').style.color = '#ffffff';
<<<<<<< HEAD
                showToast('ปิดระบบตรวจจับภาษามือชั่วคราว');
=======
                showToast('à¸›à¸´à¸”à¸£à¸°à¸šà¸šà¸•à¸£à¸§à¸ˆà¸ˆà¸±à¸šà¸ à¸²à¸©à¸²à¸¡à¸·à¸­à¸Šà¸±à¹ˆà¸§à¸„à¸£à¸²à¸§');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            }
        });
    }

    // Mobile Fullscreen Button
    if (btnMobileFullscreen) {
        btnMobileFullscreen.addEventListener('click', () => toggleTheaterMode());
    }

    // ==========================================================================
    // MOBILE QR CODE & CONNECT MODAL
    // ==========================================================================
    async function openMobileModal() {
        if (!mobileModalOverlay) return;
        mobileModalOverlay.classList.add('open');
        mobileModalOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';

        // Fetch server LAN IP information
        let mobileUrl = window.location.origin.replace('http://', 'https://').replace(':5000', '') + ':5000' + window.location.pathname;
        try {
            if (!isLocalFile) {
                const res = await fetch(`${serverUrl}/api/server-info`);
                if (res.ok) {
                    const info = await res.json();
                    // Always use HTTPS URL so mobile camera works
                    mobileUrl = info.https_url + (window.location.pathname !== '/' ? window.location.pathname : '') || mobileUrl;
                }
            }
        } catch (e) {
            console.log("Using current origin for mobile URL:", e);
        }

        if (mobileUrlInput) mobileUrlInput.value = mobileUrl;

        // Generate QR code using API with fallback
        if (qrCodeImage && qrLoading) {
            qrLoading.style.display = 'flex';
            qrCodeImage.style.display = 'none';

            const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=260x260&margin=8&data=${encodeURIComponent(mobileUrl)}`;
            qrCodeImage.src = qrApiUrl;
            qrCodeImage.onload = () => {
                qrLoading.style.display = 'none';
                qrCodeImage.style.display = 'block';
            };
            qrCodeImage.onerror = () => {
<<<<<<< HEAD
                qrLoading.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ไม่สามารถโหลดรูป QR Code ได้ (พิมพ์ลิงก์ด้านล่างลงในมือถือ)';
=======
                qrLoading.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> à¹„à¸¡à¹ˆà¸ªà¸²à¸¡à¸²à¸£à¸–à¹‚à¸«à¸¥à¸”à¸£à¸¹à¸› QR Code à¹„à¸”à¹‰ (à¸žà¸´à¸¡à¸žà¹Œà¸¥à¸´à¸‡à¸à¹Œà¸”à¹‰à¸²à¸™à¸¥à¹ˆà¸²à¸‡à¸¥à¸‡à¹ƒà¸™à¸¡à¸·à¸­à¸–à¸·à¸­)';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            };
        }
    }

    function closeMobileModal() {
        if (!mobileModalOverlay) return;
        mobileModalOverlay.classList.remove('open');
        mobileModalOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    if (btnOpenMobileModal) btnOpenMobileModal.addEventListener('click', openMobileModal);
    if (btnCloseMobileModal) btnCloseMobileModal.addEventListener('click', closeMobileModal);
    if (mobileModalOverlay) {
        mobileModalOverlay.addEventListener('click', (e) => {
            if (e.target === mobileModalOverlay) closeMobileModal();
        });
    }

    if (btnCopyUrl && mobileUrlInput) {
        btnCopyUrl.addEventListener('click', async () => {
            try {
                await navigator.clipboard.writeText(mobileUrlInput.value);
<<<<<<< HEAD
                showToast('คัดลอกลิงก์สำหรับมือถือเรียบร้อยแล้ว');
            } catch (err) {
                mobileUrlInput.select();
                document.execCommand('copy');
                showToast('คัดลอกลิงก์เรียบร้อย');
=======
                showToast('à¸„à¸±à¸”à¸¥à¸­à¸à¸¥à¸´à¸‡à¸à¹Œà¸ªà¸³à¸«à¸£à¸±à¸šà¸¡à¸·à¸­à¸–à¸·à¸­à¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢à¹à¸¥à¹‰à¸§');
            } catch (err) {
                mobileUrlInput.select();
                document.execCommand('copy');
                showToast('à¸„à¸±à¸”à¸¥à¸­à¸à¸¥à¸´à¸‡à¸à¹Œà¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            }
        });
    }

    // ==========================================================================
    // AUTHENTICATION & USER MANAGEMENT MODULE
    // ==========================================================================

    // Auth DOM Elements
    const authModalOverlay = document.getElementById('auth-modal-overlay');
    const btnCloseAuthModal = document.getElementById('btn-close-auth-modal');
    const tabLogin = document.getElementById('tab-login');
    const tabRegister = document.getElementById('tab-register');
    const formLogin = document.getElementById('form-login');
    const formRegister = document.getElementById('form-register');
    const authModalTitle = document.getElementById('auth-modal-title');
    const authModalSubtitle = document.getElementById('auth-modal-subtitle');
    const authAlert = document.getElementById('auth-alert');
    const authAlertText = document.getElementById('auth-alert-text');
    const authAlertIcon = document.getElementById('auth-alert-icon');
    const btnToggleLoginPwd = document.getElementById('btn-toggle-login-pwd');
    const btnToggleRegPwd = document.getElementById('btn-toggle-reg-pwd');
    const loginPwdInput = document.getElementById('login-password');
    const regPwdInput = document.getElementById('reg-password');
    const authButtonsGroup = document.getElementById('auth-buttons-group');
    const userProfileWidget = document.getElementById('user-profile-widget');
    const userPill = document.getElementById('user-pill');
    const userDisplayName = document.getElementById('user-display-name');
    const dropdownUsername = document.getElementById('dropdown-username');
    const dropdownEmail = document.getElementById('dropdown-email');
    const btnLogout = document.getElementById('btn-logout');
<<<<<<< HEAD
    const btnGive = document.getElementById('btn-give'); // เข้าสู่ระบบ button
    const btnPlan = document.getElementById('btn-plan'); // สมัครสมาชิก button
=======
    const btnGive = document.getElementById('btn-give'); // à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š button
    const btnPlan = document.getElementById('btn-plan'); // à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸ button
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    const btnSocialGoogle = document.getElementById('btn-social-google');
    const btnSocialGithub = document.getElementById('btn-social-github');

    // Supabase Client Integration
    const SUPABASE_URL = 'https://yotvhpskwnmhupvaxenf.supabase.co';
    const SUPABASE_ANON_KEY = 'sb_publishable_z8cNBJEv-QhG8ULD8yg63A_RdZeaXGa';
    let supabaseClient = null;
    if (window.supabase && typeof window.supabase.createClient === 'function') {
        try {
            supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        } catch (e) {
            console.warn("Supabase initialization error:", e);
        }
    }

    // Show Alert inside Auth Modal
    function showAuthAlert(message, type = 'error') {
        if (!authAlert) return;
        authAlert.className = `auth-alert ${type}`;
        authAlertText.textContent = message;
        if (type === 'error') {
            authAlertIcon.className = 'fa-solid fa-circle-exclamation';
        } else {
            authAlertIcon.className = 'fa-solid fa-circle-check';
        }
        authAlert.style.display = 'flex';
    }

    function hideAuthAlert() {
        if (authAlert) authAlert.style.display = 'none';
    }

    // Switch between Login and Register tabs
    function switchAuthTab(tab) {
        hideAuthAlert();
        if (tab === 'login') {
            tabLogin.classList.add('active');
            tabLogin.setAttribute('aria-selected', 'true');
            tabRegister.classList.remove('active');
            tabRegister.setAttribute('aria-selected', 'false');
            formLogin.style.display = 'flex';
            formRegister.style.display = 'none';
<<<<<<< HEAD
            authModalTitle.textContent = 'เข้าสู่ระบบ SignSubs';
            authModalSubtitle.textContent = 'เพื่อใช้งานระบบแปลภาษามือเรียลไทม์และบันทึกประวัติ';
=======
            authModalTitle.textContent = 'à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š SignSubs';
            authModalSubtitle.textContent = 'à¹€à¸žà¸·à¹ˆà¸­à¹ƒà¸Šà¹‰à¸‡à¸²à¸™à¸£à¸°à¸šà¸šà¹à¸›à¸¥à¸ à¸²à¸©à¸²à¸¡à¸·à¸­à¹€à¸£à¸µà¸¢à¸¥à¹„à¸—à¸¡à¹Œà¹à¸¥à¸°à¸šà¸±à¸™à¸—à¸¶à¸à¸›à¸£à¸°à¸§à¸±à¸•à¸´';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        } else {
            tabRegister.classList.add('active');
            tabRegister.setAttribute('aria-selected', 'true');
            tabLogin.classList.remove('active');
            tabLogin.setAttribute('aria-selected', 'false');
            formLogin.style.display = 'none';
            formRegister.style.display = 'flex';
<<<<<<< HEAD
            authModalTitle.textContent = 'สร้างบัญชี SignSubs ใหม่';
            authModalSubtitle.textContent = 'สมัครสมาชิกฟรีเพื่อเข้าถึงฟีเจอร์ตรวจจับภาษามือครบครัน';
=======
            authModalTitle.textContent = 'à¸ªà¸£à¹‰à¸²à¸‡à¸šà¸±à¸à¸Šà¸µ SignSubs à¹ƒà¸«à¸¡à¹ˆ';
            authModalSubtitle.textContent = 'à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸à¸Ÿà¸£à¸µà¹€à¸žà¸·à¹ˆà¸­à¹€à¸‚à¹‰à¸²à¸–à¸¶à¸‡à¸Ÿà¸µà¹€à¸ˆà¸­à¸£à¹Œà¸•à¸£à¸§à¸ˆà¸ˆà¸±à¸šà¸ à¸²à¸©à¸²à¸¡à¸·à¸­à¸„à¸£à¸šà¸„à¸£à¸±à¸™';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        }
    }

    // Open & Close Auth Modal
    function openAuthModal(tab = 'login') {
        switchAuthTab(tab);
        authModalOverlay.classList.add('open');
        authModalOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    function closeAuthModal() {
        authModalOverlay.classList.remove('open');
        authModalOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
        hideAuthAlert();
    }

    // Event listeners for opening modal
    if (btnGive) btnGive.addEventListener('click', () => openAuthModal('login'));
    if (btnPlan) btnPlan.addEventListener('click', () => openAuthModal('register'));
    if (btnCloseAuthModal) btnCloseAuthModal.addEventListener('click', closeAuthModal);

    // Close modal when clicking overlay background
    if (authModalOverlay) {
        authModalOverlay.addEventListener('click', (e) => {
            if (e.target === authModalOverlay) {
                closeAuthModal();
            }
        });
    }

    // Tab button listeners
    if (tabLogin) tabLogin.addEventListener('click', () => switchAuthTab('login'));
    if (tabRegister) tabRegister.addEventListener('click', () => switchAuthTab('register'));

    // Toggle password visibility helpers
    function setupPasswordToggle(button, input) {
        if (!button || !input) return;
        button.addEventListener('click', () => {
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            const icon = button.querySelector('i');
            if (icon) {
                icon.className = isPassword ? 'fa-regular fa-eye-slash' : 'fa-regular fa-eye';
            }
        });
    }
    setupPasswordToggle(btnToggleLoginPwd, loginPwdInput);
    setupPasswordToggle(btnToggleRegPwd, regPwdInput);

    // Apply User Logged-in State to UI
    function applyLoggedInUser(user) {
        if (authButtonsGroup) authButtonsGroup.style.display = 'none';
        if (userProfileWidget) userProfileWidget.style.display = 'block';
<<<<<<< HEAD
        if (userDisplayName) userDisplayName.textContent = user.username || user.name || 'ผู้ใช้งาน';
        if (dropdownUsername) dropdownUsername.textContent = user.username || user.name || 'ผู้ใช้งาน';
=======
        if (userDisplayName) userDisplayName.textContent = user.username || user.name || 'à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸‡à¸²à¸™';
        if (dropdownUsername) dropdownUsername.textContent = user.username || user.name || 'à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸‡à¸²à¸™';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        if (dropdownEmail) dropdownEmail.textContent = user.email || 'user@signsubs.ai';
    }

    // Apply User Logged-out State to UI
    function applyLoggedOutUser() {
        if (authButtonsGroup) authButtonsGroup.style.display = 'flex';
        if (userProfileWidget) {
            userProfileWidget.style.display = 'none';
            userProfileWidget.classList.remove('active');
        }
        localStorage.removeItem('signsubs_current_user');
        sessionStorage.removeItem('signsubs_current_user');
    }

    // Toggle User Profile Dropdown
    if (userPill) {
        userPill.addEventListener('click', (e) => {
            e.stopPropagation();
            userProfileWidget.classList.toggle('active');
        });
    }

    // Close Dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (userProfileWidget && !userProfileWidget.contains(e.target)) {
            userProfileWidget.classList.remove('active');
        }
    });

    // Handle Logout
    if (btnLogout) {
        btnLogout.addEventListener('click', async () => {
            try {
                if (!isLocalFile) {
                    await fetch(`${serverUrl}/api/logout`, { method: 'POST' });
                }
            } catch (err) {
                console.log("Logout backend request bypassed:", err);
            }
            applyLoggedOutUser();
<<<<<<< HEAD
            showToast('ออกจากระบบเรียบร้อยแล้ว');
=======
            showToast('à¸­à¸­à¸à¸ˆà¸²à¸à¸£à¸°à¸šà¸šà¹€à¸£à¸µà¸¢à¸šà¸£à¹‰à¸­à¸¢à¹à¸¥à¹‰à¸§');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        });
    }
    //
    function applyLoggedInUser(user) {
        if (authButtonsGroup) authButtonsGroup.style.display = 'none';
        if (userProfileWidget) userProfileWidget.style.display = 'block';

<<<<<<< HEAD
        if (userDisplayName) userDisplayName.textContent = user.username || 'ผู้ใช้งาน';
        if (dropdownUsername) dropdownUsername.textContent = user.username || 'ผู้ใช้งาน';
        if (dropdownEmail) dropdownEmail.textContent = user.email || 'user@signsubs.ai';
        console.log(user);

        // --- ควบคุมการแสดงปุ่ม ADMIN ตาม Role ---
        const adminMenuItem = document.getElementById('admin-menu-item');
        if (adminMenuItem) {
            if (user.role === 'admin') {
                adminMenuItem.style.display = 'flex'; // หรือ 'block' ตามดีไซน์เดิมของคุณ
            } else {
                adminMenuItem.style.display = 'none'; // ซ่อนถ้าไม่ใช่แอดมิน
=======
        if (userDisplayName) userDisplayName.textContent = user.username || 'à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸‡à¸²à¸™';
        if (dropdownUsername) dropdownUsername.textContent = user.username || 'à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸‡à¸²à¸™';
        if (dropdownEmail) dropdownEmail.textContent = user.email || 'user@signsubs.ai';
        console.log(user);

        // --- à¸„à¸§à¸šà¸„à¸¸à¸¡à¸à¸²à¸£à¹à¸ªà¸”à¸‡à¸›à¸¸à¹ˆà¸¡ ADMIN à¸•à¸²à¸¡ Role ---
        const adminMenuItem = document.getElementById('admin-menu-item');
        if (adminMenuItem) {
            if (user.role === 'admin') {
                adminMenuItem.style.display = 'flex'; // à¸«à¸£à¸·à¸­ 'block' à¸•à¸²à¸¡à¸”à¸µà¹„à¸‹à¸™à¹Œà¹€à¸”à¸´à¸¡à¸‚à¸­à¸‡à¸„à¸¸à¸“
            } else {
                adminMenuItem.style.display = 'none'; // à¸‹à¹ˆà¸­à¸™à¸–à¹‰à¸²à¹„à¸¡à¹ˆà¹ƒà¸Šà¹ˆà¹à¸­à¸”à¸¡à¸´à¸™
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            }
        }
    }

    // Handle Login Submit
    if (formLogin) {
        formLogin.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAuthAlert();
            const usernameInput = document.getElementById('login-username').value.trim();
            const passwordInput = document.getElementById('login-password').value;
            const rememberMe = document.getElementById('login-remember')?.checked;
            const submitBtn = document.getElementById('btn-submit-login');

            if (!usernameInput || !passwordInput) {
<<<<<<< HEAD
                showAuthAlert('กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบถ้วน');
=======
                showAuthAlert('à¸à¸£à¸¸à¸“à¸²à¸à¸£à¸­à¸à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¹à¸¥à¸°à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¹ƒà¸«à¹‰à¸„à¸£à¸šà¸–à¹‰à¸§à¸™');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                return;
            }

            submitBtn.disabled = true;
<<<<<<< HEAD
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังตรวจสอบ...';
=======
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> à¸à¸³à¸¥à¸±à¸‡à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸š...';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9

            let loginSuccess = false;
            let loggedInUserData = null;

            // Attempt Supabase Login first if available
            if (supabaseClient) {
                try {
                    const { data: supaUsers, error: supaErr } = await supabaseClient
                        .from('users')
                        .select('*')
                        .or(`username.eq.${usernameInput},email.eq.${usernameInput}`)
                        .eq('password', passwordInput)
                        .limit(1);

                    if (!supaErr && supaUsers && supaUsers.length > 0) {
                        loginSuccess = true;
                        loggedInUserData = {
                            username: supaUsers[0].username || usernameInput,
                            email: supaUsers[0].email || (usernameInput.includes('@') ? usernameInput : `${usernameInput}@signsubs.ai`),
                            role: supaUsers[0].role || 'user'
                        };
                    }
                } catch (sbLoginErr) {
                    console.warn("Supabase login query skipped:", sbLoginErr);
                }
            }

            // Attempt Backend Login if not authenticated via Supabase and not local file
            if (!loginSuccess && !isLocalFile) {
                try {
<<<<<<< HEAD
                    // ตรวจสอบสถานะการเข้าสู่ระบบผ่าน Supabase
                    if (!loginSuccess) {
                        showAuthAlert('ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
=======
                    // à¸•à¸£à¸§à¸ˆà¸ªà¸­à¸šà¸ªà¸–à¸²à¸™à¸°à¸à¸²à¸£à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸šà¸œà¹ˆà¸²à¸™ Supabase
                    if (!loginSuccess) {
                        showAuthAlert('à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸«à¸£à¸·à¸­à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¹„à¸¡à¹ˆà¸–à¸¹à¸à¸•à¹‰à¸­à¸‡');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š</span> <i class="fa-solid fa-arrow-right"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                        return;
                    }
                    const data = await res.json();
                    if (res.ok && data.success) {
                        loginSuccess = true;
                        loggedInUserData = data.user;
                    } else if (res.status === 401) {
<<<<<<< HEAD
                        showAuthAlert(data.message || 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
=======
                        showAuthAlert(data.message || 'à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸«à¸£à¸·à¸­à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¹„à¸¡à¹ˆà¸–à¸¹à¸à¸•à¹‰à¸­à¸‡');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š</span> <i class="fa-solid fa-arrow-right"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                        return;
                    }
                } catch (err) {
                    console.log("Backend login unavailable, trying local fallback:", err);
                }
            }

            // Fallback: Local Authentication (Mock / Frontend mode)
            if (!loginSuccess) {
                const storedUsers = JSON.parse(localStorage.getItem('signsubs_users') || '[]');
                const foundUser = storedUsers.find(u =>
                    (u.username.toLowerCase() === usernameInput.toLowerCase() ||
                        u.email.toLowerCase() === usernameInput.toLowerCase()) &&
                    u.password === passwordInput
                );

                if (foundUser) {
                    loginSuccess = true;
                    loggedInUserData = { username: foundUser.username, email: foundUser.email };
                } else if (passwordInput.length >= 4) {
                    // Demo auto-accept if password is provided
                    loginSuccess = true;
                    loggedInUserData = {
                        username: usernameInput.includes('@') ? usernameInput.split('@')[0] : usernameInput,
                        email: usernameInput.includes('@') ? usernameInput : `${usernameInput}@signsubs.ai`
                    };
                } else {
<<<<<<< HEAD
                    showAuthAlert('รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
=======
                    showAuthAlert('à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¸•à¹‰à¸­à¸‡à¸¡à¸µà¸„à¸§à¸²à¸¡à¸¢à¸²à¸§à¸­à¸¢à¹ˆà¸²à¸‡à¸™à¹‰à¸­à¸¢ 4 à¸•à¸±à¸§à¸­à¸±à¸à¸©à¸£');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š</span> <i class="fa-solid fa-arrow-right"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                    return;
                }
            }

            if (loginSuccess && loggedInUserData) {
                if (rememberMe) {
                    localStorage.setItem('signsubs_current_user', JSON.stringify(loggedInUserData));
                } else {
                    sessionStorage.setItem('signsubs_current_user', JSON.stringify(loggedInUserData));
                }

                applyLoggedInUser(loggedInUserData);
                closeAuthModal();
<<<<<<< HEAD
                showToast(`ยินดีต้อนรับคุณ ${loggedInUserData.username} เข้าสู่ระบบสำเร็จ`);
=======
                showToast(`à¸¢à¸´à¸™à¸”à¸µà¸•à¹‰à¸­à¸™à¸£à¸±à¸šà¸„à¸¸à¸“ ${loggedInUserData.username} à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸šà¸ªà¸³à¹€à¸£à¹‡à¸ˆ`);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                formLogin.reset();
            }

            submitBtn.disabled = false;
<<<<<<< HEAD
            submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
=======
            submitBtn.innerHTML = '<span>à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸š</span> <i class="fa-solid fa-arrow-right"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        });
    }

    // Handle Register Submit
    if (formRegister) {
        formRegister.addEventListener('submit', async (e) => {
            e.preventDefault();
            hideAuthAlert();

            const username = document.getElementById('reg-username').value.trim();
            const email = document.getElementById('reg-email').value.trim();
            const password = document.getElementById('reg-password').value;
            const confirmPassword = document.getElementById('reg-confirm-password').value;
            const submitBtn = document.getElementById('btn-submit-register');

            if (username.length < 3) {
<<<<<<< HEAD
                showAuthAlert('ชื่อผู้ใช้งานต้องมีความยาวอย่างน้อย 3 ตัวอักษร');
=======
                showAuthAlert('à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸‡à¸²à¸™à¸•à¹‰à¸­à¸‡à¸¡à¸µà¸„à¸§à¸²à¸¡à¸¢à¸²à¸§à¸­à¸¢à¹ˆà¸²à¸‡à¸™à¹‰à¸­à¸¢ 3 à¸•à¸±à¸§à¸­à¸±à¸à¸©à¸£');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                return;
            }

            if (password.length < 6) {
<<<<<<< HEAD
                showAuthAlert('รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร');
=======
                showAuthAlert('à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¸•à¹‰à¸­à¸‡à¸¡à¸µà¸„à¸§à¸²à¸¡à¸¢à¸²à¸§à¸­à¸¢à¹ˆà¸²à¸‡à¸™à¹‰à¸­à¸¢ 6 à¸•à¸±à¸§à¸­à¸±à¸à¸©à¸£');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                return;
            }

            if (password !== confirmPassword) {
<<<<<<< HEAD
                showAuthAlert('รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน');
=======
                showAuthAlert('à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¹à¸¥à¸°à¸à¸²à¸£à¸¢à¸·à¸™à¸¢à¸±à¸™à¸£à¸«à¸±à¸ªà¸œà¹ˆà¸²à¸™à¹„à¸¡à¹ˆà¸•à¸£à¸‡à¸à¸±à¸™');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                return;
            }

            submitBtn.disabled = true;
<<<<<<< HEAD
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังสร้างบัญชี...';
=======
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> à¸à¸³à¸¥à¸±à¸‡à¸ªà¸£à¹‰à¸²à¸‡à¸šà¸±à¸à¸Šà¸µ...';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9

            let regSuccess = false;
            let newUser = { username, email };
            let supabaseRegistered = false;

<<<<<<< HEAD
            // 1. Supabase Registration (จัดการบันทึกข้อมูลผู้ใช้ทั้งหมดที่นี่)
=======
            // 1. Supabase Registration (à¸ˆà¸±à¸”à¸à¸²à¸£à¸šà¸±à¸™à¸—à¸¶à¸à¸‚à¹‰à¸­à¸¡à¸¹à¸¥à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸—à¸±à¹‰à¸‡à¸«à¸¡à¸”à¸—à¸µà¹ˆà¸™à¸µà¹ˆ)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            if (supabaseClient) {
                try {
                    const { data: sbData, error: sbError } = await supabaseClient
                        .from('users')
                        .insert([{ username, email, password }]);

                    if (sbError) {
                        console.error('Supabase registration error:', sbError);
                        if (sbError.code === '23505' || (sbError.message && sbError.message.toLowerCase().includes('duplicate'))) {
<<<<<<< HEAD
                            showAuthAlert('ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบ Supabase แล้ว');
                        } else {
                            showAuthAlert('เกิดข้อผิดพลาด: ' + sbError.message);
                        }
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
                        return;
                    } else {
                        // สมัครสมาชิกสำเร็จ
=======
                            showAuthAlert('à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸«à¸£à¸·à¸­à¸­à¸µà¹€à¸¡à¸¥à¸™à¸µà¹‰à¸¡à¸µà¸­à¸¢à¸¹à¹ˆà¹ƒà¸™à¸£à¸°à¸šà¸š Supabase à¹à¸¥à¹‰à¸§');
                        } else {
                            showAuthAlert('à¹€à¸à¸´à¸”à¸‚à¹‰à¸­à¸œà¸´à¸”à¸žà¸¥à¸²à¸”: ' + sbError.message);
                        }
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸</span> <i class="fa-solid fa-user-check"></i>';
                        return;
                    } else {
                        // à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸à¸ªà¸³à¹€à¸£à¹‡à¸ˆ
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                        regSuccess = true;
                        window.location.href = 'index.html';
                    }
                } catch (sbErr) {
                    console.error("Supabase registration exception:", sbErr);
<<<<<<< HEAD
                    showAuthAlert('เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
                }
            } else {
                showAuthAlert('ไม่พบการเชื่อมต่อฐานข้อมูล Supabase');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
=======
                    showAuthAlert('à¹€à¸à¸´à¸”à¸‚à¹‰à¸­à¸œà¸´à¸”à¸žà¸¥à¸²à¸”à¹ƒà¸™à¸à¸²à¸£à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸</span> <i class="fa-solid fa-user-check"></i>';
                }
            } else {
                showAuthAlert('à¹„à¸¡à¹ˆà¸žà¸šà¸à¸²à¸£à¹€à¸Šà¸·à¹ˆà¸­à¸¡à¸•à¹ˆà¸­à¸à¸²à¸™à¸‚à¹‰à¸­à¸¡à¸¹à¸¥ Supabase');
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<span>à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸</span> <i class="fa-solid fa-user-check"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
            }

            // 3. Fallback: Local storage
            if (!regSuccess) {
                const storedUsers = JSON.parse(localStorage.getItem('signsubs_users') || '[]');
                const exists = storedUsers.some(u => u.username.toLowerCase() === username.toLowerCase() || u.email.toLowerCase() === email.toLowerCase());

                if (exists) {
<<<<<<< HEAD
                    showAuthAlert('ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบแล้ว');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
=======
                    showAuthAlert('à¸Šà¸·à¹ˆà¸­à¸œà¸¹à¹‰à¹ƒà¸Šà¹‰à¸«à¸£à¸·à¸­à¸­à¸µà¹€à¸¡à¸¥à¸™à¸µà¹‰à¸¡à¸µà¸­à¸¢à¸¹à¹ˆà¹ƒà¸™à¸£à¸°à¸šà¸šà¹à¸¥à¹‰à¸§');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸</span> <i class="fa-solid fa-user-check"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                    return;
                }

                storedUsers.push({ username, email, password });
                localStorage.setItem('signsubs_users', JSON.stringify(storedUsers));
                regSuccess = true;
            }

            if (regSuccess) {
                localStorage.setItem('signsubs_current_user', JSON.stringify(newUser));
                applyLoggedInUser(newUser);
                closeAuthModal();
<<<<<<< HEAD
                showToast(`สร้างบัญชีสำเร็จ ยินดีต้อนรับคุณ ${newUser.username}!`);
=======
                showToast(`à¸ªà¸£à¹‰à¸²à¸‡à¸šà¸±à¸à¸Šà¸µà¸ªà¸³à¹€à¸£à¹‡à¸ˆ à¸¢à¸´à¸™à¸”à¸µà¸•à¹‰à¸­à¸™à¸£à¸±à¸šà¸„à¸¸à¸“ ${newUser.username}!`);
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
                formRegister.reset();
            }

            submitBtn.disabled = false;
<<<<<<< HEAD
            submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
=======
            submitBtn.innerHTML = '<span>à¸ªà¸¡à¸±à¸„à¸£à¸ªà¸¡à¸²à¸Šà¸´à¸</span> <i class="fa-solid fa-user-check"></i>';
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        });
    }

    // Social Auth Demo (Google & GitHub)
    if (btnSocialGoogle) {
        btnSocialGoogle.addEventListener('click', () => {
            const googleUser = {
                username: 'Google User',
                email: 'user.google@gmail.com'
            };
            localStorage.setItem('signsubs_current_user', JSON.stringify(googleUser));
            applyLoggedInUser(googleUser);
            closeAuthModal();
<<<<<<< HEAD
            showToast('เข้าสู่ระบบด้วย Google Account สำเร็จ');
=======
            showToast('à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸šà¸”à¹‰à¸§à¸¢ Google Account à¸ªà¸³à¹€à¸£à¹‡à¸ˆ');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        });
    }

    if (btnSocialGithub) {
        btnSocialGithub.addEventListener('click', () => {
            const githubUser = {
                username: 'GitHub Dev',
                email: 'dev@github.com'
            };
            localStorage.setItem('signsubs_current_user', JSON.stringify(githubUser));
            applyLoggedInUser(githubUser);
            closeAuthModal();
<<<<<<< HEAD
            showToast('เข้าสู่ระบบด้วย GitHub Account สำเร็จ');
=======
            showToast('à¹€à¸‚à¹‰à¸²à¸ªà¸¹à¹ˆà¸£à¸°à¸šà¸šà¸”à¹‰à¸§à¸¢ GitHub Account à¸ªà¸³à¹€à¸£à¹‡à¸ˆ');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        });
    }

    // Check Existing Session on Page Load
    async function checkExistingAuth() {
        if (!isLocalFile) {
            try {
                const res = await fetch(`${serverUrl}/api/me`);
                if (res.ok) {
                    const data = await res.json();
                    if (data.authenticated && data.user) {
                        applyLoggedInUser(data.user);
                        return;
                    }
                }
            } catch (err) {
                // Ignore if backend not connected
            }
        }

        // Check local storage or session storage
        const savedUserStr = localStorage.getItem('signsubs_current_user') || sessionStorage.getItem('signsubs_current_user');
        if (savedUserStr) {
            try {
                const savedUser = JSON.parse(savedUserStr);
                applyLoggedInUser(savedUser);
            } catch (e) {
                localStorage.removeItem('signsubs_current_user');
            }
        }
    }

    checkExistingAuth();

<<<<<<< HEAD
    // Toggle Almost Fullscreen (เกือบเต็มจอ / Theater Mode)
=======
    // Toggle Almost Fullscreen (à¹€à¸à¸·à¸­à¸šà¹€à¸•à¹‡à¸¡à¸ˆà¸­ / Theater Mode)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    function toggleTheaterMode(forceState = null) {
        if (!cameraCard) return;
        const isTheater = forceState !== null ? forceState : !cameraCard.classList.contains('theater-mode');

        if (isTheater) {
            cameraCard.classList.add('theater-mode');
            if (expandIcon) expandIcon.className = 'fa-solid fa-compress';
<<<<<<< HEAD
            if (expandText) expandText.textContent = 'ย่อขนาด';
            if (btnExpandCam) btnExpandCam.title = 'ย่อขนาดจอกล้อง (Esc)';
            showToast('ขยายจอกล้องเกือบเต็มจอ (กด Esc หรือคลิกซ้ำเพื่อย่อ)');
        } else {
            cameraCard.classList.remove('theater-mode');
            if (expandIcon) expandIcon.className = 'fa-solid fa-expand';
            if (expandText) expandText.textContent = 'ขยายเกือบเต็มจอ';
            if (btnExpandCam) btnExpandCam.title = 'ขยายเกือบเต็มจอ (F)';
            showToast('ย่อจอกล้องสู่ขนาดปกติ');
=======
            if (expandText) expandText.textContent = 'à¸¢à¹ˆà¸­à¸‚à¸™à¸²à¸”';
            if (btnExpandCam) btnExpandCam.title = 'à¸¢à¹ˆà¸­à¸‚à¸™à¸²à¸”à¸ˆà¸­à¸à¸¥à¹‰à¸­à¸‡ (Esc)';
            showToast('à¸‚à¸¢à¸²à¸¢à¸ˆà¸­à¸à¸¥à¹‰à¸­à¸‡à¹€à¸à¸·à¸­à¸šà¹€à¸•à¹‡à¸¡à¸ˆà¸­ (à¸à¸” Esc à¸«à¸£à¸·à¸­à¸„à¸¥à¸´à¸à¸‹à¹‰à¸³à¹€à¸žà¸·à¹ˆà¸­à¸¢à¹ˆà¸­)');
        } else {
            cameraCard.classList.remove('theater-mode');
            if (expandIcon) expandIcon.className = 'fa-solid fa-expand';
            if (expandText) expandText.textContent = 'à¸‚à¸¢à¸²à¸¢à¹€à¸à¸·à¸­à¸šà¹€à¸•à¹‡à¸¡à¸ˆà¸­';
            if (btnExpandCam) btnExpandCam.title = 'à¸‚à¸¢à¸²à¸¢à¹€à¸à¸·à¸­à¸šà¹€à¸•à¹‡à¸¡à¸ˆà¸­ (F)';
            showToast('à¸¢à¹ˆà¸­à¸ˆà¸­à¸à¸¥à¹‰à¸­à¸‡à¸ªà¸¹à¹ˆà¸‚à¸™à¸²à¸”à¸›à¸à¸•à¸´');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        }
    }

    if (btnExpandCam) {
        btnExpandCam.addEventListener('click', () => toggleTheaterMode());
    }

    // ==========================================================================
<<<<<<< HEAD
    // About Our Website Modal System (เกี่ยวกับเว็บของเรา)
=======
    // About Our Website Modal System (à¹€à¸à¸µà¹ˆà¸¢à¸§à¸à¸±à¸šà¹€à¸§à¹‡à¸šà¸‚à¸­à¸‡à¹€à¸£à¸²)
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
    // ==========================================================================
    const aboutModalOverlay = document.getElementById('about-modal-overlay');
    const btnCloseAboutModal = document.getElementById('btn-close-about-modal');
    const btnAboutCloseFooter = document.getElementById('btn-about-close-footer');
    const btnAboutStartCam = document.getElementById('btn-about-start-cam');

    // Navigation and trigger buttons
    const navAbout = document.getElementById('nav-about');
    const navServices = document.getElementById('nav-services');
    const navTech = document.getElementById('nav-tech');
    const navGestures = document.getElementById('nav-gestures');
    const navContact = document.getElementById('nav-contact');
    const btnHeaderAbout = document.getElementById('btn-header-about');
    const btnHeroAbout = document.getElementById('btn-hero-about');
    const btnHeroStartCam = document.getElementById('btn-hero-start-cam');
    const cardAiTech = document.getElementById('card-ai-tech');
    const cardFeatures = document.getElementById('card-features');
    const btnPhone = document.getElementById('btn-phone');

    // Tab buttons and panes
    const aboutTabButtons = document.querySelectorAll('.about-tab-btn');
    const aboutTabPanes = document.querySelectorAll('.about-tab-pane');

    // Function to switch tab inside About Modal
    function switchAboutTab(targetTabId) {
        if (!targetTabId) return;

        aboutTabButtons.forEach(btn => {
            const tabId = btn.getAttribute('data-tab');
            if (tabId === targetTabId) {
                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
            } else {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            }
        });

        aboutTabPanes.forEach(pane => {
            if (pane.id === targetTabId) {
                pane.classList.add('active');
            } else {
                pane.classList.remove('active');
            }
        });

        const modalBody = document.querySelector('.about-modal-body');
        if (modalBody) modalBody.scrollTop = 0;
    }

    // Function to open About Modal with a specific tab
    function openAboutModal(targetTabId = 'tab-overview') {
        if (!aboutModalOverlay) return;
        switchAboutTab(targetTabId);
        aboutModalOverlay.classList.add('open');
        aboutModalOverlay.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    }

    // Function to close About Modal
    function closeAboutModal() {
        if (!aboutModalOverlay) return;
        aboutModalOverlay.classList.remove('open');
        aboutModalOverlay.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = '';
    }

    // Click listeners on tab buttons
    aboutTabButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = btn.getAttribute('data-tab');
            switchAboutTab(tabId);
        });
    });

    // Event listeners to open modal from various triggers
    if (navAbout) {
        navAbout.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-overview');
        });
    }

    if (navServices) {
        navServices.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-services');
        });
    }

    if (navTech) {
        navTech.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-tech');
        });
    }

    if (navGestures) {
        navGestures.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-guide');
        });
    }

    if (navContact) {
        navContact.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-contact');
        });
    }

    if (btnHeaderAbout) {
        btnHeaderAbout.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-overview');
        });
    }

    if (btnHeroAbout) {
        btnHeroAbout.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-overview');
        });
    }

    if (cardAiTech) {
        cardAiTech.addEventListener('click', () => openAboutModal('tab-tech'));
        cardAiTech.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openAboutModal('tab-tech');
            }
        });
    }

    if (cardFeatures) {
        cardFeatures.addEventListener('click', () => openAboutModal('tab-services'));
        cardFeatures.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                openAboutModal('tab-services');
            }
        });
    }

    if (btnPhone) {
        btnPhone.addEventListener('click', (e) => {
            e.preventDefault();
            openAboutModal('tab-contact');
        });
    }

    // Modal Close Triggers
    if (btnCloseAboutModal) {
        btnCloseAboutModal.addEventListener('click', closeAboutModal);
    }

    if (btnAboutCloseFooter) {
        btnAboutCloseFooter.addEventListener('click', closeAboutModal);
    }

    if (aboutModalOverlay) {
        aboutModalOverlay.addEventListener('click', (e) => {
            if (e.target === aboutModalOverlay) {
                closeAboutModal();
            }
        });
    }

    // CTA: Start Camera from Hero or inside About Modal
    function handleStartCameraCTA() {
        closeAboutModal();
        if (cameraCard) {
            cameraCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        if (!isCameraRunning) {
            startClientWebcam(currentFacingMode);
        } else {
<<<<<<< HEAD
            showToast('กล้องกำลังทำงานอยู่แล้ว พร้อมตรวจจับภาษามือ');
=======
            showToast('à¸à¸¥à¹‰à¸­à¸‡à¸à¸³à¸¥à¸±à¸‡à¸—à¸³à¸‡à¸²à¸™à¸­à¸¢à¸¹à¹ˆà¹à¸¥à¹‰à¸§ à¸žà¸£à¹‰à¸­à¸¡à¸•à¸£à¸§à¸ˆà¸ˆà¸±à¸šà¸ à¸²à¸©à¸²à¸¡à¸·à¸­');
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
        }
    }

    if (btnHeroStartCam) {
        btnHeroStartCam.addEventListener('click', handleStartCameraCTA);
    }

    if (btnAboutStartCam) {
        btnAboutStartCam.addEventListener('click', handleStartCameraCTA);
    }

    // Keyboard shortcuts: 'Escape' to close modals or exit fullscreen, 'F' to toggle fullscreen
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

        if (e.key === 'Escape') {
            if (aboutModalOverlay && aboutModalOverlay.classList.contains('open')) {
                closeAboutModal();
                return;
            }
            if (authModalOverlay && authModalOverlay.classList.contains('open')) {
                closeAuthModal();
                return;
            }
            if (cameraCard && cameraCard.classList.contains('theater-mode')) {
                toggleTheaterMode(false);
            }
        } else if (e.key === 'f' || e.key === 'F') {
            toggleTheaterMode();
        }
    });

    // Start App
    initCamera();
});

<<<<<<< HEAD
=======


    // =========================================================================
    // Dynamic Gestures Vocabulary Loader for index.html
    // =========================================================================
    let cachedGesturesList = [];
    const publicGesturesGrid = document.getElementById('public-gestures-grid');
    const gestureSearchInput = document.getElementById('gesture-search-input');
    const supportedGesturesCount = document.getElementById('supported-gestures-count');

    async function loadPublicGestures() {
        if (!publicGesturesGrid) return;
        try {
            const res = await fetch(`${serverUrl}/api/gestures`);
            if (!res.ok) throw new Error('Cannot load gestures');
            const data = await res.json();
            cachedGesturesList = data.gestures || [];
            if (supportedGesturesCount) {
                supportedGesturesCount.textContent = cachedGesturesList.length;
            }
            renderPublicGestures(cachedGesturesList);
        } catch (err) {
            console.warn('Failed to fetch public gestures:', err);
            publicGesturesGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 24px; color: var(--text-tertiary);">
                    <i class="fa-solid fa-circle-exclamation" style="font-size: 1.5rem; color: var(--accent-yellow); margin-bottom: 8px;"></i>
                    <p>ไม่สามารถโหลดคลังคำศัพท์จากเซิร์ฟเวอร์ได้ในขณะนี้</p>
                </div>
            `;
        }
    }

    function renderPublicGestures(gestures) {
        if (!publicGesturesGrid) return;
        if (!gestures || gestures.length === 0) {
            publicGesturesGrid.innerHTML = `
                <div style="grid-column: 1 / -1; text-align: center; padding: 24px; color: var(--text-tertiary);">
                    <p>ไม่พบคำศัพท์ที่ตรงกับการค้นหา</p>
                </div>
            `;
            return;
        }

        publicGesturesGrid.innerHTML = gestures.map((g, idx) => {
            const isNull = g.gesture_key === 'null_act' || g.name_th === 'null_act';
            const badgeIcon = isNull ? '<i class="fa-solid fa-hand-point-down"></i>' : (idx + 1);
            const titleTh = isNull ? 'Blank (ท่าพักมือ)' : g.name_th;
            const desc = isNull ? 'เอามือลงหรือไม่ทำท่าทาง เพื่อพักระบบชั่วคราว' : (g.description || `ภาษามือไทย: ${g.name_th}`);
            const categoryTag = g.category ? `<span style="font-size: 0.72rem; padding: 2px 6px; border-radius: 6px; background: rgba(99,102,241,0.15); color: #a5b4fc; margin-left: 6px;">${g.category}</span>` : '';

            return `
                <div class="gesture-badge-card ${isNull ? 'blank-card' : ''}" style="display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border); border-radius: 14px; transition: all 0.2s ease;">
                    <span class="gesture-code" style="min-width: 32px; height: 32px; display: inline-flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(99,102,241,0.2); color: #818cf8; font-weight: 700; font-size: 0.85rem;">
                        ${badgeIcon}
                    </span>
                    <div class="gesture-info" style="display: flex; flex-direction: column; gap: 2px;">
                        <strong style="font-size: 0.95rem; color: #fff;">${titleTh} ${categoryTag}</strong>
                        <span style="font-size: 0.8rem; color: var(--text-secondary);">${desc}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    if (gestureSearchInput) {
        gestureSearchInput.addEventListener('input', (e) => {
            const q = e.target.value.toLowerCase().trim();
            if (!q) {
                renderPublicGestures(cachedGesturesList);
            } else {
                const filtered = cachedGesturesList.filter(g => 
                    (g.name_th && g.name_th.toLowerCase().includes(q)) ||
                    (g.name_en && g.name_en.toLowerCase().includes(q)) ||
                    (g.category && g.category.toLowerCase().includes(q)) ||
                    (g.description && g.description.toLowerCase().includes(q))
                );
                renderPublicGestures(filtered);
            }
        });
    }

    // Auto-fetch gestures when Gestures tab or modal is opened
    if (navGestures) {
        navGestures.addEventListener('click', () => {
            if (cachedGesturesList.length === 0) loadPublicGestures();
        });
    }

    // Initial load
    loadPublicGestures();
>>>>>>> 1c1b13c353673fda383318dfad7b9144f1dd70d9
