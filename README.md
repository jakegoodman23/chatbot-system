# Local Multi-Chatbot Platform with RAG

A locally-hosted multi-chatbot platform with document ingestion capabilities, built with FastAPI, PostgreSQL with pgvector, and vanilla JavaScript. Create multiple specialized chatbots, each with their own document knowledge base and system prompts.

## Features

- 🤖 **Multiple specialized chatbots** - Create unlimited chatbots with individual personalities and knowledge bases
- 📄 **Per-chatbot document management** - Each chatbot has its own isolated document collection
- 🔍 **RAG-powered responses** using OpenAI embeddings and completions with vector similarity search
- 💬 **Modern chat interface** with markdown support, typing indicators, and session management
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
- `DELETE /chatbots/{id}/documents/{doc_id}` - Remove document from chatbot

**Chat & Sessions:**
- `POST /chat/` - Send message to chatbot
- `POST /chat/sessions` - Create new chat session
- `GET /chat/sessions/{session_id}/history` - Get chat history

**Document Management:**
- `POST /documents/upload` - Upload document to specific chatbot
- `GET /documents/?chatbot_id={id}` - List documents for chatbot
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document
- `POST /documents/search` - Search document chunks

**Admin & Analytics:**
- `GET /chatbots/stats/all` - Get statistics for all chatbots
- `GET /chatbots/{id}/stats` - Get specific chatbot statistics

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

## Project Structure

```
chatbot-local/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── routers/           # API route handlers
│   │   │   ├── admin.py       # Admin authentication
│   │   │   ├── chat.py        # Chat and sessions
│   │   │   ├── chatbots.py    # Chatbot management
│   │   │   └── documents.py   # Document handling
│   │   ├── services/          # Business logic
│   │   │   ├── chat_service.py
│   │   │   ├── chatbot_service.py
│   │   │   ├── document_processor.py
│   │   │   └── embeddings.py
│   │   ├── database.py        # Database connection
│   │   ├── models.py          # SQLAlchemy models
│   │   └── main.py           # FastAPI app
│   ├── migrations/           # Database migrations
│   └── requirements.txt
├── frontend/                 # Static frontend files
│   ├── index.html           # Main chat interface
│   ├── select.html          # Chatbot selection page
│   ├── admin.html           # Admin panel
│   ├── script.js            # Chat functionality
│   ├── select.js            # Selection page logic
│   └── style.css            # Styling
├── docker-compose.yml       # Container orchestration
└── README.md
```

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
- **Markdown Support**: Rich text formatting in responses
- **Responsive Design**: Works on desktop and mobile devices
- **Session Management**: Persistent chat history per session

## Deployment

### Production Deployment

1. **Set up environment**:
   ```bash
   # Copy and configure environment variables
   cp .env.example .env
   # Set OPENAI_API_KEY and other production values
   ```

2. **Deploy with Docker**:
   ```bash
   docker-compose up -d --build
   ```

3. **Run migrations**:
   ```bash
   docker-compose exec backend python run_migrations.py
   ```

### Scaling Considerations
- Use a managed PostgreSQL service for production
- Consider Redis for session management at scale
- Implement proper logging and monitoring
- Set up reverse proxy (nginx) for SSL termination
- Consider OpenAI API rate limiting for high traffic

## Troubleshooting

### Common Issues

1. **500 error on sessions endpoint**:
   - Run database migrations: `docker-compose exec backend python run_migrations.py`
   - Check that `chatbot_id` column exists in `chat_sessions` table

2. **"No chatbots available" message**:
   - Create a chatbot in the admin panel first
   - Ensure chatbot is activated (not deactivated)

3. **Upload fails**:
   - Verify file is PDF or TXT format
   - Check that chatbot exists and is active
   - Ensure backend has write permissions to uploads directory

4. **No relevant answers**:
   - Upload documents relevant to the chatbot's purpose
   - Check document content was extracted properly
   - Verify documents are associated with the correct chatbot

5. **OpenAI API errors**:
   - Verify `OPENAI_API_KEY` is set correctly
   - Check API key has sufficient credits
   - Monitor API rate limits

### Logs and Debugging

View container logs:
```bash
# Backend logs
docker-compose logs backend

# Database logs  
docker-compose logs postgres

# All services
docker-compose logs
```

Check database migrations:
```bash
docker-compose exec backend python run_migrations.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with multiple chatbots
5. Update documentation if needed
6. Submit a pull request

## License

MIT License - see LICENSE file for details.