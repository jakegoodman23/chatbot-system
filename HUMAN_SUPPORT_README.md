# Human Support System

This document describes the comprehensive human support system that allows chatbot users to request human assistance and enables real-time communication between users and support agents.

## Overview

The human support system consists of:

1. **User Interface**: A "Speak to Human" button in the chatbot widget
2. **Email Notifications**: Automatic email alerts to chatbot administrators
3. **Admin Interface**: A dedicated admin section for managing support requests
4. **Real-time Communication**: WebSocket-based real-time messaging
5. **Request Management**: Full lifecycle management of support requests

## Features

### For Users
- **Easy Access**: One-click "Speak to Human" button in the chatbot
- **Information Collection**: Optional name and email collection
- **Real-time Chat**: Seamless transition from AI to human support
- **Status Updates**: Visual indicators of support request status
- **Email Confirmations**: Optional email confirmations when support is requested

### For Administrators
- **Email Notifications**: Instant email alerts when users request support
- **Centralized Dashboard**: View all support requests in one place
- **Real-time Messaging**: Chat with users in real-time
- **Request Management**: Join, resolve, and close support requests
- **Multi-chatbot Support**: Manage support across multiple chatbots

## System Architecture

### Database Schema

#### Chatbots Table (Updated)
```sql
ALTER TABLE chatbots ADD COLUMN admin_email VARCHAR(255) NOT NULL;
```

