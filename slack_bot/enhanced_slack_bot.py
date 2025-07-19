import os
import asyncio
import logging
from typing import Dict, Optional, List
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import aiohttp
import json
from datetime import datetime

from config import SlackBotConfig
from document_handler import SlackDocumentHandler

# Configure logging
logging.basicConfig(
    level=getattr(logging, SlackBotConfig.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedSlackChatbotService:
    def __init__(self):
        # Validate configuration first
        config_errors = SlackBotConfig.validate_config()
        if config_errors:
            logger.error("Configuration errors:")
            for error in config_errors:
                logger.error(f"  - {error}")
            raise ValueError("Invalid configuration. Please check environment variables.")
        
        self.config = SlackBotConfig
        
        self.app = AsyncApp(
            token=self.config.SLACK_BOT_TOKEN,
            signing_secret=self.config.SLACK_SIGNING_SECRET
        )
        
        # Initialize document handler
        self.document_handler = SlackDocumentHandler(
            backend_url=self.config.BACKEND_URL,
            slack_token=self.config.SLACK_BOT_TOKEN
        )
        
        # Channel to chatbot mapping (can be updated dynamically)
        self.channel_chatbot_mapping = self.config.get_channel_chatbot_mapping()
        
        # User preferences (in production, you'd want to persist this in a database)
        self.user_preferences = {}
        
        # Setup event handlers
        self._setup_handlers()
        
        logger.info("✅ Slack Chatbot Service initialized successfully")
        
    def _setup_handlers(self):
        """Setup all Slack event handlers"""
        
        # Handle app mentions (@bot_name)
        @self.app.event("app_mention")
        async def handle_app_mention(event, say, client):
            await self._handle_user_message(event, say, client, is_mention=True)
        
        # Handle direct messages
        @self.app.event("message")
        async def handle_direct_message(event, say, client):
            # Only handle DMs and file uploads
            if event.get("channel_type") == "im" or "files" in event:
                await self._handle_user_message(event, say, client, is_mention=False)
        
        # Handle file uploads
        @self.app.event("file_shared")
        async def handle_file_shared(event, say, client):
            # Get the full message event that includes the file
            try:
                result = await client.conversations_history(
                    channel=event["channel_id"],
                    latest=event["event_ts"],
                    limit=1,
                    inclusive=True
                )
                
                if result["messages"]:
                    file_message = result["messages"][0]
                    if "files" in file_message:
                        await self.document_handler.handle_file_upload(file_message, client, say)
                        
            except Exception as e:
                logger.error(f"Error handling file shared event: {e}")
        
        # Slash Commands
        @self.app.command("/ask")
        async def handle_ask_command(ack, command, say, client):
            await ack()
            await self._handle_slash_command(command, say, client, "ask")
            
        @self.app.command("/select-bot")
        async def handle_bot_selection(ack, command, say, client):
            await ack()
            await self._show_bot_selection_menu(command, client)
            
        @self.app.command("/list-bots")
        async def handle_list_bots(ack, command, say, client):
            await ack()
            await self._list_available_bots(command, say)
            
        @self.app.command("/help")
        async def handle_help_command(ack, command, say, client):
            await ack()
            await say(self.config.HELP_MESSAGE)
            
        @self.app.command("/docs")
        async def handle_docs_command(ack, command, say, client):
            await ack()
            await self._show_document_management(command, client)
        
        # Handle button interactions
        @self.app.action("select_chatbot")
        async def handle_chatbot_selection(ack, body, client):
            await ack()
            await self._handle_chatbot_selection(body, client)
            
        @self.app.action("upload_document")
        async def handle_document_upload(ack, body, client):
            await ack()
            await self._handle_document_upload_request(body, client)
            
        @self.app.action("list_documents")
        async def handle_list_documents(ack, body, client):
            await ack()
            await self._handle_list_documents(body, client)
            
        @self.app.action("delete_document")
        async def handle_delete_document(ack, body, client):
            await ack()
            await self._handle_delete_document(body, client)
        
        # Handle app home opened (when user clicks on bot in sidebar)
        @self.app.event("app_home_opened")
        async def handle_app_home_opened(event, client):
            await self._update_app_home(event, client)
    
    async def _handle_user_message(self, event, say, client, is_mention: bool):
        """Handle user messages (mentions or DMs)"""
        try:
            # Skip bot messages to avoid loops
            if event.get("bot_id"):
                return
                
            user_id = event["user"]
            channel_id = event["channel"]
            text = event.get("text", "")
            
            # Handle file uploads first
            if "files" in event:
                await self.document_handler.handle_file_upload(event, client, say)
                return
            
            # Skip empty messages
            if not text.strip():
                return
            
            # Remove bot mention from text if it's a mention
            if is_mention:
                bot_user_id = await self._get_bot_user_id(client)
                text = self._clean_mention_text(text, bot_user_id)
            
            # Handle help requests
            if any(word in text.lower() for word in ["help", "commands", "what can you do"]):
                await say(self.config.HELP_MESSAGE)
                return
            
            # Show typing indicator
            typing_task = asyncio.create_task(
                self._show_typing_indicator(client, channel_id, event["ts"])
            )
            
            try:
                # Determine which chatbot to use
                chatbot_id = self._determine_chatbot(channel_id, user_id)
                
                # Create session ID
                session_id = f"slack_{user_id}_{channel_id}"
                
                # Get response from backend
                response = await self._get_chatbot_response(
                    message=text,
                    chatbot_id=chatbot_id,
                    session_id=session_id,
                    user_id=user_id
                )
                
                if response:
                    await say(response["message"])
                else:
                    await say("Sorry, I'm having trouble processing your request right now. Please try again later.")
                    
            finally:
                # Remove typing indicator
                typing_task.cancel()
                try:
                    await self._remove_typing_indicator(client, channel_id, event["ts"])
                except:
                    pass  # Ignore errors when removing indicator
                
        except Exception as e:
            logger.error(f"Error handling user message: {e}")
            await say("Sorry, something went wrong. Please try again.")
    
    async def _handle_slash_command(self, command, say, client, command_type: str):
        """Handle slash commands"""
        try:
            user_id = command["user_id"]
            channel_id = command["channel_id"]
            text = command["text"]
            
            if command_type == "ask":
                if not text.strip():
                    usage = self.config.SLASH_COMMANDS["ask"]["usage"]
                    await say(f"Please provide a question after the command. Example: `{usage}`")
                    return
                
                # Determine chatbot
                chatbot_id = self._determine_chatbot(channel_id, user_id)
                session_id = f"slack_{user_id}_{channel_id}"
                
                # Get response
                response = await self._get_chatbot_response(
                    message=text,
                    chatbot_id=chatbot_id,
                    session_id=session_id,
                    user_id=user_id
                )
                
                if response:
                    await say(response["message"])
                else:
                    await say("Sorry, I couldn't process your request.")
                    
        except Exception as e:
            logger.error(f"Error handling slash command: {e}")
            await say("Sorry, something went wrong.")
    
    async def _show_bot_selection_menu(self, command, client):
        """Show interactive menu for bot selection"""
        try:
            chatbots = await self._get_available_chatbots()
            
            if not chatbots:
                await client.chat_postMessage(
                    channel=command["channel_id"],
                    text="No chatbots are currently available."
                )
                return
            
            # Create buttons for each chatbot (max 5 per row)
            elements = []
            for chatbot in chatbots[:5]:
                elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": chatbot["name"][:75]
                    },
                    "action_id": "select_chatbot",
                    "value": str(chatbot["id"])
                })
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "🤖 *Select a chatbot to interact with:*"
                    }
                },
                {
                    "type": "actions",
                    "elements": elements
                }
            ]
            
            # Add more chatbots if there are more than 5
            if len(chatbots) > 5:
                additional_elements = []
                for chatbot in chatbots[5:10]:
                    additional_elements.append({
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": chatbot["name"][:75]
                        },
                        "action_id": "select_chatbot",
                        "value": str(chatbot["id"])
                    })
                
                if additional_elements:
                    blocks.append({
                        "type": "actions",
                        "elements": additional_elements
                    })
            
            await client.chat_postMessage(
                channel=command["channel_id"],
                blocks=blocks,
                text="Select a chatbot"
            )
            
        except Exception as e:
            logger.error(f"Error showing bot selection menu: {e}")
            await client.chat_postMessage(
                channel=command["channel_id"],
                text="Sorry, I couldn't load the chatbot selection menu."
            )
    
    async def _list_available_bots(self, command, say):
        """List all available chatbots"""
        try:
            chatbots = await self._get_available_chatbots()
            
            if not chatbots:
                await say("No chatbots are currently available.")
                return
                
            bot_list = "🤖 *Available Chatbots:*\n\n"
            for i, chatbot in enumerate(chatbots, 1):
                status = "🟢 Active" if chatbot.get("is_active", True) else "🔴 Inactive"
                description = chatbot.get("description", "No description available")
                bot_list += f"{i}. *{chatbot['name']}* - {status}\n   _{description}_\n\n"
            
            bot_list += "\nUse `/select-bot` to switch between chatbots or mention me with your question!"
            
            await say(bot_list)
            
        except Exception as e:
            logger.error(f"Error listing bots: {e}")
            await say("Sorry, I couldn't retrieve the list of chatbots.")
    
    async def _show_document_management(self, command, client):
        """Show document management interface"""
        try:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "📄 *Document Management*\n\nManage documents for your chatbots:"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📤 Upload Document"},
                            "action_id": "upload_document",
                            "style": "primary"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "📋 List Documents"},
                            "action_id": "list_documents"
                        }
                    ]
                }
            ]
            
            await client.chat_postMessage(
                channel=command["channel_id"],
                blocks=blocks,
                text="Document Management"
            )
            
        except Exception as e:
            logger.error(f"Error showing document management: {e}")
    
    async def _handle_chatbot_selection(self, body, client):
        """Handle chatbot selection from interactive menu"""
        try:
            selected_chatbot_id = body["actions"][0]["value"]
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Store user's chatbot preference
            self.user_preferences[f"{user_id}_{channel_id}"] = selected_chatbot_id
            
            # Also update channel mapping if it's a channel (not DM)
            if not channel_id.startswith("D"):  # DMs start with 'D'
                self.channel_chatbot_mapping[channel_id] = selected_chatbot_id
            
            # Get chatbot details
            chatbot = await self._get_chatbot_details(selected_chatbot_id)
            
            if chatbot:
                await client.chat_postMessage(
                    channel=channel_id,
                    text=f"✅ You're now chatting with *{chatbot['name']}*!\n_{chatbot.get('description', 'Ready to help you!')}_"
                )
            else:
                await client.chat_postMessage(
                    channel=channel_id,
                    text="Sorry, I couldn't set up that chatbot. Please try again."
                )
                
        except Exception as e:
            logger.error(f"Error handling chatbot selection: {e}")
    
    async def _handle_document_upload_request(self, body, client):
        """Handle document upload requests"""
        try:
            channel_id = body["channel"]["id"]
            
            await client.chat_postMessage(
                channel=channel_id,
                text="📄 *How to upload documents:*\n\n" +
                     "1. Drag and drop a file (PDF, TXT, DOC, DOCX) into this channel\n" +
                     "2. The file will be automatically processed\n" +
                     "3. You can then ask questions about the document\n\n" +
                     "*Supported formats:* PDF, TXT, MD, DOC, DOCX\n" +
                     "*Maximum size:* 10MB"
            )
            
        except Exception as e:
            logger.error(f"Error handling document upload request: {e}")
    
    async def _handle_list_documents(self, body, client):
        """Handle list documents request"""
        try:
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Determine current chatbot
            chatbot_id = self._determine_chatbot(channel_id, user_id)
            
            # Get documents
            documents = await self.document_handler.get_document_list(chatbot_id, user_id)
            
            if not documents:
                await client.chat_postMessage(
                    channel=channel_id,
                    text="📄 No documents found for the current chatbot."
                )
                return
            
            # Create document list
            doc_text = "📄 *Your Documents:*\n\n"
            for i, doc in enumerate(documents, 1):
                doc_name = doc.get("filename", "Unknown")
                upload_date = doc.get("created_at", "Unknown")
                doc_text += f"{i}. {doc_name} _(uploaded: {upload_date})_\n"
            
            await client.chat_postMessage(
                channel=channel_id,
                text=doc_text
            )
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
    
    async def _handle_delete_document(self, body, client):
        """Handle delete document request"""
        # This would require additional UI for document selection
        # For now, we'll just show instructions
        try:
            channel_id = body["channel"]["id"]
            
            await client.chat_postMessage(
                channel=channel_id,
                text="🗑️ To delete documents, please contact an administrator or use the web interface."
            )
            
        except Exception as e:
            logger.error(f"Error handling delete document: {e}")
    
    async def _update_app_home(self, event, client):
        """Update the app home tab"""
        try:
            user_id = event["user"]
            
            # Get user's chatbots
            chatbots = await self._get_available_chatbots()
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Welcome to {self.config.BOT_NAME}!* {self.config.BOT_EMOJI}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": self.config.WELCOME_MESSAGE
                    }
                }
            ]
            
            # Add quick actions
            if chatbots:
                action_elements = []
                for chatbot in chatbots[:3]:  # Show max 3 quick actions
                    action_elements.append({
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": f"Chat with {chatbot['name']}"
                        },
                        "action_id": "select_chatbot",
                        "value": str(chatbot["id"])
                    })
                
                if action_elements:
                    blocks.append({
                        "type": "actions",
                        "elements": action_elements
                    })
            
            await client.views_publish(
                user_id=user_id,
                view={
                    "type": "home",
                    "blocks": blocks
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating app home: {e}")
    
    async def _get_chatbot_response(self, message: str, chatbot_id: str, session_id: str, user_id: str) -> Optional[Dict]:
        """Get response from the FastAPI backend"""
        try:
            timeout = aiohttp.ClientTimeout(total=self.config.BACKEND_TIMEOUT)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                payload = {
                    "message": message,
                    "chatbot_id": int(chatbot_id),
                    "session_id": session_id,
                    "user_id": user_id,
                    "source": "slack"
                }
                
                async with session.post(
                    f"{self.config.BACKEND_URL}/chat/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Backend returned status {response.status}: {await response.text()}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("Backend request timed out")
            return None
        except Exception as e:
            logger.error(f"Error calling backend: {e}")
            return None
    
    async def _get_available_chatbots(self) -> List[Dict]:
        """Get list of available chatbots from backend"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.config.BACKEND_URL}/chatbots/") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get chatbots: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting chatbots: {e}")
            return []
    
    async def _get_chatbot_details(self, chatbot_id: str) -> Optional[Dict]:
        """Get details of a specific chatbot"""
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.config.BACKEND_URL}/chatbots/{chatbot_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting chatbot details: {e}")
            return None
    
    def _determine_chatbot(self, channel_id: str, user_id: str = None) -> str:
        """Determine which chatbot to use based on channel and user preferences"""
        # First check user preferences
        if user_id:
            user_pref_key = f"{user_id}_{channel_id}"
            if user_pref_key in self.user_preferences:
                return self.user_preferences[user_pref_key]
        
        # Then check channel mapping
        if channel_id in self.channel_chatbot_mapping:
            return self.channel_chatbot_mapping[channel_id]
        
        # Fall back to default
        return self.config.DEFAULT_CHATBOT_ID
    
    def _clean_mention_text(self, text: str, bot_user_id: str) -> str:
        """Remove bot mention from text"""
        mention_pattern = f"<@{bot_user_id}>"
        return text.replace(mention_pattern, "").strip()
    
    async def _get_bot_user_id(self, client) -> str:
        """Get the bot's user ID"""
        try:
            response = await client.auth_test()
            return response["user_id"]
        except Exception as e:
            logger.error(f"Error getting bot user ID: {e}")
            return ""
    
    async def _show_typing_indicator(self, client, channel: str, timestamp: str):
        """Show typing indicator"""
        try:
            await client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name="thinking_face"
            )
        except Exception as e:
            logger.debug(f"Could not add thinking reaction: {e}")
    
    async def _remove_typing_indicator(self, client, channel: str, timestamp: str):
        """Remove typing indicator"""
        try:
            await client.reactions_remove(
                channel=channel,
                timestamp=timestamp,
                name="thinking_face"
            )
        except Exception as e:
            logger.debug(f"Could not remove thinking reaction: {e}")
    
    async def start(self):
        """Start the Slack bot"""
        handler = AsyncSocketModeHandler(self.app, self.config.SLACK_APP_TOKEN)
        await handler.start_async()

# Main execution
async def main():
    slack_service = EnhancedSlackChatbotService()
    logger.info("🚀 Starting Enhanced Slack Chatbot Service...")
    await slack_service.start()

if __name__ == "__main__":
    asyncio.run(main())