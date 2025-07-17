# Local Chatbot with RAG

A locally-hosted chatbot system with document ingestion capabilities, built with FastAPI, PostgreSQL with pgvector, and vanilla JavaScript.

## Features

- 🤖 **RAG-powered chatbot** using OpenAI embeddings and completions
- 📄 **Document ingestion** for PDF and TXT files
- 🔍 **Vector similarity search** with PostgreSQL + pgvector
- 💬 **Real-time chat interface** with vanilla JavaScript
- ⚙️ **Admin panel** with system prompt control and document management
- 🔐 **Secure admin authentication** with session management
- 🐳 **Docker containerization** for easy deployment
- 📊 **Chat history tracking** and session management

## Architecture

- **Backend**: FastAPI with Python
- **Database**: PostgreSQL with pgvector extension
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Embeddings**: OpenAI text-embedding-ada-002
- **Chat**: OpenAI GPT-3.5-turbo

## Quick Start

### Prerequisites

- Docker and Docker Compose
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

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Admin Panel: http://localhost:3000/admin.html
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Usage

1. **Upload Documents**: 
   - Go to the "Upload Documents" tab
   - Upload PDF or TXT files
   - Documents will be processed and embedded automatically

2. **Chat**:
   - Return to the "Chat" tab
   - Ask questions about your uploaded documents
   - The bot will provide answers based on the document content

3. **Admin Panel**:
   - Access the "Admin" tab
   - Login with admin password (default: `admin123`)
   - Customize system prompt
   - Manage documents and view analytics
   - Monitor system statistics

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
   uvicorn app.main:app --reload --port 8000
   ```

3. **Serve frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
   # Or use any static file server
   ```

### API Endpoints

**Chat & Documents:**
- `POST /chat/` - Send a message to the chatbot
- `POST /documents/upload` - Upload a document
- `GET /documents/` - List all documents
- `POST /documents/search` - Search document chunks
- `GET /chat/sessions/{session_id}/history` - Get chat history

**Admin Endpoints:**
- `POST /admin/login` - Admin login
- `GET /admin/system-prompt` - Get system prompt
- `POST /admin/system-prompt` - Update system prompt
- `GET /admin/dashboard` - Get dashboard statistics
- `GET /admin/documents/analytics` - Get document analytics
- `DELETE /admin/documents/{id}` - Admin delete document

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/chatbot_db` |
| `CHUNK_SIZE` | Text chunk size for embeddings | `1000` |
| `CHUNK_OVERLAP` | Overlap between chunks | `200` |
| `TOP_K_RESULTS` | Number of similar chunks to retrieve | `5` |
| `ADMIN_PASSWORD` | Admin panel password | `admin123` |
| `ADMIN_SESSION_DURATION` | Admin session duration (hours) | `24` |

## Deployment

The project includes Docker configuration for easy deployment:

1. **Production deployment**:
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

2. **Environment configuration**:
   - Update `.env` with production values
   - Consider using environment-specific compose files
   - Set up proper CORS origins for production

3. **Scaling considerations**:
   - Use a managed PostgreSQL service for production
   - Consider using Redis for session management
   - Implement proper logging and monitoring

## Troubleshooting

### Common Issues

1. **"Server unavailable" error**:
   - Check if backend is running on port 8000
   - Verify database connection
   - Check OpenAI API key is set

2. **Upload fails**:
   - Ensure file is PDF or TXT format
   - Check file size limits
   - Verify backend has write permissions

3. **No relevant answers**:
   - Upload more relevant documents
   - Check document content was extracted properly
   - Adjust similarity threshold in chat service

### Logs

View container logs:
```bash
docker-compose logs backend
docker-compose logs postgres
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.