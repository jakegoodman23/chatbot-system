import os
import logging
import aiohttp
import tempfile
from typing import Dict, Optional, List
from slack_sdk.web.async_client import AsyncWebClient

logger = logging.getLogger(__name__)

class SlackDocumentHandler:
    """Handle document uploads and processing for Slack bot"""
    
    def __init__(self, backend_url: str, slack_token: str):
        self.backend_url = backend_url
        self.slack_token = slack_token
        
        # Supported file types
        self.supported_types = [
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ]
        
        # Max file size (10MB)
        self.max_file_size = 10 * 1024 * 1024
    
    async def handle_file_upload(self, event: Dict, client: AsyncWebClient, say) -> bool:
        """
        Handle file upload event from Slack
        Returns True if file was processed successfully
        """
        try:
            if "files" not in event:
                return False
            
            files = event["files"]
            user_id = event["user"]
            channel_id = event["channel"]
            
            # Process each file
            for file_info in files:
                success = await self._process_single_file(
                    file_info, user_id, channel_id, client, say
                )
                if not success:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling file upload: {e}")
            await say("Sorry, I encountered an error while processing your file.")
            return False
    
    async def _process_single_file(self, file_info: Dict, user_id: str, 
                                 channel_id: str, client: AsyncWebClient, say) -> bool:
        """Process a single uploaded file"""
        try:
            file_name = file_info.get("name", "unknown")
            file_type = file_info.get("mimetype", "")
            file_size = file_info.get("size", 0)
            file_url = file_info.get("url_private_download")
            
            # Validate file
            validation_result = self._validate_file(file_name, file_type, file_size)
            if not validation_result["valid"]:
                await say(validation_result["message"])
                return False
            
            # Notify user that processing has started
            await say(f"📄 Processing your file: *{file_name}*...")
            
            # Download and process file
            success = await self._download_and_process_file(
                file_url, file_name, file_type, user_id, channel_id, client
            )
            
            if success:
                await say(f"✅ Successfully processed *{file_name}*! You can now ask questions about this document.")
                return True
            else:
                await say(f"❌ Failed to process *{file_name}*. Please try again or contact support.")
                return False
                
        except Exception as e:
            logger.error(f"Error processing single file: {e}")
            return False
    
    def _validate_file(self, file_name: str, file_type: str, file_size: int) -> Dict:
        """Validate uploaded file"""
        
        # Check file size
        if file_size > self.max_file_size:
            return {
                "valid": False,
                "message": f"❌ File *{file_name}* is too large. Maximum size is 10MB."
            }
        
        # Check file type
        if file_type not in self.supported_types:
            return {
                "valid": False,
                "message": f"❌ File type `{file_type}` is not supported. Supported types: PDF, TXT, DOC, DOCX."
            }
        
        # Check file extension as backup
        allowed_extensions = [".pdf", ".txt", ".md", ".doc", ".docx"]
        file_extension = os.path.splitext(file_name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {
                "valid": False,
                "message": f"❌ File extension `{file_extension}` is not supported."
            }
        
        return {"valid": True, "message": "File is valid"}
    
    async def _download_and_process_file(self, file_url: str, file_name: str, 
                                       file_type: str, user_id: str, 
                                       channel_id: str, client: AsyncWebClient) -> bool:
        """Download file from Slack and send to backend for processing"""
        try:
            # Download file from Slack
            file_content = await self._download_file_from_slack(file_url)
            if not file_content:
                logger.error("Failed to download file from Slack")
                return False
            
            # Determine chatbot ID (you might want to make this configurable)
            chatbot_id = await self._determine_chatbot_for_upload(channel_id)
            
            # Send to backend for processing
            success = await self._upload_to_backend(
                file_content, file_name, file_type, chatbot_id, user_id
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error downloading and processing file: {e}")
            return False
    
    async def _download_file_from_slack(self, file_url: str) -> Optional[bytes]:
        """Download file content from Slack"""
        try:
            headers = {
                "Authorization": f"Bearer {self.slack_token}"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url, headers=headers) as response:
                    if response.status == 200:
                        return await response.read()
                    else:
                        logger.error(f"Failed to download file: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Error downloading file from Slack: {e}")
            return None
    
    async def _upload_to_backend(self, file_content: bytes, file_name: str, 
                               file_type: str, chatbot_id: str, user_id: str) -> bool:
        """Upload file to the FastAPI backend"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_name)[1]) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # Prepare multipart form data
                data = aiohttp.FormData()
                data.add_field('chatbot_id', chatbot_id)
                data.add_field('uploaded_by', user_id)
                data.add_field('source', 'slack')
                
                # Add file
                with open(temp_file_path, 'rb') as f:
                    data.add_field('file', f, filename=file_name, content_type=file_type)
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.backend_url}/documents/upload",
                            data=data
                        ) as response:
                            if response.status == 200:
                                logger.info(f"Successfully uploaded {file_name} to backend")
                                return True
                            else:
                                error_text = await response.text()
                                logger.error(f"Backend upload failed: {response.status} - {error_text}")
                                return False
            
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error uploading to backend: {e}")
            return False
    
    async def _determine_chatbot_for_upload(self, channel_id: str) -> str:
        """Determine which chatbot should receive the uploaded document"""
        # This is a simplified implementation
        # You might want to implement more sophisticated logic based on:
        # - Channel mapping
        # - User preferences
        # - Document type
        # - etc.
        
        from config import SlackBotConfig
        channel_mapping = SlackBotConfig.get_channel_chatbot_mapping()
        return channel_mapping.get(channel_id, SlackBotConfig.DEFAULT_CHATBOT_ID)
    
    async def get_document_list(self, chatbot_id: str, user_id: str) -> List[Dict]:
        """Get list of documents for a specific chatbot"""
        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "chatbot_id": chatbot_id,
                    "uploaded_by": user_id
                }
                
                async with session.get(
                    f"{self.backend_url}/documents/",
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to get documents: {response.status}")
                        return []
                        
        except Exception as e:
            logger.error(f"Error getting document list: {e}")
            return []
    
    async def delete_document(self, document_id: str, user_id: str) -> bool:
        """Delete a document"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(
                    f"{self.backend_url}/documents/{document_id}",
                    params={"user_id": user_id}
                ) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False