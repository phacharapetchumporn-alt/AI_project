document.addEventListener('DOMContentLoaded', () => {
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
    let apiInterval = null;
    let mockInterval = null;
    let localStream = null;

    // Realistic Thai sign language words
    const mockWords = ["สวัสดี", "ขอบคุณ", "สบายดี", "ยินดีต้อนรับ", "ฉันรักคุณ", "เข้าใจแล้ว", "ขอความช่วยเหลือ", "โบสถ์", "1", "2", "3", "ใช่", "ตกลง"];
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
        if (!text || text === '...' || text === 'กำลังรอสัญญาณมือ...') {
            showToast('ยังไม่มีข้อความสำหรับการอ่านออกเสียง');
            return;
        }
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'th-TH';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            window.speechSynthesis.speak(utterance);
            showToast(`🔊 กำลังอ่านออกเสียง: "${text}"`);
        } else {
            showToast('อุปกรณ์ของคุณไม่รองรับฟังก์ชัน Text-to-Speech');
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
                'แตะเพื่อเปิดกล้อง',
                'กดปุ่มด้านล่างเพื่ออนุญาตให้เว็บไซต์เข้าถึงกล้องโทรศัพท์ของคุณ',
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
                'ไม่สามารถเปิดกล้องได้',
                isHttp && !isLocal
                    ? 'เบราว์เซอร์บนมือถือต้องการ HTTPS เพื่อเปิดกล้อง กรุณาเปิดผ่าน HTTPS (แตะลิงก์ด้านล่าง)'
                    : 'เบราว์เซอร์ของคุณไม่รองรับการเปิดกล้องผ่าน WebRTC กรุณาอัปเดตเบราว์เซอร์',
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
                if (typeof startCapture === 'function') startCapture();
            } catch (pErr) {
                console.warn('Autoplay prevented:', pErr);
            }

            if (cameraFallbackScreen) cameraFallbackScreen.style.display = 'none';
            if (scannerHud) scannerHud.style.display = 'block';

            const camName = facingMode === 'user' ? 'กล้องหน้า' : 'กล้องหลัง';
            statusText.textContent = isBackendConnected ? `ONLINE (${camName})` : `LIVE (${camName})`;
            statusDot.className = 'indicator-dot active';
            statusDot.style.backgroundColor = '#10b981';
            statusDot.style.boxShadow = '0 0 8px #10b981';

            if (btnCameraPower) btnCameraPower.classList.add('active');
            if (iconCamPower) iconCamPower.className = 'fa-solid fa-video';

            showToast(`เปิด${camName}สำเร็จแล้ว พร้อมตรวจจับ`);

            if (isBackendConnected) {
                if (apiInterval) clearInterval(apiInterval);
                apiInterval = setInterval(pollBackendPrediction, 250);
            } else {
                startMockPredictions();
            }
        } else {
            console.error("Camera access failed:", lastErr);
            isCameraRunning = false;
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
        if (typeof stopCapture === 'function') stopCapture();
        if (apiInterval) clearInterval(apiInterval);
        if (mockInterval) clearInterval(mockInterval);
        showCameraFallback('กล้องถูกปิดอยู่', 'แตะปุ่มด้านล่างหรือไอคอนกล้องเพื่อเปิดการทำงานใหม่');
        showToast('ปิดการทำงานของกล้องแล้ว');
    }

    // Toggle Camera On/Off
    function toggleCameraPower() {
        if (isCameraRunning) {
            stopClientWebcam();
        } else {
            startClientWebcam(currentFacingMode);
        }
    }

    // Flip Camera Front/Rear (for Mobile Phone)
    function flipCamera() {
        currentFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';

        // Add rotation animation
        if (btnFlipCam) btnFlipCam.classList.add('rotating');
        if (btnFlipCamBottom) btnFlipCamBottom.classList.add('rotating');
        setTimeout(() => {
            if (btnFlipCam) btnFlipCam.classList.remove('rotating');
            if (btnFlipCamBottom) btnFlipCamBottom.classList.remove('rotating');
        }, 600);

        showToast(`กำลังสลับไปยัง${currentFacingMode === 'user' ? 'กล้องหน้า' : 'กล้องหลัง'}...`);
        startClientWebcam(currentFacingMode);
    }

    // Poll predictions from Flask backend
    async function pollBackendPrediction() {
        if (!isTranslationActive || !isCameraRunning) return;

        try {
            const response = await fetch(`${serverUrl}/api/prediction`);
            if (response.ok) {
                const data = await response.json();
                updateUI(data.prediction, data.confidence, data.sentence);
            }
        } catch (err) {
            console.error("Error polling prediction:", err);
            isBackendConnected = false;
            clearInterval(apiInterval);
            startMockPredictions();
        }
    }

    // Simulate predictions for Demo Mode
    function startMockPredictions() {
        if (mockInterval) clearInterval(mockInterval);

        let lastMockWord = "";

        mockInterval = setInterval(() => {
            if (!isTranslationActive || !isCameraRunning) return;

            // 65% chance to detect something
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
                updateUI("รอกลุ่มท่าทาง...", "0.0%", mockSentence.join(' ') || "...");
            }
        }, 2200);
    }

    // Update UI Elements with smooth animation feedback
    let prevWord = "";
    function updateUI(word, confidence, sentence) {
        if (word !== prevWord && word !== "รอกลุ่มท่าทาง..." && word !== "กำลังรอสัญญาณมือ...") {
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

    // Camera Event Listeners
    if (btnClear) btnClear.addEventListener('click', () => handleControlAction('clear'));
    if (btnBackspace) btnBackspace.addEventListener('click', () => handleControlAction('backspace'));
    if (btnFlipCam) btnFlipCam.addEventListener('click', flipCamera);
    if (btnFlipCamBottom) btnFlipCamBottom.addEventListener('click', flipCamera);
    if (btnCameraPower) btnCameraPower.addEventListener('click', toggleCameraPower);
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
                showToast('เปิดระบบตรวจจับภาษามือ');
            } else {
                transOverlay.classList.add('hidden');
                btnToggleTranslate.style.backgroundColor = '#ef4444';
                btnToggleTranslate.style.boxShadow = '0 10px 20px rgba(239, 68, 68, 0.3)';
                btnToggleTranslate.querySelector('i').style.color = '#ffffff';
                showToast('ปิดระบบตรวจจับภาษามือชั่วคราว');
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
                qrLoading.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ไม่สามารถโหลดรูป QR Code ได้ (พิมพ์ลิงก์ด้านล่างลงในมือถือ)';
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
                showToast('คัดลอกลิงก์สำหรับมือถือเรียบร้อยแล้ว');
            } catch (err) {
                mobileUrlInput.select();
                document.execCommand('copy');
                showToast('คัดลอกลิงก์เรียบร้อย');
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
    const btnGive = document.getElementById('btn-give'); // เข้าสู่ระบบ button
    const btnPlan = document.getElementById('btn-plan'); // สมัครสมาชิก button
    const btnSocialGoogle = document.getElementById('btn-social-google');
    const btnSocialGithub = document.getElementById('btn-social-github');

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
            authModalTitle.textContent = 'เข้าสู่ระบบ SignSubs';
            authModalSubtitle.textContent = 'เพื่อใช้งานระบบแปลภาษามือเรียลไทม์และบันทึกประวัติ';
        } else {
            tabRegister.classList.add('active');
            tabRegister.setAttribute('aria-selected', 'true');
            tabLogin.classList.remove('active');
            tabLogin.setAttribute('aria-selected', 'false');
            formLogin.style.display = 'none';
            formRegister.style.display = 'flex';
            authModalTitle.textContent = 'สร้างบัญชี SignSubs ใหม่';
            authModalSubtitle.textContent = 'สมัครสมาชิกฟรีเพื่อเข้าถึงฟีเจอร์ตรวจจับภาษามือครบครัน';
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
        if (userDisplayName) userDisplayName.textContent = user.username || user.name || 'ผู้ใช้งาน';
        if (dropdownUsername) dropdownUsername.textContent = user.username || user.name || 'ผู้ใช้งาน';
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
            showToast('ออกจากระบบเรียบร้อยแล้ว');
        });
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
                showAuthAlert('กรุณากรอกชื่อผู้ใช้และรหัสผ่านให้ครบถ้วน');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังตรวจสอบ...';

            let loginSuccess = false;
            let loggedInUserData = null;

            // Attempt Backend Login if not local file
            if (!isLocalFile) {
                try {
                    const res = await fetch(`${serverUrl}/api/login`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username: usernameInput, password: passwordInput })
                    });
                    const data = await res.json();
                    if (res.ok && data.success) {
                        loginSuccess = true;
                        loggedInUserData = data.user;
                    } else if (res.status === 401) {
                        showAuthAlert(data.message || 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
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
                    showAuthAlert('รหัสผ่านต้องมีความยาวอย่างน้อย 4 ตัวอักษร');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
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
                showToast(`ยินดีต้อนรับคุณ ${loggedInUserData.username} เข้าสู่ระบบสำเร็จ`);
                formLogin.reset();
            }

            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>เข้าสู่ระบบ</span> <i class="fa-solid fa-arrow-right"></i>';
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
                showAuthAlert('ชื่อผู้ใช้งานต้องมีความยาวอย่างน้อย 3 ตัวอักษร');
                return;
            }

            if (password.length < 6) {
                showAuthAlert('รหัสผ่านต้องมีความยาวอย่างน้อย 6 ตัวอักษร');
                return;
            }

            if (password !== confirmPassword) {
                showAuthAlert('รหัสผ่านและการยืนยันรหัสผ่านไม่ตรงกัน');
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังสร้างบัญชี...';

            let regSuccess = false;
            let newUser = { username, email };

            if (!isLocalFile) {
                try {
                    const res = await fetch(`${serverUrl}/api/register`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ username, email, password })
                    });
                    const data = await res.json();
                    if (res.ok && data.success) {
                        regSuccess = true;
                        newUser = data.user || newUser;
                    } else {
                        showAuthAlert(data.message || 'ไม่สามารถสมัครสมาชิกได้');
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
                        return;
                    }
                } catch (err) {
                    console.log("Backend register unavailable, saving locally:", err);
                }
            }

            // Local fallback registration
            if (!regSuccess) {
                const storedUsers = JSON.parse(localStorage.getItem('signsubs_users') || '[]');
                const exists = storedUsers.some(u => u.username.toLowerCase() === username.toLowerCase() || u.email.toLowerCase() === email.toLowerCase());
                
                if (exists) {
                    showAuthAlert('ชื่อผู้ใช้หรืออีเมลนี้มีอยู่ในระบบแล้ว');
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
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
                showToast(`สร้างบัญชีสำเร็จ ยินดีต้อนรับคุณ ${newUser.username}!`);
                formRegister.reset();
            }

            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>สมัครสมาชิก</span> <i class="fa-solid fa-user-check"></i>';
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
            showToast('เข้าสู่ระบบด้วย Google Account สำเร็จ');
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
            showToast('เข้าสู่ระบบด้วย GitHub Account สำเร็จ');
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

    // Toggle Almost Fullscreen (เกือบเต็มจอ / Theater Mode)
    function toggleTheaterMode(forceState = null) {
        if (!cameraCard) return;
        const isTheater = forceState !== null ? forceState : !cameraCard.classList.contains('theater-mode');

        if (isTheater) {
            cameraCard.classList.add('theater-mode');
            if (expandIcon) expandIcon.className = 'fa-solid fa-compress';
            if (expandText) expandText.textContent = 'ย่อขนาด';
            if (btnExpandCam) btnExpandCam.title = 'ย่อขนาดจอกล้อง (Esc)';
            showToast('ขยายจอกล้องเกือบเต็มจอ (กด Esc หรือคลิกซ้ำเพื่อย่อ)');
        } else {
            cameraCard.classList.remove('theater-mode');
            if (expandIcon) expandIcon.className = 'fa-solid fa-expand';
            if (expandText) expandText.textContent = 'ขยายเกือบเต็มจอ';
            if (btnExpandCam) btnExpandCam.title = 'ขยายเกือบเต็มจอ (F)';
            showToast('ย่อจอกล้องสู่ขนาดปกติ');
        }
    }

    if (btnExpandCam) {
        btnExpandCam.addEventListener('click', () => toggleTheaterMode());
    }

    // Keyboard shortcuts: 'F' to toggle fullscreen, 'Escape' to exit
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'Escape' && cameraCard.classList.contains('theater-mode')) {
            toggleTheaterMode(false);
        } else if (e.key === 'f' || e.key === 'F') {
            toggleTheaterMode();
        }
    });

    // Start App
    initCamera();
});
