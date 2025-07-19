#!/bin/bash

# ChatBot System Runner
# This script helps run the chatbot system and manage database migrations

set -e

echo "🚀 ChatBot System Manager"
echo "========================"

# Function to run migrations
run_migrations() {
    echo "📝 Running database migrations..."
    
    if command -v docker-compose &> /dev/null; then
        echo "Using docker-compose..."
        docker-compose exec backend python run_migrations.py
    elif command -v docker &> /dev/null && docker compose ps &> /dev/null; then
        echo "Using docker compose..."
        docker compose exec backend python run_migrations.py
    else
        echo "⚠️  Docker not available. To run migrations manually:"
        echo "1. Ensure PostgreSQL is running with the correct database"
        echo "2. Set DATABASE_URL environment variable"
        echo "3. Run: python backend/run_migrations.py"
        echo ""
        echo "Required migrations:"
        echo "- 001_add_chatbots.sql"
        echo "- 002_migrate_to_chatbots.sql" 
        echo "- 003_add_message_feedback.sql (NEW - for thumbs up/down feature)"
        echo "- 004_add_suggested_questions.sql (NEW - for suggested questions feature)"
        echo ""
        echo "New features added:"
        echo "✅ Thumbs up/down feedback on chat messages"
        echo "✅ Feedback statistics API endpoints"
        echo "✅ Frontend UI for message feedback"
        echo "✅ Widget support for feedback buttons"
        echo "✅ Pre-loaded suggested questions for users"
        echo "✅ Admin interface for managing suggested questions"
    fi
}

# Function to start services
start_services() {
    echo "🏃 Starting services..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d
    elif command -v docker &> /dev/null; then
        docker compose up -d
    else
        echo "⚠️  Docker not available. To run manually:"
        echo "1. Start PostgreSQL server"
        echo "2. Set environment variables (see .env.example)"
        echo "3. Install Python dependencies: pip install -r backend/requirements.txt"
        echo "4. Run backend: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        echo "5. Serve frontend files on a web server"
    fi
}

# Main menu
case "${1:-}" in
    "migrate" | "migrations")
        run_migrations
        ;;
    "start" | "up")
        start_services
        ;;
    "restart")
        echo "🔄 Restarting services..."
        if command -v docker-compose &> /dev/null; then
            docker-compose restart
        elif command -v docker &> /dev/null; then
            docker compose restart
        fi
        ;;
    "logs")
        echo "📋 Showing logs..."
        if command -v docker-compose &> /dev/null; then
            docker-compose logs -f
        elif command -v docker &> /dev/null; then
            docker compose logs -f
        fi
        ;;
    *)
        echo "Usage: $0 {migrate|start|restart|logs}"
        echo ""
        echo "Commands:"
        echo "  migrate   - Run database migrations"
        echo "  start     - Start all services"
        echo "  restart   - Restart all services" 
        echo "  logs      - Show service logs"
        echo ""
        echo "🆕 New Feedback Feature:"
        echo "This update adds thumbs up/down feedback capability to chat messages."
        echo "Users can now rate bot responses, and admins can view feedback statistics."
        echo ""
        echo "🆕 New Suggested Questions Feature:"
        echo "Admins can now pre-load suggested questions that appear as quick-start"
        echo "buttons for users. This helps users get started and shows what the"
        echo "chatbot can help with."
        echo ""
        echo "To apply the new features, run: $0 migrate"
        ;;
esac