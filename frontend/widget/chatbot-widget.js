/**
 * LT Chatbot Web Component
 * Embeddable chatbot widget for any webpage
 * Usage: <lt-chatbot data-id="chatbot123"></lt-chatbot>
 */

class LTChatbot extends HTMLElement {
    static get observedAttributes() {
        return [
            'data-id',
            'data-mode', 
            'data-theme',
            'data-api-base',
            'data-title',
            'data-placeholder',
            'data-height',
            'data-width'
        ];
    }

    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        
        // Component state
        this.chatbotId = null;
        this.chatbot = null;
        this.sessionId = null;
        this.apiBase = 'http://localhost:8000/api'; // Default to common FastAPI port
        this.mode = 'inline'; // inline, floating, modal, sidebar
        this.theme = 'light';
        this.isMinimized = false;
        this.isLoading = true;
        this.typingIndicator = null;
        this.humanSupportRequest = null;
        this.websocket = null;
        this.isHumanSupportActive = false;
        
        // Configuration
        this.config = {
            title: 'AI Assistant',
            placeholder: 'Type your message here...',
            height: '500px',
            width: '100%',
            welcomeMessage: 'Hello! How can I help you today?'
        };

        // Bind methods
        this.sendMessage = this.sendMessage.bind(this);
        this.handleKeyPress = this.handleKeyPress.bind(this);
        this.toggleWidget = this.toggleWidget.bind(this);
    }

    connectedCallback() {
        this.parseAttributes();
        this.render();
        this.initializeChatbot();
    }

    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue !== newValue) {
            this.parseAttributes();
            if (this.shadowRoot.innerHTML) {
                this.render();
                this.initializeChatbot();
            }
        }
    }

    parseAttributes() {
        this.chatbotId = this.getAttribute('data-id');
        this.mode = this.getAttribute('data-mode') || 'inline';
        this.theme = this.getAttribute('data-theme') || 'light';
        this.apiBase = this.getAttribute('data-api-base') || '/api';
        
        this.config.title = this.getAttribute('data-title') || 'AI Assistant';
        this.config.placeholder = this.getAttribute('data-placeholder') || 'Type your message here...';
        this.config.height = this.getAttribute('data-height') || '500px';
        this.config.width = this.getAttribute('data-width') || '100%';

        if (!this.chatbotId) {
            console.error('LT Chatbot: data-id attribute is required');
        }
        
        // Check for session ID in URL parameters
        this.checkUrlParameters();
    }

    getRequestHeaders() {
        return {
            'Content-Type': 'application/json',
            'ngrok-skip-browser-warning': 'true'
        };
    }
    
    checkUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const urlChatbotId = urlParams.get('chatbot');
        const urlSessionId = urlParams.get('session');
        
        // If URL has chatbot ID that matches or overrides the widget's chatbot ID
        if (urlChatbotId && (urlChatbotId === this.chatbotId || !this.chatbotId)) {
            this.chatbotId = urlChatbotId;
            this.urlSessionId = urlSessionId;
        }
    }

    render() {
        const styles = this.getStyles();
        const html = this.getHTML();
        
        this.shadowRoot.innerHTML = `
            <style>${styles}</style>
            ${html}
        `;

        this.bindEvents();
    }

    getStyles() {
        return `
            :host {
                display: block;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                --primary-color: #1e3a8a;
                --secondary-color: #1d4ed8;
                --background-color: ${this.theme === 'dark' ? '#1a1a1a' : '#ffffff'};
                --text-color: ${this.theme === 'dark' ? '#ffffff' : '#333333'};
                --border-color: ${this.theme === 'dark' ? '#333333' : '#e2e8f0'};
                --input-bg: ${this.theme === 'dark' ? '#2d2d2d' : '#ffffff'};
                --message-bg: ${this.theme === 'dark' ? '#2d2d2d' : '#f7fafc'};
            }

            .chatbot-container {
                width: ${this.config.width};
                height: ${this.config.height};
                display: flex;
                flex-direction: column;
                background: var(--background-color);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            }

            .chatbot-container.floating {
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 350px;
                height: 500px;
                z-index: 10000;
                transition: all 0.3s ease;
            }

            .chatbot-container.floating.minimized {
                height: 60px;
                width: 300px;
            }

            .chatbot-header {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                padding: 12px 16px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: ${this.mode === 'floating' ? 'pointer' : 'default'};
            }

            .chatbot-title {
                font-size: 16px;
                font-weight: 600;
                margin: 0;
            }

            .chatbot-controls {
                display: flex;
                gap: 8px;
            }

            .control-btn {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 4px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 14px;
                transition: background 0.2s;
            }

            .control-btn:hover {
                background: rgba(255, 255, 255, 0.3);
            }

            .chat-messages {
                flex: 1;
                overflow-y: auto;
                padding: 16px;
                display: flex;
                flex-direction: column;
                gap: 12px;
                background: var(--background-color);
            }

            .message {
                max-width: 80%;
                animation: slideIn 0.3s ease;
            }

            .message.user {
                align-self: flex-end;
            }

            .message.bot {
                align-self: flex-start;
            }

            .message-content {
                padding: 12px 16px;
                border-radius: 16px;
                word-wrap: break-word;
                line-height: 1.4;
            }

            .message.user .message-content {
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                border-bottom-right-radius: 4px;
            }

            .message.bot .message-content {
                background: var(--message-bg);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-bottom-left-radius: 4px;
            }

            .message-sender {
                font-size: 12px;
                color: #6b7280;
                margin-bottom: 4px;
                font-weight: 500;
            }

            .chat-input-container {
                padding: 16px;
                border-top: 1px solid var(--border-color);
                background: var(--background-color);
            }

            .input-wrapper {
                display: flex;
                gap: 8px;
                margin-bottom: 8px;
            }

            .action-buttons {
                display: flex;
                justify-content: center;
                margin-bottom: 8px;
            }

            .human-support-button {
                background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            }

            .human-support-button:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
            }

            .support-status {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                background: rgba(34, 197, 94, 0.1);
                border-radius: 20px;
                font-size: 14px;
                color: #16a34a;
            }

            .status-indicator {
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: #fbbf24;
                animation: pulse 2s infinite;
            }

            .status-indicator.active {
                background: #22c55e;
            }

            .status-indicator.resolved {
                background: #6b7280;
            }

            .message-input {
                flex: 1;
                padding: 12px 16px;
                border: 2px solid var(--border-color);
                border-radius: 20px;
                outline: none;
                background: var(--input-bg);
                color: var(--text-color);
                font-size: 14px;
                transition: border-color 0.3s;
            }

            .message-input:focus {
                border-color: var(--primary-color);
            }

            .send-button {
                padding: 12px 20px;
                background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
                color: white;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                font-weight: 600;
                transition: transform 0.2s, box-shadow 0.2s;
                font-size: 14px;
            }

            .send-button:hover:not(:disabled) {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);
            }

            .send-button:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .status {
                font-size: 12px;
                color: #718096;
                text-align: center;
            }

            .loading {
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 40px;
                color: #718096;
                flex-direction: column;
                gap: 12px;
            }

            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid var(--primary-color);
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
            }

            .typing-indicator {
                align-self: flex-start;
                max-width: 80%;
                animation: slideIn 0.3s ease;
            }

            .typing-indicator .message-content {
                background: var(--message-bg);
                color: var(--text-color);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                border-bottom-left-radius: 4px;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .typing-dots {
                display: flex;
                gap: 4px;
            }

            .typing-dot {
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background-color: #9ca3af;
                animation: typingAnimation 1.4s infinite ease-in-out;
            }

            .typing-dot:nth-child(1) { animation-delay: 0ms; }
            .typing-dot:nth-child(2) { animation-delay: 200ms; }
            .typing-dot:nth-child(3) { animation-delay: 400ms; }

            .minimized .chat-messages,
            .minimized .chat-input-container {
                display: none;
            }

            @keyframes slideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            @keyframes typingAnimation {
                0%, 50%, 100% {
                    opacity: 0.3;
                    transform: scale(0.8);
                }
                25% {
                    opacity: 1;
                    transform: scale(1.2);
                }
            }

            /* Responsive design */
            @media (max-width: 768px) {
                .chatbot-container.floating {
                    width: calc(100vw - 20px);
                    height: calc(100vh - 100px);
                    bottom: 10px;
                    right: 10px;
                    left: 10px;
                }
                
                .message {
                    max-width: 90%;
                }
            }
        `;
    }

    getHTML() {
        const containerClass = this.mode === 'floating' ? 'chatbot-container floating' : 'chatbot-container';
        const showControls = this.mode === 'floating';

        return `
            <div class="${containerClass}" id="chatbot-container">
                <div class="chatbot-header" ${showControls ? 'onclick="this.getRootNode().host.toggleWidget()"' : ''}>
                    <h3 class="chatbot-title">${this.config.title}</h3>
                    ${showControls ? `
                        <div class="chatbot-controls">
                            <button class="control-btn" onclick="this.getRootNode().host.toggleWidget(); event.stopPropagation();" title="Minimize/Maximize">
                                <span id="toggle-icon">−</span>
                            </button>
                        </div>
                    ` : ''}
                </div>
                
                <div class="chat-messages" id="chat-messages">
                    ${this.isLoading ? `
                        <div class="loading">
                            <div class="spinner"></div>
                            <div>Loading chatbot...</div>
                        </div>
                    ` : `
                        <div class="message bot">
                            <div class="message-content">${this.config.welcomeMessage}</div>
                        </div>
                    `}
                </div>

                <div class="chat-input-container">
                    <div class="input-wrapper">
                        <input 
                            type="text" 
                            class="message-input" 
                            id="message-input"
                            placeholder="${this.isHumanSupportActive ? 'Chatting with human support...' : this.config.placeholder}"
                            ${this.isLoading ? 'disabled' : ''}
                        >
                        <button 
                            class="send-button" 
                            id="send-button"
                            ${this.isLoading ? 'disabled' : ''}
                        >
                            Send
                        </button>
                    </div>
                    <div class="action-buttons">
                        ${!this.isHumanSupportActive ? `
                            <button 
                                class="human-support-button" 
                                id="human-support-button"
                                title="Request human support"
                            >
                                👤 Speak to Human
                            </button>
                        ` : `
                            <div class="support-status">
                                <span class="status-indicator ${this.humanSupportRequest?.status || 'pending'}"></span>
                                Human Support ${this.humanSupportRequest?.status || 'pending'}
                            </div>
                        `}
                    </div>
                    <div class="status" id="status">
                        ${this.isLoading ? 'Connecting...' : 'Ready'}
                    </div>
                </div>
            </div>
        `;
    }

    bindEvents() {
        const messageInput = this.shadowRoot.getElementById('message-input');
        const sendButton = this.shadowRoot.getElementById('send-button');
        const humanSupportButton = this.shadowRoot.getElementById('human-support-button');

        if (messageInput && sendButton) {
            messageInput.addEventListener('keypress', this.handleKeyPress);
            messageInput.addEventListener('input', (e) => {
                sendButton.disabled = !e.target.value.trim() || this.isLoading;
            });
            sendButton.addEventListener('click', this.sendMessage);
        }

        if (humanSupportButton) {
            humanSupportButton.addEventListener('click', () => this.requestHumanSupport());
        }
    }

    toggleWidget() {
        if (this.mode !== 'floating') return;

        const container = this.shadowRoot.getElementById('chatbot-container');
        const toggleIcon = this.shadowRoot.getElementById('toggle-icon');
        
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            container.classList.add('minimized');
            if (toggleIcon) toggleIcon.textContent = '+';
        } else {
            container.classList.remove('minimized');
            if (toggleIcon) toggleIcon.textContent = '−';
        }
    }

    handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    async initializeChatbot() {
        if (!this.chatbotId) {
            this.updateStatus('Error: No chatbot ID provided');
            return;
        }

        try {
            // Load chatbot details
            const response = await fetch(`${this.apiBase}/chatbots/${this.chatbotId}`, {
                headers: this.getRequestHeaders()
            });
            if (!response.ok) {
                throw new Error(`Chatbot not found: ${response.statusText}`);
            }
            
            this.chatbot = await response.json();
            
            if (!this.chatbot.is_active) {
                throw new Error('Chatbot is not active');
            }

            // Handle session creation or restoration
            if (this.urlSessionId) {
                await this.restoreOrCreateSession();
            } else {
                await this.createNewSession();
            }

            // Update UI
            this.setLoading(false);
            this.updateStatus('Connected');
            
            // Update title and welcome message
            const titleElement = this.shadowRoot.querySelector('.chatbot-title');
            if (titleElement && this.getAttribute('data-title') === null) {
                titleElement.textContent = this.chatbot.name;
            }

            // Update welcome message if not customized
            if (this.config.welcomeMessage === 'Hello! How can I help you today?') {
                this.config.welcomeMessage = `Hello! I'm ${this.chatbot.name}. ${this.chatbot.description || 'How can I help you today?'}`;
                this.updateWelcomeMessage();
            }

        } catch (error) {
            console.error('Error initializing chatbot:', error);
            this.updateStatus(`Error: ${error.message}`);
            this.showError(error.message);
        }
    }
    
    async restoreOrCreateSession() {
        try {
            // Try to restore the session
            const response = await fetch(`${this.apiBase}/chat/sessions/${this.urlSessionId}/info`, {
                headers: this.getRequestHeaders()
            });
            
            if (response.ok) {
                const sessionInfo = await response.json();
                
                // Verify session belongs to current chatbot and is active
                if (sessionInfo.chatbot_id === this.chatbot.id && sessionInfo.chatbot_active) {
                    this.sessionId = this.urlSessionId;
                    
                    // Load chat history if available
                    if (sessionInfo.has_messages) {
                        await this.loadChatHistory();
                    }
                    
                    this.updateStatus('Session restored');
                    return;
                }
            }
            
            // If restoration failed, create new session
            console.log('Session restoration failed, creating new session');
            await this.createNewSession();
            
        } catch (error) {
            console.error('Error restoring session:', error);
            await this.createNewSession();
        }
    }
    
    async createNewSession() {
        const sessionResponse = await fetch(`${this.apiBase}/chat/sessions`, {
            method: 'POST',
            headers: this.getRequestHeaders(),
            body: JSON.stringify({
                chatbot_id: this.chatbot.id
            })
        });

        if (!sessionResponse.ok) {
            throw new Error('Failed to create chat session');
        }

        const sessionData = await sessionResponse.json();
        this.sessionId = sessionData.session_id;
        
        // Only update URL if this is a new session (not restoring from URL)
        if (!this.urlSessionId) {
            this.updateURL();
        }
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`${this.apiBase}/chat/sessions/${this.sessionId}/history?limit=50`, {
                headers: this.getRequestHeaders()
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Clear welcome message
                this.clearMessages();
                
                // Add historical messages
                data.history.forEach(msg => {
                    this.addMessage(msg.message, 'user');
                    this.addMessage(msg.response, 'bot');
                });
                
                this.updateStatus(`Loaded ${data.returned_messages} messages`);
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
        }
    }
    
    updateURL() {
        if (!this.chatbot || !this.sessionId) return;
        
        const url = new URL(window.location);
        url.searchParams.set('chatbot', this.chatbot.id);
        url.searchParams.set('session', this.sessionId);
        
        // Update URL without page reload
        window.history.pushState({}, '', url);
    }
    
    clearMessages() {
        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (messagesContainer) {
            messagesContainer.innerHTML = '';
        }
    }

    async sendMessage() {
        const messageInput = this.shadowRoot.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message || !this.sessionId || this.isLoading) return;

        // Add user message to chat
        this.addMessage(message, 'user');
        messageInput.value = '';
        
        // Update send button state
        const sendButton = this.shadowRoot.getElementById('send-button');
        sendButton.disabled = true;

        try {
            // If human support is active, send message through human support channel
            if (this.isHumanSupportActive && this.humanSupportRequest) {
                await this.sendHumanSupportMessage(message);
                this.updateStatus('Message sent to support');
                return;
            }

            // Show typing indicator for bot responses
            this.showTypingIndicator();
            this.updateStatus('Thinking...');

            const response = await fetch(`${this.apiBase}/chat/`, {
                method: 'POST',
                headers: this.getRequestHeaders(),
                body: JSON.stringify({
                    message: message,
                    chatbot_id: this.chatbot.id,
                    session_id: this.sessionId
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to send message');
            }

            const data = await response.json();
            
            // Hide typing indicator
            this.hideTypingIndicator();
            
            // Add bot response
            this.addMessage(data.response, 'bot');
            
            // Show sources if available
            if (data.context_used && data.sources && data.sources.length > 0) {
                this.addSourcesInfo(data.sources);
            }

            this.updateStatus('Connected');

        } catch (error) {
            console.error('Error sending message:', error);
            this.hideTypingIndicator();
            if (this.isHumanSupportActive) {
                this.addMessage(`Sorry, there was an error sending your message to support: ${error.message}`, 'bot');
                this.updateStatus('Error sending to support');
            } else {
                this.addMessage(`Sorry, I encountered an error: ${error.message}`, 'bot');
                this.updateStatus('Error occurred');
            }
        } finally {
            // Re-enable send button
            sendButton.disabled = false;
        }
    }

    // Utility methods for markdown parsing (simplified version)
    parseMarkdown(text) {
        return text
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/\*([^*]+)\*/g, '<em>$1</em>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    addMessage(content, type = 'bot', senderLabel = null) {
        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (!messagesContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const senderInfo = senderLabel ? `<div class="message-sender">${senderLabel}</div>` : '';
        messageDiv.innerHTML = `
            ${senderInfo}
            <div class="message-content">${type === 'bot' ? this.parseMarkdown(content) : content}</div>
        `;

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    showTypingIndicator() {
        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (!messagesContainer || this.typingIndicator) return;

        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'typing-indicator';
        this.typingIndicator.innerHTML = `
            <div class="message-content">
                <div class="typing-dots">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        `;

        messagesContainer.appendChild(this.typingIndicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }

    async requestHumanSupport() {
        try {
            // Show modal to collect user details
            const userDetails = await this.showHumanSupportModal();
            if (!userDetails) return; // User cancelled

            const response = await fetch(`${this.apiBase}/human-support/request`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    chatbot_id: this.chatbot.id,
                    session_id: this.sessionId,
                    initial_message: userDetails.message,
                    user_name: userDetails.name,
                    user_email: userDetails.email
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            this.humanSupportRequest = result;
            this.isHumanSupportActive = true;

            // Connect to WebSocket for real-time communication
            this.connectWebSocket(result.request_id);

            // Add system message about human support
            this.addMessage('bot', result.message);
            
            // Re-render to update UI
            this.render();

        } catch (error) {
            console.error('Error requesting human support:', error);
            this.addMessage('bot', 'Sorry, there was an error requesting human support. Please try again.');
        }
    }

    showHumanSupportModal() {
        return new Promise((resolve) => {
            // Create modal overlay
            const modalOverlay = document.createElement('div');
            modalOverlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            `;

            const modal = document.createElement('div');
            modal.style.cssText = `
                background: white;
                padding: 30px;
                border-radius: 10px;
                max-width: 400px;
                width: 90%;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
            `;

            modal.innerHTML = `
                <h3 style="margin: 0 0 20px 0; color: #1a202c;">Request Human Support</h3>
                <p style="color: #4a5568; margin-bottom: 20px;">Please provide some details so our support team can help you better.</p>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #2d3748; font-weight: 500;">Your Name (Optional)</label>
                    <input type="text" id="support-name" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px;">
                </div>
                
                <div style="margin-bottom: 15px;">
                    <label style="display: block; margin-bottom: 5px; color: #2d3748; font-weight: 500;">Your Email (Optional)</label>
                    <input type="email" id="support-email" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px;">
                </div>
                
                <div style="margin-bottom: 20px;">
                    <label style="display: block; margin-bottom: 5px; color: #2d3748; font-weight: 500;">How can we help? *</label>
                    <textarea id="support-message" placeholder="Please describe your issue or question..." style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 14px; min-height: 80px; resize: vertical;" required></textarea>
                </div>
                
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button id="cancel-support" style="padding: 10px 20px; border: 1px solid #e2e8f0; background: white; color: #4a5568; border-radius: 6px; cursor: pointer;">Cancel</button>
                    <button id="submit-support" style="padding: 10px 20px; border: none; background: #3182ce; color: white; border-radius: 6px; cursor: pointer;">Request Support</button>
                </div>
            `;

            modalOverlay.appendChild(modal);
            document.body.appendChild(modalOverlay);

            // Handle form submission
            const submitBtn = modal.querySelector('#submit-support');
            const cancelBtn = modal.querySelector('#cancel-support');
            const messageTextarea = modal.querySelector('#support-message');

            const cleanup = () => {
                document.body.removeChild(modalOverlay);
            };

            submitBtn.addEventListener('click', () => {
                const name = modal.querySelector('#support-name').value.trim();
                const email = modal.querySelector('#support-email').value.trim();
                const message = messageTextarea.value.trim();

                if (!message) {
                    alert('Please describe how we can help you.');
                    return;
                }

                cleanup();
                resolve({ name, email, message });
            });

            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve(null);
            });

            // Close on overlay click
            modalOverlay.addEventListener('click', (e) => {
                if (e.target === modalOverlay) {
                    cleanup();
                    resolve(null);
                }
            });

            // Focus on message textarea
            setTimeout(() => messageTextarea.focus(), 100);
        });
    }

    connectWebSocket(requestId) {
        try {
            const wsUrl = this.apiBase.replace('http://', 'ws://').replace('https://', 'wss://');
            this.websocket = new WebSocket(`${wsUrl}/human-support/ws/${requestId}`);

            this.websocket.onopen = () => {
                console.log('WebSocket connected for human support');
                // Send ping to keep connection alive
                setInterval(() => {
                    if (this.websocket.readyState === WebSocket.OPEN) {
                        this.websocket.send(JSON.stringify({ type: 'ping' }));
                    }
                }, 30000);
            };

            this.websocket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this.handleWebSocketMessage(data);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };

            this.websocket.onclose = () => {
                console.log('WebSocket connection closed');
                this.websocket = null;
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.websocket = null;
            };

        } catch (error) {
            console.error('Error connecting WebSocket:', error);
        }
    }

    handleWebSocketMessage(data) {
        switch (data.type) {
            case 'new_message':
                // Add the message to the chat
                this.addMessage(
                    data.data.sender_type === 'admin' ? 'bot' : 'user',
                    data.data.message,
                    data.data.sender_type === 'admin' ? 'Support Agent' : null
                );
                break;

            case 'admin_joined':
                this.humanSupportRequest.status = 'active';
                this.addMessage('bot', data.message);
                this.render(); // Re-render to update status
                break;

            case 'request_resolved':
                this.humanSupportRequest.status = 'resolved';
                this.addMessage('bot', data.message);
                this.render(); // Re-render to update status
                break;

            case 'request_closed':
                this.humanSupportRequest.status = 'closed';
                this.addMessage('bot', data.message);
                this.isHumanSupportActive = false;
                this.render(); // Re-render to show normal interface
                break;

            case 'pong':
                // Keep-alive response
                break;

            default:
                console.log('Unknown WebSocket message type:', data.type);
        }
    }

    async sendHumanSupportMessage(message) {
        try {
            const response = await fetch(`${this.apiBase}/human-support/requests/${this.humanSupportRequest.request_id}/messages`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    sender_type: 'user'
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Message will be broadcast via WebSocket to all connected clients
            return await response.json();

        } catch (error) {
            console.error('Error sending human support message:', error);
            throw error;
        }
    }

    updateStatus(message) {
        const statusElement = this.shadowRoot.getElementById('status');
        if (statusElement) {
            statusElement.textContent = message;
        }
    }

    setLoading(loading) {
        this.isLoading = loading;
        const messageInput = this.shadowRoot.getElementById('message-input');
        const sendButton = this.shadowRoot.getElementById('send-button');
        
        if (messageInput && sendButton) {
            messageInput.disabled = loading;
            sendButton.disabled = loading || !messageInput.value.trim();
        }
    }

    updateWelcomeMessage() {
        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (!messagesContainer) return;

        // Clear loading content and add welcome message
        messagesContainer.innerHTML = `
            <div class="message bot">
                <div class="message-content">${this.parseMarkdown(this.config.welcomeMessage)}</div>
            </div>
        `;
    }

    showError(errorMessage) {
        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (!messagesContainer) return;

        messagesContainer.innerHTML = `
            <div class="message bot">
                <div class="message-content" style="color: #f56565; border-color: #f56565;">
                    ❌ Error: ${errorMessage}
                </div>
            </div>
        `;
    }

    addSourcesInfo(sources) {
        if (!sources || sources.length === 0) return;

        const sourcesText = sources.length === 1 
            ? `Source: ${sources[0]}`
            : `Sources: ${sources.join(', ')}`;

        const messagesContainer = this.shadowRoot.getElementById('chat-messages');
        if (!messagesContainer) return;

        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message bot';
        sourcesDiv.innerHTML = `
            <div class="message-content" style="font-size: 12px; opacity: 0.8; font-style: italic;">
                📄 ${sourcesText}
            </div>
        `;

        messagesContainer.appendChild(sourcesDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}

// Register the custom element
if (!customElements.get('lt-chatbot')) {
    customElements.define('lt-chatbot', LTChatbot);
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LTChatbot;
}