#### Human Support Requests
```sql
CREATE TABLE human_support_requests (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    chatbot_id INTEGER NOT NULL REFERENCES chatbots(id),
    session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(session_id),
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    initial_message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    admin_joined_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Human Support Messages
```sql
CREATE TABLE human_support_messages (
    id SERIAL PRIMARY KEY,
    support_request_id INTEGER NOT NULL REFERENCES human_support_requests(id),
    sender_type VARCHAR(50) NOT NULL, -- 'user' or 'admin'
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### API Endpoints

#### Human Support API (`/human-support`)

- `POST /request` - Create a new support request
- `GET /requests/pending` - Get pending support requests (admin only)
- `GET /requests/active` - Get active support requests (admin only)
- `GET /requests/{request_id}` - Get support request details
- `POST /requests/{request_id}/join` - Admin joins a support request
- `POST /requests/{request_id}/messages` - Add a message to a support request
- `GET /requests/{request_id}/messages` - Get all messages for a support request
- `POST /requests/{request_id}/resolve` - Mark support request as resolved
- `POST /requests/{request_id}/close` - Close a support request
- `WebSocket /ws/{request_id}` - Real-time communication channel

#### Updated Chatbot API
- Chatbot creation now requires `admin_email` field
- Chatbot updates can modify `admin_email` field

## Installation and Setup

### 1. Run Database Migration

```bash
cd backend
python add_human_support_migration.py
```

To rollback (development only):
```bash
python add_human_support_migration.py rollback
```

### 2. Install Email Dependencies

The system uses Python's built-in `smtplib` for email functionality. No additional dependencies are required.

### 3. Configure Email Settings

Set the following environment variables for email functionality:

```bash
# SMTP Configuration
export SMTP_SERVER="smtp.gmail.com"  # or your SMTP server
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
export SMTP_USE_TLS="true"
export FROM_EMAIL="noreply@yourdomain.com"

# Frontend URL for email links
export FRONTEND_URL="http://localhost:3000"
```

### 4. Update Existing Chatbots

If you have existing chatbots, update them with admin email addresses:

```sql
UPDATE chatbots SET admin_email = 'admin@yourdomain.com' WHERE id = 1;
```

Or use the admin interface to edit existing chatbots.

## Usage Guide

### For Chatbot Creators

1. **Create Chatbot**: When creating a new chatbot, provide an admin email address
2. **Monitor Support**: Check your email for support request notifications
3. **Access Admin Panel**: Navigate to the admin panel and click "Human Support"
4. **Manage Requests**: View pending/active requests and join conversations

### For End Users

1. **Request Support**: Click the "👤 Speak to Human" button in the chatbot
2. **Provide Details**: Fill in optional name, email, and describe your issue
3. **Continue Chatting**: Keep the chat window open to communicate with support
4. **Status Updates**: See visual indicators when an agent joins or resolves your request

### Admin Interface Navigation

#### Human Support Dashboard
- **Pending Requests**: New support requests waiting for agent response
- **Active Conversations**: Ongoing conversations between users and agents
- **All Requests**: Complete history of all support requests

#### Support Conversation Window
- **Request Details**: User information, timestamps, and initial message
- **Message History**: Full conversation thread between user and agent
- **Actions**: Send messages, resolve, or close the support request

## Configuration Options

### Email Templates

The system sends two types of emails:

1. **Admin Notification**: Sent to the chatbot admin when a user requests support
2. **User Confirmation**: Sent to the user confirming their support request (if email provided)

Email templates are HTML-formatted and include:
- Request details and user information
- Direct links to join the conversation
- Professional styling and branding

### WebSocket Configuration

Real-time communication is handled via WebSocket connections:
- **User Side**: Automatic connection when human support is requested
- **Admin Side**: Connection established when opening a support conversation
- **Message Broadcasting**: Messages are broadcast to all connected clients
- **Connection Management**: Automatic reconnection and error handling

### Status Management

Support requests have four possible statuses:
- **Pending**: Waiting for admin to join
- **Active**: Admin has joined and conversation is ongoing
- **Resolved**: Issue has been resolved by admin
- **Closed**: Conversation has been closed

## Security Considerations

### Authentication
- Admin functions require authentication (implement your auth system)
- WebSocket connections should validate permissions
- Email addresses should be validated and sanitized

### Data Privacy
- User emails are optional and stored securely
- Message content should be encrypted for sensitive applications
- Consider implementing message retention policies

### Rate Limiting
- Implement rate limiting for support request creation
- Monitor for abuse or spam requests
- Consider CAPTCHA for public-facing chatbots

## Troubleshooting

### Common Issues

1. **Email Not Sending**
   - Check SMTP configuration in environment variables
   - Verify SMTP server credentials and ports
   - Check firewall settings for outbound SMTP

2. **WebSocket Connection Fails**
   - Ensure WebSocket URL is correctly configured
   - Check browser security settings
   - Verify server WebSocket support

3. **Database Migration Errors**
   - Check database connection and permissions
   - Ensure PostgreSQL is running
   - Verify table dependencies exist

### Logs and Monitoring

Monitor the following for system health:
- Email delivery success/failure rates
- WebSocket connection counts
- Support request resolution times
- Database query performance

## Customization

### Styling
The human support interface can be customized by modifying:
- CSS classes in `frontend/admin.html`
- Widget styles in `frontend/widget/chatbot-widget.js`
- Email template HTML in `backend/app/services/email_service.py`

### Functionality Extensions
Consider implementing:
- File upload support in support messages
- Support ticket prioritization
- SLA tracking and reporting
- Integration with external help desk systems
- Multi-language support

## Performance Considerations

### Database Optimization
- Indexes are created on frequently queried columns
- Consider partitioning for high-volume installations
- Regular cleanup of old resolved/closed requests

### WebSocket Scaling
- For high concurrency, consider using Redis for WebSocket management
- Implement connection pooling for better resource utilization
- Monitor memory usage for long-lived connections

### Email Delivery
- Use a professional email service (SendGrid, Mailgun) for production
- Implement email queuing for high-volume scenarios
- Monitor email delivery rates and bounce handling

## Support and Maintenance

### Regular Tasks
- Monitor support request volumes and response times
- Clean up old resolved/closed requests periodically
- Update email templates and admin contact information
- Review and update security configurations

### Monitoring Metrics
- Average response time to support requests
- Support request resolution rate
- Email delivery success rate
- WebSocket connection stability
- Admin user activity and engagement

This human support system provides a comprehensive solution for seamless user-to-human handoff in your chatbot application, ensuring users can always get the help they need when AI responses aren't sufficient.