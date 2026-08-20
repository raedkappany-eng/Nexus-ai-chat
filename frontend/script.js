// ==================== التهيئة العامة ====================

/**
 * الدالة الرئيسية التي تعمل عند تحميل الصفحة
 */
function init() {
    console.log('تهيئة تطبيق Nexus AI...');
    
    // إنشاء النجوم في الخلفية
    createStars();
    
    // تهيئة النماذج
    initializeModels();
    
    // إضافة مستمعي الأحداث
    setupEventListeners();
    
    // التحقق من وجود مستخدم مسجل
    checkAuthentication();
}

// ==================== نظام النجوم ====================

/**
 * إنشاء نجوم متوهجة في الخلفية
 */
function createStars() {
    const container = document.getElementById('stars-container');
    const starCount = 150; // زيادة عدد النجوم
    
    for (let i = 0; i < starCount; i++) {
        const star = document.createElement('div');
        star.classList.add('star');
        
        star.style.left = Math.random() * 100 + '%';
        star.style.top = Math.random() * 100 + '%';
        
        const size = Math.random() * 2 + 1;
        star.style.width = size + 'px';
        star.style.height = size + 'px';
        
        star.style.animationDelay = Math.random() * 3 + 's';
        star.style.animationDuration = (Math.random() * 2 + 1) + 's';
        
        const brightness = Math.random() * 0.7 + 0.3;
        star.style.opacity = brightness;
        
        container.appendChild(star);
    }
}

// ==================== نظام النماذج ====================


const models = [
    { id: 'gemini', name: 'Gemini', color: '#b388ff' },
    { id: 'mistral_small', name: 'ChatGPT', color: '#00d4ff' },
    { id: 'mistral_code', name: 'Code AI', color: '#00ff9d' },
    { id: 'mistral_vision', name: 'Photo AI', color: '#ff6b35' }
];

// النماذج المختارة حالياً
let selectedModels = new Set();
selectedModels.add('gpt-4');

/**
 * تهيئة عرض النماذج
 */
function initializeModels() {
    const modelsList = document.getElementById('models-list');
    modelsList.innerHTML = '';
    
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.classList.add('model-card');
        modelCard.dataset.modelId = model.id;
        modelCard.style.color = model.color;
        
        modelCard.innerHTML = `
            <span class="model-name">${model.name}</span>
        `;
        
        if (selectedModels.has(model.id)) {
            modelCard.classList.add('active');
        }
        
        modelCard.addEventListener('click', () => toggleModel(model.id));
        
        modelsList.appendChild(modelCard);
    });
    
    updateInputBorderColor();
}

/**
 * تبديل حالة النموذج
 */
function toggleModel(modelId) {
    if (selectedModels.has(modelId)) {
        selectedModels.delete(modelId);
    } else {
        selectedModels.add(modelId);
    }
    
    const modelCards = document.querySelectorAll('.model-card');
    modelCards.forEach(card => {
        const id = card.dataset.modelId;
        if (selectedModels.has(id)) {
            card.classList.add('active');
        } else {
            card.classList.remove('active');
        }
    });
    
    updateInputBorderColor();
}

/**
 * تحديث لون إطار الإدخال
 * شرح: عند اختيار نموذج واحد نستخدم لونه مباشرة
 * عند اختيار عدة نماذج ندمج الألوان بتدرج
 */
function updateInputBorderColor() {
    const inputWrapper = document.getElementById('input-wrapper');
    const selectedColors = [];
    
    selectedModels.forEach(modelId => {
        const model = models.find(m => m.id === modelId);
        if (model) {
            selectedColors.push(model.color);
        }
    });
    
    if (selectedColors.length === 1) {
        inputWrapper.style.borderColor = selectedColors[0];
        inputWrapper.style.color = selectedColors[0];
        inputWrapper.style.boxShadow = `0 0 20px ${selectedColors[0]}40`;
    } else if (selectedColors.length > 1) {
        const gradient = `linear-gradient(90deg, ${selectedColors.join(', ')})`;
        inputWrapper.style.borderColor = 'transparent';
        inputWrapper.style.backgroundImage = `linear-gradient(var(--bg-dark), var(--bg-dark)), ${gradient}`;
        inputWrapper.style.backgroundOrigin = 'border-box';
        inputWrapper.style.backgroundClip = 'padding-box, border-box';
        inputWrapper.style.color = selectedColors[0];
        inputWrapper.style.boxShadow = `0 0 30px ${selectedColors[0]}40`;
    }
}

