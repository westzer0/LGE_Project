/**
 * AI 챗봇 공통 기능
 * 메인 페이지와 온보딩 페이지에서 공통으로 사용
 */

// AI 챗봇 기능
let chatbotOpen = false;
let chatHistory = [];

function initChatbot() {
    // 챗봇 토글 버튼 이벤트
    const toggleBtn = document.getElementById('chatbotToggleBtn');
    const window = document.getElementById('chatbotWindow');
    
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleChatbot);
    }
    
    // 닫기 버튼 이벤트
    const closeBtn = document.querySelector('.chatbot-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', toggleChatbot);
    }
    
    // 입력 필드 엔터 키 이벤트
    const input = document.getElementById('chatbotInput');
    if (input) {
        input.addEventListener('keypress', function(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendChatbotMessage();
            }
        });
    }
    
    // 전송 버튼 이벤트
    const sendBtn = document.querySelector('.chatbot-send-btn');
    if (sendBtn) {
        sendBtn.addEventListener('click', sendChatbotMessage);
    }
}

function toggleChatbot() {
    chatbotOpen = !chatbotOpen;
    const window = document.getElementById('chatbotWindow');
    const btn = document.getElementById('chatbotToggleBtn');
    
    if (chatbotOpen) {
        window.classList.add('open');
        if (btn) btn.classList.add('active');
        const input = document.getElementById('chatbotInput');
        if (input) {
            setTimeout(() => input.focus(), 300);
        }
    } else {
        window.classList.remove('open');
        if (btn) btn.classList.remove('active');
    }
}

async function sendChatbotMessage() {
    const input = document.getElementById('chatbotInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // 사용자 메시지 표시
    addChatbotMessage(message, 'user');
    input.value = '';
    input.disabled = true;
    document.querySelector('.chatbot-send-btn').disabled = true;
    
    // 로딩 표시
    const loadingId = addChatbotMessage('답변을 생성하고 있어요...', 'bot', true);
    
    try {
        const response = await fetch('/api/ai/chat/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                context: {
                    history: chatHistory
                }
            })
        });
        
        const data = await response.json();
        
        // 로딩 메시지 제거
        document.getElementById(loadingId)?.remove();
        
        if (data.success) {
            addChatbotMessage(data.response, 'bot');
            chatHistory.push(
                { role: 'user', content: message },
                { role: 'assistant', content: data.response }
            );
            // 최근 10개 대화만 유지
            if (chatHistory.length > 20) {
                chatHistory = chatHistory.slice(-20);
            }
        } else {
            addChatbotMessage('죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.', 'bot');
        }
    } catch (error) {
        console.error('Chatbot error:', error);
        document.getElementById(loadingId)?.remove();
        addChatbotMessage('네트워크 오류가 발생했어요. 잠시 후 다시 시도해주세요.', 'bot');
    } finally {
        input.disabled = false;
        document.querySelector('.chatbot-send-btn').disabled = false;
        input.focus();
    }
}

function addChatbotMessage(text, type, isLoading = false) {
    const messages = document.getElementById('chatbotMessages');
    const messageId = 'msg-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    const messageDiv = document.createElement('div');
    messageDiv.id = messageId;
    messageDiv.className = `chatbot-message ${type}`;
    
    if (isLoading) {
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content loading">
                ${escapeHtml(text)}
                <span class="loading-dots">
                    <span>.</span><span>.</span><span>.</span>
                </span>
            </div>
        `;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">${type === 'user' ? '👤' : '🤖'}</div>
            <div class="message-content">${escapeHtml(text).replace(/\n/g, '<br>')}</div>
        `;
    }
    
    messages.appendChild(messageDiv);
    messages.scrollTop = messages.scrollHeight;
    
    return messageId;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// 페이지 로드 시 초기화
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initChatbot);
} else {
    initChatbot();
}

