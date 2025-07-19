# Local Multi-Chatbot Platform with RAG

A locally-hosted multi-chatbot platform with document ingestion capabilities, built with FastAPI, PostgreSQL with pgvector, and vanilla JavaScript. Create multiple specialized chatbots, each with their own document knowledge base and system prompts.

## Features

- 🤖 **Multiple specialized chatbots** - Create unlimited chatbots with individual personalities and knowledge bases
- 📄 **Per-chatbot document management** - Each chatbot has its own isolated document collection
- 🔍 **RAG-powered responses** using OpenAI embeddings and completions with vector similarity search
- 💬 **Modern chat interface** with markdown support, typing indicators, and session management
- 👍 **Message feedback system** - Users can give thumbs up/down feedback on bot responses
- ⚙️ **Comprehensive admin panel** with chatbot creation, document management, and analytics
- 🔗 **Embeddable widgets** - Generate embed codes to add chatbots to any website
- 🐳 **Docker containerization** for easy deployment and development
- 📊 **Chat history tracking** and detailed analytics per chatbot

## Architecture

- **Backend**: FastAPI with Python
- **Database**: PostgreSQL with pgvector extension for vector storage
- **Frontend**: Vanilla HTML/CSS/JavaScript with responsive design
- **Embeddings**: OpenAI text-embedding-ada-002
- **Chat**: OpenAI GPT-4o
- **File Processing**: PDF and TXT document support with intelligent chunking

## Quick Start

### Prerequisites

- Docker
- OpenAI API key

### Setup

1. **Clone and navigate to the project**:
   ```bash
   cd chatbot-local
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**:
   ```bash
   docker-compose exec backend python run_migrations.py
   ```

5. **Access the application**:
   - **Chatbot Selection**: http://localhost:3000/select.html
   - **Chat Interface**: http://localhost:3000/index.html (redirects to selection if no chatbot chosen)
   - **Admin Panel**: http://localhost:3000/admin.html
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

## Usage

### Creating Your First Chatbot

1. **Access Admin Panel**: Go to http://localhost:3000/admin.html
2. **Create Chatbot**: Click "Create New Chatbot"
   - Enter a unique name (e.g., "Customer Support Bot")
   - Add description (optional)
   - Define system prompt (personality and behavior)
3. **Upload Documents**: Click "📄 Manage Documents" on your chatbot
   - Upload PDF or TXT files relevant to this chatbot's purpose
   - Documents are processed and embedded automatically

### Chatting with Your Bots

1. **Select Chatbot**: Go to http://localhost:3000/select.html
2. **Choose a chatbot** from the available options
3. **Start chatting**: Ask questions related to the uploaded documents
4. **Switch chatbots**: Use "← Back to Selection" to try different bots

### Embedding Chatbots

1. **Get embed code**: In admin panel, click "🔗 Embed Code" on any chatbot
2. **Choose widget type**:
   - **Inline**: Embedded directly in page content
   - **Floating**: Minimizable chat bubble
   - **Custom**: Configurable height, width, and styling
3. **Copy and paste** the generated HTML into your website

## Development

### Running Locally (without Docker)

1. **Start PostgreSQL with pgvector**:
   ```bash
   docker run -d \
     --name postgres-pgvector \
     -e POSTGRES_PASSWORD=password \
     -e POSTGRES_DB=chatbot_db \
     -p 5432:5432 \
     pgvector/pgvector:pg16
   ```

2. **Set up backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   python run_migrations.py  # Run database migrations
   uvicorn app.main:app --reload --port 8000
   ```

3. **Serve frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
   # Or use any static file server
   ```

### API Endpoints

**Chatbot Management:**
- `GET /chatbots/` - List all chatbots
- `POST /chatbots/` - Create a new chatbot
- `GET /chatbots/{id}` - Get specific chatbot
- `PUT /chatbots/{id}` - Update chatbot
- `DELETE /chatbots/{id}` - Delete chatbot
- `POST /chatbots/{id}/activate` - Activate chatbot
- `POST /chatbots/{id}/deactivate` - Deactivate chatbot
- `GET /chatbots/{id}/documents` - Get chatbot's documents
- `POST /chatbots/{id}/documents` - Add document to chatbot
- `