// ==================== نظام المصادقة ====================

/**
 * التحقق من وجود مستخدم مسجل
 */
function checkAuthentication() {
    const token = localStorage.getItem('nexus_token');
    const username = localStorage.getItem('nexus_username');
    
    if (token && username) {
        showSplashScreen(username);
    } else {
        showAuthScreen();
    }
}

/**
 * إظهار شاشة تسجيل الدخول
 */
function showAuthScreen() {
    document.getElementById('auth-screen').classList.remove('hidden');
    document.getElementById('splash-screen').classList.add('hidden');
    document.getElementById('chat-screen').classList.add('hidden');
}

/**
 * إظهار شاشة الترحيب مع تأثير الكتابة
 * شرح تأثير الكتابة: نضيف حرفاً كل 50ms مع مؤشر وامض
 */
function showSplashScreen(username) {
    const splashScreen = document.getElementById('splash-screen');
    const welcomeText = document.getElementById('welcome-text');
    const neonSphere = document.getElementById('neon-sphere');
    
    splashScreen.classList.remove('hidden');
    document.getElementById('auth-screen').classList.add('hidden');
    document.getElementById('chat-screen').classList.add('hidden');
    
    welcomeText.classList.remove('hidden');
    welcomeText.classList.remove('shrinking');
    neonSphere.classList.add('hidden');
    
    const message = `مرحباً ${username}`;
    let charIndex = 0;
    welcomeText.innerHTML = '';
    
    const cursor = document.createElement('span');
    cursor.classList.add('typing-cursor');
    welcomeText.appendChild(cursor);
    
    function typeNextChar() {
        if (charIndex < message.length) {
            const charSpan = document.createElement('span');
            charSpan.textContent = message[charIndex];
            welcomeText.insertBefore(charSpan, cursor);
            charIndex++;
            setTimeout(typeNextChar, 50);
        } else {
            cursor.remove();
            
            setTimeout(() => {
                welcomeText.classList.add('shrinking');
                
                setTimeout(() => {
                    welcomeText.classList.add('hidden');
                    neonSphere.classList.remove('hidden');
                    
                    setTimeout(() => {
                        enterChatScreen(username);
                    }, 2000);
                }, 50);
            }, 1000);
        }
    }
    
    setTimeout(typeNextChar, 500);
}

/**
 * الانتقال لواجهة الدردشة
 */
function enterChatScreen(username) {
    document.getElementById('splash-screen').classList.add('hidden');
    document.getElementById('chat-screen').classList.remove('hidden');
    document.getElementById('user-name-display').textContent = username;
    
    loadChatHistory();
}

// ==================== نظام تسجيل الدخول ====================

/**
 * إعداد مستمعي الأحداث
 */
function setupEventListeners() {
    document.getElementById('show-register').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('flip-card').classList.add('flipped');
    });
    
    document.getElementById('show-login').addEventListener('click', (e) => {
        e.preventDefault();
        document.getElementById('flip-card').classList.remove('flipped');
    });
    
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
    
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    document.getElementById('send-btn').addEventListener('click', sendMessage);
    document.getElementById('message-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    document.getElementById('attach-btn').addEventListener('click', () => {
        document.getElementById('file-input').click();
    });
    
    document.getElementById('file-input').addEventListener('change', handleFileUpload);
    
    const messageInput = document.getElementById('message-input');
    messageInput.addEventListener('input', () => {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 150) + 'px';
    });
}

