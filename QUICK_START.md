# Quick Start Guide - Human Support System

Get your chatbot with human support up and running in 5 minutes!

## 🚀 Quick Setup

### 1. Database Migration
```bash
cd backend
python add_human_support_migration.py
```

### 2. Configure Email (Optional but Recommended)
Create a `.env` file in the backend directory:
```bash
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
FROM_EMAIL=noreply@yourdomain.com
FRONTEND_URL=http://localhost:3000
```

### 3. Start the Application
```bash
# Backend (Terminal 1)
cd backend
uvicorn app.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend
python -m http.server 3000
```

### 4. Create Your First Chatbot
1. Visit http://localhost:3000/admin.html
2. Click "Create New Chatbot"
3. Enter:
   - **Name**: Customer Support Bot
   - **Description**: Helps customers with common questions
   - **Admin Email**: your-email@domain.com ⚠️ **Required for human support!**
   - **System Prompt**: You are a helpful customer support assistant.

### 5. Test the Human Support Feature
1. Visit http://localhost:3000/human_support_example.html
2. Chat with the bot
3. Click "👤 Speak to Human"
4. Fill out the support request form
5. Check your email for the notification
6. Go to Admin Panel → Human Support to join the conversation

## 🎯 Key Features Demonstrated

### User Experience
- **AI Chat**: Start with intelligent AI responses
- **Seamless Handoff**: One-click transition to human support
- **Real-time Chat**: Instant messaging with support agents
- **Status Updates**: Visual indicators of support request status

### Admin Experience
- **Email Alerts**: Instant notifications when users need help
- **Dashboard**: Centralized view of all support requests
- **Real-time Communication**: WebSocket-powered messaging
- **Request Management**: Join, resolve, and close requests

## 📧 Email Configuration Options

### Gmail Setup
```bash
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password, not regular password
SMTP_USE_TLS=true
```

### Other Email Providers
```bash
# Outlook/Hotmail
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587

# Yahoo
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587

# Custom SMTP
SMTP_SERVER=mail.yourdomain.com
SMTP_PORT=587
```

## 🔧 Widget Integration

Add to any website:
```html
<script src="https://your-domain.com/widget/chatbot-widget.js"></script>
<lt-chatbot 
    data-id="1" 
    data-mode="floating"
    data-api-base="https://your-api-domain.com"
    data-title="Customer Support"
></lt-chatbot>
```

### Widget Modes
- `inline` - Embedded in page content
- `floating` - Floating chat bubble (recommended)
- `modal` - Opens in a modal dialog
- `sidebar` - Side panel overlay

## 🎮 Testing the System

### Test Workflow
1. **User Journey**:
   - Visit the demo page
   - Chat with the AI
   - Request human support
   - Continue conversation

2. **Admin Journey**:
   - Receive email notification
   - Access admin panel
   - Join conversation
   - Resolve the request

3. **Features to Test**:
   - Email notifications
   - Real-time messaging
   - Status transitions
   - Multiple concurrent requests

## 📊 Admin Panel Features

### Human Support Dashboard
- **Pending**: New requests waiting for response
- **Active**: Ongoing conversations
- **All**: Complete request history

### Conversation Management
- View user details and initial message
- Real-time chat interface
- Resolve or close requests
- Message history and timestamps

## 🔍 Troubleshooting

### Common Issues

**Email not sending?**
- Check SMTP credentials
- Enable "Less secure app access" or use App Password
- Verify firewall settings

**WebSocket connection failed?**
- Check if backend is running on correct port
- Verify browser security settings
- Check CORS configuration

**Database errors?**
- Ensure PostgreSQL is running
- Check database connection string
- Run migration script again

**Widget not loading?**
- Verify script path is correct
- Check browser console for errors
- Ensure API base URL is correct

## 🎨 Customization

### Styling
Modify CSS in:
- `frontend/widget/chatbot-widget.js` - Widget appearance
- `frontend/admin.html` - Admin interface
- `backend/app/services/email_service.py` - Email templates

### Functionality
- Add file upload support
- Implement user authentication
- Create custom email templates
- Add support for multiple languages

## 📈 Next Steps

1. **Production Setup**:
   - Use a production SMTP service (SendGrid, Mailgun)
   - Add authentication to admin routes
   - Set up proper database backups
   - Configure monitoring and logging

2. **Advanced Features**:
   - Support ticket prioritization
   - SLA tracking and reporting
   - Integration with external help desk systems
   - Analytics and performance metrics

3. **Security**:
   - Implement rate limiting
   - Add CAPTCHA for public forms
   - Encrypt sensitive data
   - Regular security audits

## 💡 Tips for Success

- **Set Clear Expectations**: Let users know response times
- **Train Support Staff**: Ensure they understand the interface
- **Monitor Performance**: Track response times and resolution rates
- **Gather Feedback**: Continuously improve based on user feedback
- **Scale Gradually**: Start with one chatbot, expand as needed

## 🆘 Getting Help

- Check the detailed documentation in `HUMAN_SUPPORT_README.md`
- Review the example implementation in `human_support_example.html`
- Look at the admin interface for debugging tools
- Monitor server logs for error messages

Happy chatting! 🎉