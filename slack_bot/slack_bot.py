import os
import asyncio
import logging
from typing import Dict, Optional, List
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
import aiohttp
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SlackChatbotService:
    def __init__(self):
        self.app = AsyncApp(
            token=os.environ.get("SLACK_BOT_TOKEN"),
            signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
        )
        
        # Your FastAPI backend URL
        self.backend_url = os.environ.get("CHATBOT_BACKEND_URL", "http://localhost:8000")
        
        # Channel to chatbot mapping
        self.channel_chatbot_mapping = {
            # Add your channel IDs and corresponding chatbot IDs here
            # "C1234567890": "customer-support-bot",
            # "C0987654321": "technical-docs-bot",
        }
        
        # Default chatbot for unmapped channels/DMs
        self.default_chatbot = os.environ.get("DEFAULT_CHATBOT_ID", "1")  # Assuming first chatbot as default
        
        # Setup event handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup all Slack event handlers"""
        
        # Handle app mentions (@bot_name)
        @self.app.event("app_mention")
        async def handle_app_mention(event, say, client):
            await self._handle_user_message(event, say, client, is_mention=True)
        
        # Handle direct messages
        @self.app.event("message")
        async def handle_direct_message(event, say, client):
            # Only handle DMs (not channel messages to avoid duplicates with mentions)
            if event.get("channel_type") == "im":
                await self._handle_user_message(event, say, client, is_mention=False)
        
        # Handle slash commands
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
        
        # Handle button interactions
        @self.app.action("select_chatbot")
        async def handle_chatbot_selection(ack, body, client):
            await ack()
            await self._handle_chatbot_selection(body, client)
            
        @self.app.action("upload_document")
        async def handle_document_upload(ack, body, client):
            await ack()
            await self._handle_document_upload_request(body, client)
    
    async def _handle_user_message(self, event, say, client, is_mention: bool):
        """Handle user messages (mentions or DMs)"""
        try:
            user_id = event["user"]
            channel_id = event["channel"]
            text = event["text"]
            
            # Remove bot mention from text if it's a mention
            if is_mention:
                # Remove <@BOTID> from the beginning of the message
                bot_user_id = await self._get_bot_user_id(client)
                text = self._clean_mention_text(text, bot_user_id)
            
            # Show typing indicator
            await self._show_typing_indicator(client, channel_id, event["ts"])
            
            # Determine which chatbot to use
            chatbot_id = self._determine_chatbot(channel_id)
            
            # Create session ID
            session_id = f"slack_{user_id}_{channel_id}"
            
            # Get response from backend
            response = await self._get_chatbot_response(
                message=text,
                chatbot_id=chatbot_id,
                session_id=session_id,
                user_id=user_id
            )
            
            # Remove typing indicator
            await self._remove_typing_indicator(client, channel_id, event["ts"])
            
            if response:
                await say(response["message"])
            else:
                await say("Sorry, I'm having trouble processing your request right now. Please try again later.")
                
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
                    await say("Please provide a question after the command. Example: `/ask What is your return policy?`")
                    return
                
                # Determine chatbot
                chatbot_id = self._determine_chatbot(channel_id)
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
            # Get available chatbots from backend
            chatbots = await self._get_available_chatbots()
            
            if not chatbots:
                await client.chat_postMessage(
                    channel=command["channel_id"],
                    text="No chatbots are currently available."
                )
                return
            
            # Create buttons for each chatbot
            elements = []
            for chatbot in chatbots[:5]:  # Limit to 5 buttons per row
                elements.append({
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": chatbot["name"][:75]  # Slack button text limit
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
    
    async def _handle_chatbot_selection(self, body, client):
        """Handle chatbot selection from interactive menu"""
        try:
            selected_chatbot_id = body["actions"][0]["value"]
            user_id = body["user"]["id"]
            channel_id = body["channel"]["id"]
            
            # Store user's chatbot preference (you might want to use a database for persistence)
            # For now, we'll just update the channel mapping
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
                text="📄 To upload a document, simply drag and drop a file (PDF or TXT) into this channel and mention me, or use the file upload button in Slack!"
            )
            
        except Exception as e:
            logger.error(f"Error handling document upload request: {e}")
    
    async def _get_chatbot_response(self, message: str, chatbot_id: str, session_id: str, user_id: str) -> Optional[Dict]:
        """Get response from the FastAPI backend"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": message,
                    "chatbot_id": int(chatbot_id),
                    "session_id": session_id,
                    "user_id": user_id,
                    "source": "slack"
                }
                
                async with session.post(
                    f"{self.backend_url}/chat/",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Backend returned status {response.status}: {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error calling backend: {e}")
            return None
    
    async def _get_available_chatbots(self) -> List[Dict]:
        """Get list of available chatbots from backend"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/chatbots/") as response:
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
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/chatbots/{chatbot_id}") as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return None
                        
        except Exception as e:
            logger.error(f"Error getting chatbot details: {e}")
            return None
    
    def _determine_chatbot(self, channel_id: str) -> str:
        """Determine which chatbot to use based on channel"""
        return self.channel_chatbot_mapping.get(channel_id, self.default_chatbot)
    
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
        handler = AsyncSocketModeHandler(self.app, os.environ.get("SLACK_APP_TOKEN"))
        await handler.start_async()

# Main execution
async def main():
    slack_service = SlackChatbotService()
    logger.info("🚀 Starting Slack Chatbot Service...")
    await slack_service.start()

if __name__ == "__main__":
    asyncio.run(main())