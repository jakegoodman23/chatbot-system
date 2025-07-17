const API_BASE = '/api';

class ChatApp {
    constructor() {
        this.sessionId = null;
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.status = document.getElementById('status');
        this.contextInfo = document.getElementById('contextInfo');
        this.sourcesList = document.getElementById('sourcesList');
        this.typingIndicator = null; // Reference to typing indicator element
        
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
        this.createSession();
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

    async createSession() {
        try {
            const response = await fetch(`${API_BASE}/chat/sessions`, {
                method: 'POST'
            });
            if (response.ok) {
                const data = await response.json();
                this.sessionId = data.session_id;
                this.status.textContent = 'Ready to chat';
            }
        } catch (error) {
            console.error('Error creating session:', error);
            this.status.textContent = 'Error creating chat session';
        }
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
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || !this.sessionId) return;

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
                    session_id: this.sessionId
                })
            });

            if (response.ok) {
                const data = await response.json();
                
                // Hide typing indicator before showing response
                this.hideTypingIndicator();
                
                this.addMessage(data.response, 'bot');
                
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

    addMessage(content, type) {
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
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
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