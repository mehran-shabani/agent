// Medical Chat Application
class MedicalChatApp {
    constructor() {
        this.sessionId = null;
        this.conversationId = null;
        this.messageCount = 0;
        this.startTime = null;
        this.isTyping = false;
        this.recognition = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.initSpeechRecognition();
        this.startNewConversation();
    }

    bindEvents() {
        // Send message events
        document.getElementById('sendBtn').addEventListener('click', () => this.sendMessage());
        document.getElementById('messageInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Voice input
        document.getElementById('voiceBtn').addEventListener('click', () => this.toggleVoiceRecording());

        // Quick action buttons
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const message = e.currentTarget.dataset.message;
                document.getElementById('messageInput').value = message;
                this.sendMessage();
            });
        });

        // New chat button
        document.getElementById('newChatBtn').addEventListener('click', () => this.startNewConversation());

        // Medical case button
        document.getElementById('medicalCaseBtn').addEventListener('click', () => this.showMedicalCase());

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => this.closeModal());
        document.getElementById('medicalCaseModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeModal();
        });
    }

    initSpeechRecognition() {
        if ('webkitSpeechRecognition' in window) {
            this.recognition = new webkitSpeechRecognition();
            this.recognition.lang = 'fa-IR';
            this.recognition.continuous = false;
            this.recognition.interimResults = false;

            this.recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                document.getElementById('messageInput').value = transcript;
                this.showToast('متن شما تشخیص داده شد', 'success');
            };

            this.recognition.onerror = (event) => {
                this.showToast('خطا در تشخیص صدا: ' + event.error, 'error');
            };

            this.recognition.onend = () => {
                document.getElementById('voiceBtn').innerHTML = '<i class="fas fa-microphone"></i>';
            };
        } else {
            document.getElementById('voiceBtn').style.display = 'none';
        }
    }

    async startNewConversation() {
        try {
            this.showLoading(true);
            
            const response = await fetch('/api/conversation/start/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                }
            });

            if (!response.ok) throw new Error('خطا در شروع مکالمه');

            const data = await response.json();
            this.sessionId = data.session_id;
            this.conversationId = data.conversation_id;
            this.startTime = new Date();
            
            // Clear chat and reset UI
            this.clearChat();
            this.resetUI();
            
            // Add initial message
            this.addMessage('assistant', data.message, new Date(data.timestamp));
            
            // Enable input
            this.setInputEnabled(true);
            
            this.showToast('مکالمه جدید شروع شد', 'success');
            this.updateTimer();

        } catch (error) {
            this.showToast('خطا در شروع مکالمه: ' + error.message, 'error');
        } finally {
            this.showLoading(false);
        }
    }

    async sendMessage() {
        const input = document.getElementById('messageInput');
        const message = input.value.trim();
        
        if (!message || this.isTyping) return;
        if (!this.sessionId) {
            this.showToast('ابتدا مکالمه را شروع کنید', 'warning');
            return;
        }

        // Add user message to chat
        this.addMessage('user', message);
        input.value = '';
        this.messageCount++;
        this.updateMessageCount();

        // Show typing indicator
        this.showTypingIndicator();
        this.isTyping = true;

        try {
            const response = await fetch('/api/conversation/message/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    message: message
                })
            });

            if (!response.ok) throw new Error('خطا در ارسال پیام');

            const data = await response.json();
            
            // Remove typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessage('assistant', data.response, new Date(data.timestamp));
            this.messageCount++;
            this.updateMessageCount();

            // Update medical case info
            this.updateUrgencyLevel();

        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('error', 'متأسفانه خطایی رخ داده است: ' + error.message);
            this.showToast('خطا در ارسال پیام', 'error');
        } finally {
            this.isTyping = false;
        }
    }

    addMessage(role, content, timestamp = new Date()) {
        const messagesContainer = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const avatarIcon = {
            'user': 'fas fa-user',
            'assistant': 'fas fa-robot',
            'error': 'fas fa-exclamation-triangle'
        };

        messageDiv.innerHTML = `
            <div class="message-avatar">
                <i class="${avatarIcon[role]}"></i>
            </div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(content)}</div>
                <div class="message-time">${this.formatTime(timestamp)}</div>
            </div>
        `;

        messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatMessage(content) {
        // Convert newlines to <br> and add basic formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    showTypingIndicator() {
        const messagesContainer = document.getElementById('chatMessages');
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant typing-indicator-message';
        typingDiv.innerHTML = `
            <div class="message-avatar">
                <i class="fas fa-robot"></i>
            </div>
            <div class="typing-indicator">
                <span>در حال تایپ</span>
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;
        
        messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const typingIndicator = document.querySelector('.typing-indicator-message');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    toggleVoiceRecording() {
        if (!this.recognition) return;

        const voiceBtn = document.getElementById('voiceBtn');
        
        if (this.recognition.recording) {
            this.recognition.stop();
            voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        } else {
            this.recognition.start();
            voiceBtn.innerHTML = '<i class="fas fa-stop"></i>';
            this.showToast('در حال گوش دادن...', 'info');
        }
    }

    async showMedicalCase() {
        if (!this.sessionId) {
            this.showToast('ابتدا مکالمه را شروع کنید', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/medical-case/${this.sessionId}/`);
            
            if (!response.ok) throw new Error('پرونده پزشکی یافت نشد');

            const data = await response.json();
            
            // Update modal content
            document.getElementById('chiefComplaint').textContent = data.chief_complaint || '--';
            document.getElementById('medicalHistory').textContent = data.medical_history || '--';
            document.getElementById('medications').textContent = data.medications || '--';
            
            // Update urgency
            const urgencyElement = document.getElementById('caseUrgency');
            urgencyElement.textContent = this.getUrgencyText(data.urgency_level);
            urgencyElement.className = `urgency-badge ${data.urgency_level}`;
            
            // Update symptoms
            const symptomsList = document.getElementById('symptomsList');
            if (data.symptoms && Object.keys(data.symptoms).length > 0) {
                symptomsList.innerHTML = Object.entries(data.symptoms)
                    .map(([key, value]) => `<span class="symptom-tag">${key}: ${value}</span>`)
                    .join('');
            } else {
                symptomsList.textContent = '--';
            }

            // Show modal
            document.getElementById('medicalCaseModal').classList.add('show');

        } catch (error) {
            this.showToast('خطا در بارگذاری پرونده پزشکی', 'error');
        }
    }

    closeModal() {
        document.getElementById('medicalCaseModal').classList.remove('show');
    }

    async updateUrgencyLevel() {
        if (!this.sessionId) return;

        try {
            const response = await fetch(`/api/medical-case/${this.sessionId}/`);
            if (response.ok) {
                const data = await response.json();
                const urgencyElement = document.getElementById('urgencyLevel');
                urgencyElement.textContent = this.getUrgencyText(data.urgency_level);
                
                // Update card styling
                const urgencyCard = document.querySelector('.urgency-card');
                urgencyCard.className = `info-card urgency-card ${data.urgency_level}`;
            }
        } catch (error) {
            console.log('خطا در به‌روزرسانی سطح اورژانسی:', error);
        }
    }

    getUrgencyText(level) {
        const texts = {
            'low': 'کم',
            'medium': 'متوسط', 
            'high': 'بالا',
            'emergency': 'اورژانسی'
        };
        return texts[level] || 'نامشخص';
    }

    updateTimer() {
        if (!this.startTime) return;

        setInterval(() => {
            const now = new Date();
            const diff = now - this.startTime;
            const minutes = Math.floor(diff / 60000);
            const seconds = Math.floor((diff % 60000) / 1000);
            
            document.getElementById('chatDuration').textContent = 
                `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    updateMessageCount() {
        document.getElementById('messageCount').textContent = this.messageCount;
    }

    clearChat() {
        document.getElementById('chatMessages').innerHTML = '';
        this.messageCount = 0;
        this.updateMessageCount();
    }

    resetUI() {
        document.getElementById('urgencyLevel').textContent = 'نامشخص';
        document.getElementById('chatDuration').textContent = '--:--';
        document.querySelector('.urgency-card').className = 'info-card urgency-card';
    }

    setInputEnabled(enabled) {
        const input = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        input.disabled = !enabled;
        sendBtn.disabled = !enabled;
        
        if (enabled) {
            input.focus();
        }
    }

    showLoading(show) {
        const loadingState = document.getElementById('loadingState');
        loadingState.style.display = show ? 'flex' : 'none';
    }

    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatTime(date) {
        return date.toLocaleTimeString('fa-IR', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="${icons[type]}"></i>
            <span>${message}</span>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MedicalChatApp();
});

// Add CSRF token to page
document.addEventListener('DOMContentLoaded', () => {
    if (!document.querySelector('[name=csrfmiddlewaretoken]')) {
        fetch('/api/conversation/start/', {
            method: 'GET',
        }).then(response => response.text()).then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const token = doc.querySelector('[name=csrfmiddlewaretoken]');
            if (token) {
                document.head.appendChild(token);
            }
        }).catch(() => {
            // Create a dummy token if needed
            const tokenInput = document.createElement('input');
            tokenInput.type = 'hidden';
            tokenInput.name = 'csrfmiddlewaretoken';
            tokenInput.value = 'dummy-token';
            document.head.appendChild(tokenInput);
        });
    }
});