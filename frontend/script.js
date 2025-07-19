const API_BASE = '/api';

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.chatbot = null;
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.status = document.getElementById('status');
        this.contextInfo = document.getElementById('contextInfo');
        this.sourcesList = document.getElementById('sourcesList');
        this.chatbotInfo = document.getElementById('chatbotInfo');
        this.chatbotName = document.getElementById('chatbotName');
        this.chatbotDescription = document.getElementById('chatbotDescription');
        this.backToSelectBtn = document.getElementById('backToSelectBtn');
        this.shareChatBtn = document.getElementById('shareChatBtn');
        this.typingIndicator = null; // Reference to typing indicator element
        this.isSharedLink = false; // Track if loading from shared URL
        
        // Check if all elements exist
        if (!this.messageInput || !this.sendButton || !this.chatMessages || !this.status) {
            console.error('Critical DOM elements not found:', {
                messageInput: !!this.messageInput,
                sendButton: !!this.sendButton,
                chatMessages: !!this.chatMessages,
                status: !!this.status
            });
            return;
        }
        
        this.init();
    }

    // Simple markdown parser
    parseMarkdown(text) {
        return text
            // Code blocks (must be first to avoid interference)
            .replace(/```([^`]+)```/g, '<pre><code>$1</code></pre>')
            // Headers
            .replace(/^### (.+$)/gm, '<h3>$1</h3>')
            .replace(/^## (.+$)/gm, '<h2>$1</h2>')
            .replace(/^# (.+$)/gm, '<h1>$1</h1>')
            // Bold (before italic to avoid conflicts)
            .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
            .replace(/__([^_]+)__/g, '<strong>$1</strong>')
            // Italic
            .replace(/\*([^*\s][^*]*[^*\s])\*/g, '<em>$1</em>')
            .replace(/_([^_\s][^_]*[^_\s])_/g, '<em>$1</em>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
            // Lists (wrap consecutive list items in ul tags)
            .replace(/(^[\*\-] .+$\n?)+/gm, (match) => {
                const items = match.trim().split('\n').map(line => 
                    line.replace(/^[\*\-] (.+$)/, '<li>$1</li>')
                ).join('');
                return `<ul>${items}</ul>`;
            })
            // Numbered lists
            .replace(/(^\d+\. .+$\n?)+/gm, (match) => {
                const items = match.trim().split('\n').map(line => 
                    line.replace(/^\d+\. (.+$)/, '<li>$1</li>')
                ).join('');
                return `<ol>${items}</ol>`;
            })
            // Paragraphs (double line breaks)
            .replace(/\n\n/g, '</p><p>')
            // Single line breaks
            .replace(/\n/g, '<br>')
            // Wrap in paragraph tags
            .replace(/^(.*)$/gm, (match) => {
                // Don't wrap if already wrapped in HTML tags
                if (match.match(/^<[\/]?(h[1-6]|ul|ol|li|pre|code)/)) {
                    return match;
                }
                return match ? `<p>${match}</p>` : '';
            })
            // Clean up empty paragraphs and fix nested tags
            .replace(/<p><\/p>/g, '')
            .replace(/<p>(<[\/]?(h[1-6]|ul|ol|pre))/g, '$1')
            .replace(/(<\/[\/]?(h[1-6]|ul|ol|pre)>)<\/p>/g, '$1');
    }

    async init() {
        await this.checkServerHealth();
        await this.loadChatbot();
        this.setupEventListeners();
    }

    async checkServerHealth() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            if (response.ok) {
                this.status.textContent = 'Connected to server';
                this.messageInput.disabled = false;
                this.sendButton.disabled = false;
            } else {
                throw new Error('Server not healthy');
            }
        } catch (error) {
            this.status.textContent = 'Server unavailable - check if backend is running';
            console.error('Server health check failed:', error);
        }
    }

    async loadChatbot() {
        // Check if chatbot and session are provided from URL
        const urlParams = new URLSearchParams(window.location.search);
        const chatbotId = urlParams.get('chatbot');
        const sessionId = urlParams.get('session');
        
        // If both chatbot and session are in URL, this is a shared link
        this.isSharedLink = !!(chatbotId && sessionId);
        
        if (chatbotId) {
            // Load chatbot from API
            try {
                const response = await fetch(`${API_BASE}/chatbots/${chatbotId}`);
                if (response.ok) {
                    this.chatbot = await response.json();
                    localStorage.setItem('selectedChatbot', JSON.stringify(this.chatbot));
                } else {
                    throw new Error('Chatbot not found');
                }
            } catch (error) {
                console.error('Error loading chatbot:', error);
                this.redirectToSelection();
                return;
            }
        } else {
            // Try to load from localStorage
            const stored = localStorage.getItem('selectedChatbot');
            if (stored) {
                try {
                    this.chatbot = JSON.parse(stored);
                } catch (error) {
                    console.error('Error parsing stored chatbot:', error);
                    this.redirectToSelection();
                    return;
                }
            } else {
                this.redirectToSelection();
                return;
            }
        }
        
        if (!this.chatbot || !this.chatbot.is_active) {
            this.redirectToSelection();
            return;
        }
        
        // Display chatbot info
        this.displayChatbotInfo();
        
        // Handle session restoration or creation
        if (sessionId) {
            console.log(`Attempting to restore session: ${sessionId}`);
            await this.restoreSession(sessionId);
        } else {
            console.log('No session ID in URL, creating new session');
            await this.createSession();
        }
    }
    
    displayChatbotInfo() {
        this.chatbotName.textContent = this.chatbot.name;
        this.chatbotDescription.textContent = this.chatbot.description || 'No description';
        this.chatbotInfo.style.display = 'flex';
        
        // Update welcome message
        const welcomeMsg = this.chatMessages.querySelector('.bot-message .message-content');
        if (welcomeMsg) {
            welcomeMsg.innerHTML = `Hello! I'm <strong>${this.chatbot.name}</strong>. ${this.chatbot.description || 'I can help answer questions based on uploaded documents.'} How can I assist you today?`;
        }
        
        // Load and display suggested questions
        this.loadSuggestedQuestions();
    }
    
    async loadSuggestedQuestions() {
        try {
            const response = await fetch(`${API_BASE}/chatbots/${this.chatbot.id}/suggested-questions`);
            if (response.ok) {
                const questions = await response.json();
                if (questions.length > 0) {
                    this.displaySuggestedQuestions(questions);
                }
            }
        } catch (error) {
            console.error('Error loading suggested questions:', error);
        }
    }
    
    displaySuggestedQuestions(questions) {
        // Only show suggested questions if there are no existing messages (except welcome)
        const existingMessages = this.chatMessages.querySelectorAll('.message');
        const hasUserMessages = Array.from(existingMessages).some(msg => msg.classList.contains('user-message'));
        
        if (hasUserMessages) {
            return; // Don't show suggested questions if user has already started chatting
        }
        
        const suggestedQuestionsDiv = document.createElement('div');
        suggestedQuestionsDiv.className = 'suggested-questions';
        suggestedQuestionsDiv.innerHTML = `
            <div class="suggested-questions-title">Here are some questions you can try:</div>
            <div class="suggested-questions-buttons">
                ${questions.map(q => `
                    <button class="suggested-question-btn" data-question="${q.question_text}">
                        ${q.question_text}
                    </button>
                `).join('')}
            </div>
        `;
        
        // Add click handlers for suggested question buttons
        suggestedQuestionsDiv.addEventListener('click', (e) => {
            if (e.target.classList.contains('suggested-question-btn')) {
                const questionText = e.target.getAttribute('data-question');
                this.messageInput.value = questionText;
                
                // Remove suggested questions after user clicks one
                suggestedQuestionsDiv.remove();
                
                // Auto-send the message
                this.sendMessage();
            }
        });
        
        this.chatMessages.appendChild(suggestedQuestionsDiv);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    redirectToSelection() {
        window.location.href = 'select.html';
    }

    async restoreSession(sessionId) {
        try {
            console.log(`Fetching session info for: ${sessionId}`);
            // Validate session exists and belongs to the chatbot
            const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/info`);
            
            if (!response.ok) {
                console.log(`Session not found (${response.status}), showing error`);
                this.handleSessionRestorationError('Session not found or has expired');
                return;
            }
            
            const sessionInfo = await response.json();
            console.log('Session info received:', sessionInfo);
            
            // Verify session belongs to the current chatbot
            if (sessionInfo.chatbot_id !== this.chatbot.id) {
                console.log(`Session belongs to different chatbot (${sessionInfo.chatbot_id} vs ${this.chatbot.id})`);
                this.handleSessionRestorationError('This session belongs to a different chatbot');
                return;
            }
            
            // Check if chatbot is still active
            if (!sessionInfo.chatbot_active) {
                console.log('Chatbot is no longer active');
                this.handleSessionRestorationError('This chatbot is no longer active');
                return;
            }
            
            // Use the existing session (don't call updateURL to preserve the shared URL)
            this.sessionId = sessionId;
            console.log(`Successfully restored session: ${sessionId}`);
            
            // Load chat history if it exists
            if (sessionInfo.has_messages) {
                console.log(`Loading ${sessionInfo.message_count} messages from history`);
                await this.loadChatHistory();
            }
            
            this.showShareButton();
            this.status.textContent = 'Session restored - Ready to chat';
            
        } catch (error) {
            console.error('Error restoring session:', error);
            this.handleSessionRestorationError('Unable to restore session');
        }
    }
    
    handleSessionRestorationError(message) {
        // Show error message
        this.status.textContent = message;
        
        // Disable chat functionality
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
        
        // Add error message to chat
        this.addMessage(`⚠️ ${message}. Please start a new chat session.`, 'bot');
        
        // Show option to start new chat
        const startNewBtn = document.createElement('button');
        startNewBtn.className = 'btn-primary';
        startNewBtn.textContent = 'Start New Chat';
        startNewBtn.style.marginTop = '10px';
        startNewBtn.onclick = () => {
            // Clear URL parameters and reload
            window.location.href = `index.html?chatbot=${this.chatbot.id}`;
        };
        
        const lastMessage = this.chatMessages.lastElementChild;
        if (lastMessage) {
            lastMessage.appendChild(startNewBtn);
        }
    }
    
    async loadChatHistory() {
        try {
            const response = await fetch(`${API_BASE}/chat/sessions/${this.sessionId}/history?limit=50`);
            
            if (response.ok) {
                const data = await response.json();
                
                // Clear current messages (except welcome message if it's the only one)
                const messages = this.chatMessages.querySelectorAll('.message');
                if (messages.length <= 1) {
                    this.chatMessages.innerHTML = '';
                } else {
                    // Remove all messages except the first (welcome) message
                    for (let i = 1; i < messages.length; i++) {
                        messages[i].remove();
                    }
                }
                
                // Add historical messages
                data.history.forEach(msg => {
                    this.addMessage(msg.message, 'user');
                    this.addMessage(msg.response, 'bot', msg.id);
                    
                    // Apply feedback state if exists
                    if (msg.feedback) {
                        this.applyFeedbackState(msg.id, msg.feedback.type);
                    }
                });
                
                this.status.textContent = `Loaded ${data.returned_messages} messages from history`;
            }
        } catch (error) {
            console.error('Error loading chat history:', error);
            this.status.textContent = 'Could not load chat history';
        }
    }

    applyFeedbackState(messageId, feedbackType) {
        // Find the feedback buttons for this message
        const messages = this.chatMessages.querySelectorAll('.bot-message');
        for (const messageDiv of messages) {
            const feedbackDiv = messageDiv.querySelector('.message-feedback');
            if (feedbackDiv) {
                const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
                const targetClass = feedbackType === 'thumbs_up' ? 'thumbs-up' : 'thumbs-down';
                
                buttons.forEach(btn => btn.classList.remove('selected'));
                
                const targetButton = feedbackDiv.querySelector(`.${targetClass}`);
                if (targetButton) {
                    targetButton.classList.add('selected');
                }
                break;
            }
        }
    }

    async createSession() {
        if (!this.chatbot) {
            this.redirectToSelection();
            return;
        }
        
        try {
            const response = await fetch(`${API_BASE}/chat/sessions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    chatbot_id: this.chatbot.id
                })
            });
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.updateURL();
                this.showShareButton();
                this.status.textContent = 'Ready to chat';
            }
        } catch (error) {
            console.error('Error creating session:', error);
            this.status.textContent = 'Error creating chat session';
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
    
    showShareButton() {
        if (this.shareChatBtn && this.sessionId) {
            this.shareChatBtn.style.display = 'inline-block';
        }
    }
    
    shareChat() {
        if (!this.chatbot || !this.sessionId) {
            this.status.textContent = 'No session available to share';
            return;
        }
        
        const shareUrl = new URL(window.location.origin + window.location.pathname);
        shareUrl.searchParams.set('chatbot', this.chatbot.id);
        shareUrl.searchParams.set('session', this.sessionId);
        
        // Copy to clipboard
        navigator.clipboard.writeText(shareUrl.toString()).then(() => {
            // Show temporary success message
            const originalText = this.shareChatBtn.textContent;
            this.shareChatBtn.textContent = '✓ Copied!';
            this.shareChatBtn.style.backgroundColor = '#48bb78';
            
            setTimeout(() => {
                this.shareChatBtn.textContent = originalText;
                this.shareChatBtn.style.backgroundColor = '';
            }, 2000);
            
            this.status.textContent = 'Chat link copied to clipboard!';
            
            setTimeout(() => {
                this.status.textContent = 'Ready to chat';
            }, 3000);
            
        }).catch(err => {
            console.error('Failed to copy to clipboard:', err);
            
            // Fallback: show the URL in an alert
            alert(`Share this URL:\n\n${shareUrl.toString()}`);
            this.status.textContent = 'Share URL displayed in dialog';
        });
    }

    setupEventListeners() {
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.messageInput.addEventListener('input', () => {
            this.sendButton.disabled = !this.messageInput.value.trim();
        });
        
        this.backToSelectBtn.addEventListener('click', () => {
            this.redirectToSelection();
        });
        
        this.shareChatBtn.addEventListener('click', () => {
            this.shareChat();
        });
    }

    async sendMessage() {
        console.log('sendMessage called');
        const message = this.messageInput.value.trim();
        console.log('Message:', message, 'SessionId:', this.sessionId, 'ChatbotId:', this.chatbot?.id);
        
        if (!message) {
            console.log('No message provided');
            return;
        }
        
        if (!this.sessionId) {
            console.log('No session ID available');
            this.status.textContent = 'No session available. Please refresh the page.';
            return;
        }
        
        if (!this.chatbot) {
            console.log('No chatbot available');
            this.status.textContent = 'No chatbot selected. Redirecting...';
            this.redirectToSelection();
            return;
        }

        // Disable input while processing
        this.messageInput.disabled = true;
        this.sendButton.disabled = true;
        this.status.textContent = 'Thinking...';

        // Add user message to chat
        this.addMessage(message, 'user');
        this.messageInput.value = '';

        // Show typing indicator
        this.showTypingIndicator();

        try {
            const response = await fetch(`${API_BASE}/chat/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    chatbot_id: this.chatbot.id,
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Hide typing indicator before showing response
                this.hideTypingIndicator();
                
                this.addMessage(data.response, 'bot', data.message_id);
                
                // Show context sources if available
                if (data.context_used && data.sources.length > 0) {
                    this.showContextSources(data.sources);
                } else {
                    this.hideContextSources();
                }
                
                this.status.textContent = 'Ready to chat';
            } else {
                throw new Error('Failed to get response');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            
            // Hide typing indicator before showing error
            this.hideTypingIndicator();
            
            this.addMessage('Sorry, I encountered an error. Please try again.', 'bot');
            this.status.textContent = 'Error occurred';
        } finally {
            // Re-enable input
            this.messageInput.disabled = false;
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }

    addMessage(content, type, messageId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        if (type === 'bot') {
            // Parse markdown for bot messages
            contentDiv.innerHTML = this.parseMarkdown(content);
        } else {
            // Keep user messages as plain text
            contentDiv.textContent = content;
        }
        
        messageDiv.appendChild(contentDiv);
        
        // Add feedback buttons for bot messages (except error messages)
        if (type === 'bot' && messageId && !content.includes('Sorry, I encountered an error')) {
            const feedbackDiv = this.createFeedbackButtons(messageId);
            messageDiv.appendChild(feedbackDiv);
        }
        
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    createFeedbackButtons(messageId) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'message-feedback';
        
        const thumbsUpBtn = document.createElement('button');
        thumbsUpBtn.className = 'feedback-btn thumbs-up';
        thumbsUpBtn.innerHTML = '👍';
        thumbsUpBtn.title = 'This was helpful';
        thumbsUpBtn.onclick = () => this.submitFeedback(messageId, 'thumbs_up', thumbsUpBtn);
        
        const thumbsDownBtn = document.createElement('button');
        thumbsDownBtn.className = 'feedback-btn thumbs-down';
        thumbsDownBtn.innerHTML = '👎';
        thumbsDownBtn.title = 'This was not helpful';
        thumbsDownBtn.onclick = () => this.submitFeedback(messageId, 'thumbs_down', thumbsDownBtn);
        
        feedbackDiv.appendChild(thumbsUpBtn);
        feedbackDiv.appendChild(thumbsDownBtn);
        
        return feedbackDiv;
    }

    async submitFeedback(messageId, feedbackType, button) {
        try {
            const response = await fetch(`${API_BASE}/chat/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message_id: messageId,
                    feedback_type: feedbackType
                })
            });

            if (response.ok) {
                // Update button visual state
                const feedbackDiv = button.parentElement;
                const buttons = feedbackDiv.querySelectorAll('.feedback-btn');
                
                // Reset all buttons
                buttons.forEach(btn => {
                    btn.classList.remove('selected');
                    btn.disabled = false;
                });
                
                // Mark selected button
                button.classList.add('selected');
                
                // Show brief confirmation
                const originalContent = button.innerHTML;
                button.innerHTML = feedbackType === 'thumbs_up' ? '✓' : '✗';
                
                setTimeout(() => {
                    button.innerHTML = originalContent;
                }, 1000);
                
                console.log(`Feedback submitted: ${feedbackType} for message ${messageId}`);
                
            } else {
                throw new Error('Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            
            // Show error state briefly
            const originalContent = button.innerHTML;
            button.innerHTML = '⚠️';
            button.style.opacity = '0.5';
            
            setTimeout(() => {
                button.innerHTML = originalContent;
                button.style.opacity = '1';
            }, 2000);
        }
    }

    showContextSources(sources) {
        this.contextInfo.style.display = 'block';
        this.sourcesList.innerHTML = sources
            .filter((source, index, self) => self.indexOf(source) === index) // Remove duplicates
            .map(source => `<li>📄 ${source}</li>`)
            .join('');
    }

    hideContextSources() {
        this.contextInfo.style.display = 'none';
    }

    showTypingIndicator() {
        // Remove any existing typing indicator first
        this.hideTypingIndicator();
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        typingDiv.id = 'typingIndicator';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const dotsDiv = document.createElement('div');
        dotsDiv.className = 'typing-dots';
        
        // Create three animated dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'typing-dot';
            dotsDiv.appendChild(dot);
        }
        
        contentDiv.appendChild(dotsDiv);
        typingDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(typingDiv);
        this.typingIndicator = typingDiv;
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }
}

// Initialize the chat app when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});