/**
 * معالجة تسجيل الدخول
 * شرح تأثير الانفجار: الزر يتمدد من المركز للخارج مع تلاشي
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const loginBtn = document.getElementById('login-btn');
    
    loginBtn.classList.add('exploding');
    
    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({ username, password })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'فشل تسجيل الدخول');
        }

        const data = await response.json();
        localStorage.setItem('nexus_token', data.access_token);
        localStorage.setItem('nexus_username', data.username);
        
        setTimeout(() => {
            showSplashScreen(data.username);
        }, 600);
        
    } catch (error) {
        console.error('خطأ في تسجيل الدخول:', error);
        loginBtn.classList.remove('exploding');
        alert(error.message || 'فشل تسجيل الدخول. يرجى المحاولة مرة أخرى.');
    }
}

/**
 * معالجة إنشاء الحساب
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;
    const registerBtn = document.getElementById('register-btn');
    
    registerBtn.classList.add('exploding');
    
    try {
        const response = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.detail || 'فشل إنشاء الحساب');
        }

        const data = await response.json();
        localStorage.setItem('nexus_token', data.access_token);
        localStorage.setItem('nexus_username', data.username);
        
        setTimeout(() => {
            showSplashScreen(data.username);
        }, 600);
        
    } catch (error) {
        console.error('خطأ في إنشاء الحساب:', error);
        registerBtn.classList.remove('exploding');
        alert(error.message || 'فشل إنشاء الحساب. يرجى المحاولة مرة أخرى.');
    }
}

/**
 * معالجة تسجيل الخروج
 */
function handleLogout() {
    localStorage.removeItem('nexus_token');
    localStorage.removeItem('nexus_username');
    showAuthScreen();
}

// ==================== نظام الدردشة ====================

/**
 * تحميل سجل المحادثات من الـ Backend
 */
async function loadChatHistory() {
    const token = localStorage.getItem('nexus_token');
    const currentUsername = localStorage.getItem('nexus_username');
    const messagesContainer = document.getElementById('messages-container');
    
    messagesContainer.innerHTML = '';
    
    try {
        const response = await fetch('/api/messages', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) throw new Error('فشل جلب المحادثات');
        
        const data = await response.json();
        
        if (data.length === 0) {
            addMessageToChat(
                'مرحباً بك في Nexus AI! كيف يمكنني مساعدتك اليوم؟',
                'bot',
                new Date().toISOString()
            );
        } else {
            data.forEach(msg => {
                if (msg.sender === currentUsername) {
                    addMessageToChat(msg.content, 'user', msg.timestamp);
                } else {
                    const botKeyMatch = Object.keys(BOT_STYLES).find(key => 
                        BOT_STYLES[key].label.toLowerCase() === msg.sender.toLowerCase()
                    );
                    const style = botKeyMatch ? BOT_STYLES[botKeyMatch] : {
                        label: msg.sender, cssClass: '', color: 'var(--neon-blue)',
                        avatar: msg.sender.charAt(0).toUpperCase()
                    };
                    addMessageToChat(msg.content, 'bot', msg.timestamp, style);
                }
            });
        }
        
    } catch (error) {
        console.error('خطأ في تحميل سجل المحادثات:', error);
    }
}

const BOT_STYLES = {
    gemini:         { label: 'Gemini',  cssClass: 'model-gemini',  color: 'var(--neon-purple)', avatar: 'G' },
    mistral_small:  { label: 'ChatGpt', cssClass: 'model-chatgpt', color: 'var(--neon-blue)',   avatar: 'C' },
    mistral_code:   { label: 'Code_ai', cssClass: 'model-code',    color: 'var(--neon-green)',  avatar: '⌘' },
    mistral_vision: { label: 'photo_ai',cssClass: 'model-photo',   color: 'var(--neon-orange)', avatar: '📷' }
};

