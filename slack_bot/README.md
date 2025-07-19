# Slack Chatbot Integration

A dedicated Slack bot service that integrates with your existing multi-chatbot FastAPI backend. This service provides a seamless way for users to interact with your RAG-powered chatbots directly within Slack.

## Features

- 🤖 **Multiple Chatbot Support** - Route different channels to different specialized chatbots
- 💬 **Multiple Interaction Methods** - App mentions, direct messages, and slash commands
- 📄 **Document Upload** - Upload and process PDF, TXT, DOC files directly in Slack
- ⚡ **Real-time Responses** - Socket Mode for instant communication
- 🔄 **Session Management** - Maintain conversation context per user/channel
- 🎯 **Interactive UI** - Buttons and menus for bot selection and actions
- 🛡️ **Enterprise Ready** - Works behind firewalls with Socket Mode

## Architecture

```
Slack User → Slack Bot (Bolt) → Your FastAPI Backend → RAG Pipeline → Response → Slack
```

## Setup Instructions

### 1. Prerequisites

- Python 3.8+
- Your existing FastAPI chatbot backend running
- Slack workspace with admin permissions

### 2. Create Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From an app manifest"
3. Select your workspace
4. Use this manifest (replace `YOUR-COMMAND-NAME` with actual command names):

```yaml
display_information:
  name: "Multi-Chatbot Assistant"
  description: "AI-powered assistant with multiple specialized chatbots"
features:
  bot_user:
    display_name: "ChatBot Assistant"
    always_online: true
  slash_commands:
    - command: "/ask"
      description: "Ask a question to the chatbot"
      should_escape: false
    - command: "/select-bot"
      description: "Select which chatbot to interact with"
      should_escape: false
    - command: "/list-bots"
      description: "List all available chatbots"
      should_escape: false
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - channels:history
      - channels:read
      - chat:write
      - commands
      - files:read
      - groups:history
      - groups:read
      - im:history
      - im:read
      - im:write
      - mpim:history
      - mpim:read
      - reactions:read
      - reactions:write
      - users:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - file_shared
      - message.channels
      - message.groups
      - message.im
      - message.mpim
  interactivity:
    is_enabled: true
  org_deploy_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```

### 3. Get Tokens

After creating the app:

1. **Bot Token**: Go to "OAuth & Permissions" → Copy the "Bot User OAuth Token" (starts with `xoxb-`)
2. **App Token**: Go to "Basic Information" → "App-Level Tokens" → "Generate Token and Scopes" → Add `connections:write` scope → Copy token (starts with `xapp-`)
3. **Signing Secret**: Go to "Basic Information" → "App Credentials" → Copy "Signing Secret"

### 4. Install Dependencies

```bash
cd slack_bot
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# Slack Bot Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-level-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Backend Configuration
CHATBOT_BACKEND_URL=http://localhost:8000
DEFAULT_CHATBOT_ID=1

# Optional: Channel to Chatbot Mapping
# CHANNEL_CHATBOT_MAPPING=C1234567890:1,C0987654321:2
```

### 6. Install App to Workspace

1. Go to "OAuth & Permissions" → "Install to Workspace" → "Allow"
2. The bot will now appear in your workspace

### 7. Run the Bot

```bash
python slack_bot.py
```

You should see:
```
🚀 Starting Slack Chatbot Service...
⚡️ Bolt app is running!
```

## Usage

### Ways to Interact

1. **App Mentions**: `@ChatBot Assistant what is your return policy?`
2. **Direct Messages**: Send a DM to the bot
3. **Slash Commands**: `/ask what are your hours?`

### Available Commands

- `/ask <question>` - Ask any question to the current chatbot
- `/select-bot` - Interactive menu to choose which chatbot to use
- `/list-bots` - List all available chatbots with descriptions

### Document Upload

1. Upload a PDF, TXT, or DOC file to any channel where the bot is present
2. Mention the bot: `@ChatBot Assistant please analyze this document`
3. The bot will process the file and confirm when ready
4. Ask questions about the document content

