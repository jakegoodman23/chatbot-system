# Local Multi-Chatbot Platform with RAG

A locally-hosted multi-chatbot platform with document ingestion capabilities, built with FastAPI, PostgreSQL with pgvector, and vanilla JavaScript. Create multiple specialized chatbots, each with their own document knowledge base and system prompts.

## Features

- 🤖 **Multiple specialized chatbots** - Create unlimited chatbots with individual personalities and knowledge bases
- 📄 **Per-chatbot document management** - Each chatbot has its own isolated document collection
- 🔍 **RAG-powered responses** using OpenAI embeddings and completions with vector similarity search
- 💬 **Modern chat interface** with markdown support, typing indicators, and session management
- 👍 **Message feedback system** - Users can give thumbs up/down feedback on bot responses
- 💬 **Suggested questions** - Pre-loaded questions help users get started quickly
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
   - **Chat Interface**: http://localhost:3000/index.html
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
4. **Add Suggested Questions**: Click "💬 Suggested Questions"
   - Add helpful starter questions for users
   - Questions appear as clickable buttons in the chat interface

### Chatting with Your Bots

1. **Select Chatbot**: Go to http://localhost:3000/select.html
2. **Choose a chatbot** from the available options
3. **Start chatting**: Click suggested questions or type your own
4. **Provide feedback**: Use 👍/👎 buttons to rate responses
5. **Switch chatbots**: Use "← Back to Selection" to try different bots

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
   python run_migrations.py
   uvicorn app.main:app --reload --port 8000
   ```

3. **Serve frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
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
- `DELETE /chatbots/{id}/documents/{doc_id}` - Remove document from chatbot

**Chat & Sessions:**
- `POST /chat/` - Send message to chatbot
- `POST /chat/feedback` - Submit thumbs up/down feedback for a message
- `GET /chat/feedback/stats/{chatbot_id}` - Get feedback statistics for a chatbot
- `POST /chat/sessions` - Create new chat session
- `GET /chat/sessions/{session_id}/history` - Get chat history

**Suggested Questions:**
- `GET /chatbots/{chatbot_id}/suggested-questions` - Get suggested questions for a chatbot
- `POST /chatbots/{chatbot_id}/suggested-questions` - Create a new suggested question
- `PUT /chatbots/{chatbot_id}/suggested-questions/{question_id}` - Update a suggested question
- `DELETE /chatbots/{chatbot_id}/suggested-questions/{question_id}` - Delete a suggested question

**Document Management:**
- `POST /documents/upload` - Upload document to specific chatbot
- `GET /documents/?chatbot_id={id}` - List documents for chatbot
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/chatbot_db` |
| `POSTGRES_USER` | PostgreSQL username | `postgres` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `password` |
| `POSTGRES_DB` | PostgreSQL database name | `chatbot_db` |
| `CHUNK_SIZE` | Text chunk size for embeddings | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `TOP_K_RESULTS` | Number of similar chunks to retrieve | `5` |

## Key Features Explained

### Multi-Chatbot Architecture
- **Isolated Knowledge**: Each chatbot has its own document collection
- **Custom Personalities**: Individual system prompts define behavior
- **Independent Settings**: Per-chatbot configuration and activation status
- **Scalable Design**: Create unlimited specialized chatbots

### Document Processing
- **Smart Chunking**: Intelligent text splitting with configurable overlap
- **Vector Embeddings**: Documents converted to searchable vectors
- **Similarity Search**: Retrieves most relevant chunks for context
- **File Support**: PDF and TXT files with content extraction

### User Experience
- **Chatbot Selection**: Intuitive interface to choose between chatbots
- **Suggested Questions**: Pre-loaded questions help users get started quickly
- **Markdown Support**: Rich text formatting in responses
- **Message Feedback**: Thumbs up/down feedback on bot responses for quality tracking
- **Responsive Design**: Works on desktop and mobile devices
- **Session Management**: Persistent chat history per session

## License

MIT License - see LICENSE file for details.