function addMessageToChat(content, role, timestamp, modelInfo) {
    const messagesContainer = document.getElementById('messages-container');
    
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    if (role === 'bot' && modelInfo && modelInfo.cssClass) {
        messageDiv.classList.add(modelInfo.cssClass);
    }
    
    const time = new Date(timestamp);
    const timeString = time.toLocaleTimeString('ar-SA', {
        hour: '2-digit',
        minute: '2-digit'
    });
    
    const headerHtml = (role === 'bot' && modelInfo)
        ? `<div class="message-header">
               <span class="message-avatar" style="background:${modelInfo.color}">${modelInfo.avatar}</span>
               <span class="message-model-name" style="color:${modelInfo.color}">${modelInfo.label}</span>
           </div>`
        : '';
    
    messageDiv.innerHTML = `
        ${headerHtml}
        <div class="message-content">${content}</div>
        <div class="message-timestamp">${timeString}</div>
    `;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

/**
 * إرسال رسالة إلى الـ Backend
 */

async function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const message = messageInput.value.trim();
    
    if (!message) return;
    
    const token = localStorage.getItem('nexus_token');
    
    addMessageToChat(message, 'user', new Date().toISOString());
    
    messageInput.value = '';
    messageInput.style.height = 'auto';

    const selectedBotsArray = Array.from(selectedModels);
    const targetBotString = selectedBotsArray.length > 0 ? selectedBotsArray.join(',') : 'all';
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: message,
                target_bot: targetBotString, 
                attachment: currentAttachment
            })
        });

        currentAttachment = null;
        removeAttachment();

        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('جلسة العمل منتهية، يرجى تسجيل الدخول مرة أخرى.');
            }
            throw new Error(`خطأ في الخادم: ${response.status}`);
        }

        const data = await response.json();

        if (data.responses) {
            Object.entries(data.responses).forEach(([botKey, reply]) => {
                const style = BOT_STYLES[botKey] || {
                    label: botKey, cssClass: '', color: 'var(--neon-blue)',
                    avatar: botKey.charAt(0).toUpperCase()
                };
                addMessageToChat(reply, 'bot', new Date().toISOString(), style);
            });
        }

    } catch (error) {
        console.error('Error:', error);
        addMessageToChat('عذراً، ' + error.message, 'bot', new Date().toISOString());
    }
}

let currentAttachment = null;

async function handleFileUpload(event) {
    const files = event.target.files;
    const token = localStorage.getItem('nexus_token');
    
    if (files.length === 0) return;
    
    const file = files[0];
    const formData = new FormData();
    
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`
            },
            body: formData
        });

        if (!response.ok) {
            throw new Error('فشل رفع الملف');
        }

        const data = await response.json();
        
        currentAttachment = {
            url: data.url,
            filename: data.filename,
            content_type: data.content_type
        };
        
        addMessageToChat(`📎 تم إرفاق المرفق: ${file.name} جاهز للإرسال.`, 'user', new Date().toISOString());
        
    } catch (error) {
        console.error('خطأ في الرفع:', error);
        addMessageToChat('عذراً، حدث خطأ أثناء رفع الملف.', 'bot', new Date().toISOString());
    }
    
    event.target.value = '';
}

// ==================== بدء التطبيق ====================

document.addEventListener('DOMContentLoaded', init);

window.NexusAI = {
    init,
    sendMessage,
    loadChatHistory,
    toggleModel,
    handleLogout
};

// --- أكواد معاينة المرفقات ---
const fileInput = document.getElementById('file-input');
const previewContainer = document.getElementById('attachment-preview-container');
const previewImg = document.getElementById('attachment-preview-img');

fileInput.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(event) {
            previewImg.src = event.target.result; 
            previewContainer.style.display = 'flex';
        };
        reader.readAsDataURL(file);
    }
});

function removeAttachment() {
    previewContainer.style.display = 'none';
    previewImg.src = '';
    fileInput.value = ''; 
}
// -----------------------------