### Channel-Specific Chatbots

You can configure different channels to use different chatbots by:

1. **Environment Variable**: Set `CHANNEL_CHATBOT_MAPPING` in `.env`
2. **Runtime Configuration**: Use `/select-bot` command in each channel

## Configuration

### Channel Mapping

Map Slack channels to specific chatbots:

```bash
# In .env file
CHANNEL_CHATBOT_MAPPING=C1234567890:1,C0987654321:2
```

Or programmatically in `slack_bot.py`:

```python
self.channel_chatbot_mapping = {
    "C1234567890": "1",  # #support channel → Customer Support Bot
    "C0987654321": "2",  # #tech channel → Technical Docs Bot
}
```

### Backend Integration

The bot expects your FastAPI backend to have these endpoints:

- `POST /chat/` - Send messages to chatbots
- `GET /chatbots/` - List available chatbots
- `GET /chatbots/{id}` - Get chatbot details
- `POST /documents/upload` - Upload documents

### Customization

#### Add New Slash Commands

1. Add command to Slack app manifest
2. Update `_setup_handlers()` in `slack_bot.py`:

```python
@self.app.command("/new-command")
async def handle_new_command(ack, command, say, client):
    await ack()
    # Your command logic here
```

#### Modify Bot Responses

Edit messages in `config.py`:

```python
WELCOME_MESSAGE = """
🎉 Custom welcome message here!
"""
```

#### Add Interactive Elements

```python
blocks = [
    {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "Choose an option:"}
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Option 1"},
                "action_id": "option_1"
            }
        ]
    }
]
```

## Troubleshooting

### Common Issues

1. **"Token verification failed"**
   - Check that all three tokens are correct
   - Ensure bot token starts with `xoxb-`
   - Ensure app token starts with `xapp-`

2. **"Bot doesn't respond to mentions"**
   - Verify bot is invited to the channel
   - Check that `app_mentions:read` scope is added
   - Ensure Socket Mode is enabled

3. **"File upload fails"**
   - Check file size (max 10MB)
   - Verify supported file types (PDF, TXT, DOC, DOCX)
   - Ensure backend `/documents/upload` endpoint is working

4. **"Backend connection failed"**
   - Verify `CHATBOT_BACKEND_URL` is correct
   - Ensure FastAPI backend is running
   - Check firewall/network connectivity

### Debug Mode

Enable verbose logging:

```bash
LOG_LEVEL=DEBUG python slack_bot.py
```

### Test Backend Connectivity

```bash
curl -X GET http://localhost:8000/chatbots/
```

## Production Deployment

### Using Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "slack_bot.py"]
```

### Environment Variables for Production

```bash
# Use secure token storage (e.g., AWS Secrets Manager, Azure Key Vault)
SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}
SLACK_APP_TOKEN=${SLACK_APP_TOKEN}
SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}

# Point to production backend
CHATBOT_BACKEND_URL=https://your-api.example.com

# Production logging
LOG_LEVEL=INFO
```

### Health Checks

The bot automatically validates configuration on startup. Check logs for any validation errors.

## Integration with Existing Backend

This Slack bot is designed to work with your existing FastAPI backend without modifications. It expects standard REST endpoints that your current web interface already uses.

### Expected API Format

**Chat Endpoint** (`POST /chat/`):
```json
{
  "message": "user question",
  "chatbot_id": 1,
  "session_id": "slack_user123_channel456",
  "user_id": "user123",
  "source": "slack"
}
```

**Response Format**:
```json
{
  "message": "bot response",
  "session_id": "slack_user123_channel456"
}
```

## Support

For issues:
1. Check logs for error messages
2. Verify all configuration values
3. Test backend connectivity independently
4. Review Slack app permissions and scopes

The bot includes comprehensive error handling and logging to help diagnose issues quickly.