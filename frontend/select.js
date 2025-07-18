class ChatbotSelector {
    constructor() {
        this.apiBase = '/api';
        this.chatbots = [];
        
        this.init();
    }
    
    async init() {
        this.bindEvents();
        await this.loadChatbots();
    }
    
    bindEvents() {
        // Create chatbot button
        document.getElementById('createChatbotBtn').addEventListener('click', () => {
            this.showCreateModal();
        });
        
        // Modal close events
        document.querySelector('.close').addEventListener('click', () => {
            this.hideCreateModal();
        });
        
        document.getElementById('cancelBtn').addEventListener('click', () => {
            this.hideCreateModal();
        });
        
        // Click outside modal to close
        document.getElementById('createModal').addEventListener('click', (e) => {
            if (e.target.id === 'createModal') {
                this.hideCreateModal();
            }
        });
        
        // Form submission
        document.getElementById('createChatbotForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.createChatbot();
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.hideCreateModal();
            }
        });
    }
    
    async loadChatbots() {
        const loading = document.getElementById('loading');
        const grid = document.getElementById('chatbotsGrid');
        
        try {
            loading.style.display = 'block';
            grid.innerHTML = '';
            
            const response = await fetch(`${this.apiBase}/chatbots/`);
            if (!response.ok) {
                throw new Error(`Failed to load chatbots: ${response.statusText}`);
            }
            
            this.chatbots = await response.json();
            this.renderChatbots();
            
        } catch (error) {
            console.error('Error loading chatbots:', error);
            this.showError('Failed to load chatbots. Please refresh the page.');
        } finally {
            loading.style.display = 'none';
        }
    }
    
    renderChatbots() {
        const grid = document.getElementById('chatbotsGrid');
        
        if (this.chatbots.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <h3>No Chatbots Yet</h3>
                    <p>Create your first chatbot to get started!</p>
                </div>
            `;
            return;
        }
        
        grid.innerHTML = this.chatbots.map(chatbot => `
            <div class="chatbot-card ${!chatbot.is_active ? 'inactive' : ''}" 
                 data-chatbot-id="${chatbot.id}"
                 onclick="chatbotSelector.selectChatbot(${chatbot.id})">
                <div class="chatbot-name">${this.escapeHtml(chatbot.name)}</div>
                <div class="chatbot-description">
                    ${chatbot.description ? this.escapeHtml(chatbot.description) : 'No description'}
                </div>
                <div class="chatbot-stats">
                    <div class="stat-item">
                        <span>📄</span>
                        <span>Documents: 0</span>
                    </div>
                    <div class="stat-item">
                        <span>💬</span>
                        <span>Chats: 0</span>
                    </div>
                </div>
            </div>
        `).join('');
        
        // Load stats for each chatbot
        this.loadChatbotStats();
    }
    
    async loadChatbotStats() {
        try {
            const response = await fetch(`${this.apiBase}/chatbots/stats/all`);
            if (!response.ok) return;
            
            const statsArray = await response.json();
            
            statsArray.forEach(stats => {
                const card = document.querySelector(`[data-chatbot-id="${stats.id}"]`);
                if (card) {
                    const statsDiv = card.querySelector('.chatbot-stats');
                    statsDiv.innerHTML = `
                        <div class="stat-item">
                            <span>📄</span>
                            <span>Documents: ${stats.document_count}</span>
                        </div>
                        <div class="stat-item">
                            <span>💬</span>
                            <span>Chats: ${stats.session_count}</span>
                        </div>
                    `;
                }
            });
        } catch (error) {
            console.error('Error loading chatbot stats:', error);
        }
    }
    
    async selectChatbot(chatbotId) {
        const chatbot = this.chatbots.find(cb => cb.id === chatbotId);
        if (!chatbot) {
            this.showError('Chatbot not found');
            return;
        }
        
        if (!chatbot.is_active) {
            this.showError('This chatbot is inactive. Please contact an administrator.');
            return;
        }
        
        // Store selected chatbot in localStorage for the chat interface
        localStorage.setItem('selectedChatbot', JSON.stringify(chatbot));
        
        // Redirect to chat interface
        window.location.href = `index.html?chatbot=${chatbotId}`;
    }
    
    showCreateModal() {
        document.getElementById('createModal').style.display = 'block';
        document.getElementById('chatbotName').focus();
    }
    
    hideCreateModal() {
        document.getElementById('createModal').style.display = 'none';
        document.getElementById('createChatbotForm').reset();
    }
    
    async createChatbot() {
        const form = document.getElementById('createChatbotForm');
        const formData = new FormData(form);
        
        const chatbotData = {
            name: formData.get('name').trim(),
            description: formData.get('description').trim() || null,
            system_prompt: formData.get('system_prompt').trim()
        };
        
        // Validation
        if (!chatbotData.name) {
            this.showError('Chatbot name is required');
            return;
        }
        
        if (!chatbotData.system_prompt) {
            this.showError('System prompt is required');
            return;
        }
        
        try {
            const submitBtn = form.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Creating...';
            submitBtn.disabled = true;
            
            const response = await fetch(`${this.apiBase}/chatbots/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(chatbotData)
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create chatbot');
            }
            
            const newChatbot = await response.json();
            
            this.hideCreateModal();
            await this.loadChatbots();
            
            // Show success message
            this.showSuccess(`Chatbot "${newChatbot.name}" created successfully!`);
            
        } catch (error) {
            console.error('Error creating chatbot:', error);
            this.showError(error.message || 'Failed to create chatbot');
        } finally {
            const submitBtn = form.querySelector('button[type="submit"]');
            submitBtn.textContent = 'Create Chatbot';
            submitBtn.disabled = false;
        }
    }
    
    showError(message) {
        // Create and show error notification
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #f56565;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1001;
            max-width: 400px;
            font-weight: 500;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    showSuccess(message) {
        // Create and show success notification
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #48bb78;
            color: white;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            z-index: 1001;
            max-width: 400px;
            font-weight: 500;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the chatbot selector when the page loads
const chatbotSelector = new ChatbotSelector();