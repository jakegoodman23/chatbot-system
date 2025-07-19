import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SlackBotConfig:
    """Configuration class for Slack Bot"""
    
    # Slack API Configuration
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN") 
    SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET")
    
    # Backend Configuration
    BACKEND_URL = os.getenv("CHATBOT_BACKEND_URL", "http://localhost:8000")
    DEFAULT_CHATBOT_ID = os.getenv("DEFAULT_CHATBOT_ID", "1")
    
    # Slack Bot Settings
    BOT_NAME = os.getenv("BOT_NAME", "ChatBot Assistant")
    BOT_EMOJI = os.getenv("BOT_EMOJI", ":robot_face:")
    
    # Timeout settings
    BACKEND_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "30"))  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Channel to Chatbot Mapping
    @classmethod
    def get_channel_chatbot_mapping(cls) -> Dict[str, str]:
        """
        Get channel to chatbot mapping from environment variable
        Format: CHANNEL_ID:CHATBOT_ID,CHANNEL_ID:CHATBOT_ID
        """
        mapping_str = os.getenv("CHANNEL_CHATBOT_MAPPING", "")
        mapping = {}
        
        if mapping_str:
            try:
                pairs = mapping_str.split(",")
                for pair in pairs:
                    if ":" in pair:
                        channel_id, chatbot_id = pair.strip().split(":", 1)
                        mapping[channel_id.strip()] = chatbot_id.strip()
            except Exception as e:
                print(f"Error parsing channel mapping: {e}")
        
        return mapping
    
    # Slash Commands Configuration
    SLASH_COMMANDS = {
        "ask": {
            "name": "/ask",
            "description": "Ask a question to the chatbot",
            "usage": "/ask <your question>"
        },
        "select_bot": {
            "name": "/select-bot", 
            "description": "Select which chatbot to interact with",
            "usage": "/select-bot"
        },
        "list_bots": {
            "name": "/list-bots",
            "description": "List all available chatbots", 
            "usage": "/list-bots"
        }
    }
    
    # Help messages
    HELP_MESSAGE = """
🤖 *Slack Chatbot Assistant Help*

*Ways to interact with me:*
• Mention me in a channel: `@{bot_name} your question`
• Send me a direct message
• Use slash commands

*Available Commands:*
• `/ask <question>` - Ask me anything
• `/select-bot` - Choose which chatbot to use
• `/list-bots` - See all available chatbots

*Features:*
• Multiple specialized chatbots
• Document upload and analysis
• RAG-powered responses
• Session memory

Need help? Just mention me and ask!
""".format(bot_name=BOT_NAME)
    
    WELCOME_MESSAGE = """
👋 Welcome! I'm your AI assistant powered by multiple specialized chatbots.

I can help you with various tasks depending on which chatbot you're talking to:
• Customer Support
• Technical Documentation  
• General Q&A
• Document Analysis

Use `/list-bots` to see available options or just start chatting!
"""
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """Validate required configuration and return list of errors"""
        errors = []
        
        if not cls.SLACK_BOT_TOKEN:
            errors.append("SLACK_BOT_TOKEN is required")
        
        if not cls.SLACK_APP_TOKEN:
            errors.append("SLACK_APP_TOKEN is required for Socket Mode")
            
        if not cls.SLACK_SIGNING_SECRET:
            errors.append("SLACK_SIGNING_SECRET is required")
            
        if not cls.BACKEND_URL:
            errors.append("CHATBOT_BACKEND_URL is required")
            
        # Validate token formats
        if cls.SLACK_BOT_TOKEN and not cls.SLACK_BOT_TOKEN.startswith("xoxb-"):
            errors.append("SLACK_BOT_TOKEN should start with 'xoxb-'")
            
        if cls.SLACK_APP_TOKEN and not cls.SLACK_APP_TOKEN.startswith("xapp-"):
            errors.append("SLACK_APP_TOKEN should start with 'xapp-'")
        
        return errors