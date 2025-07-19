import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@chatbot.local")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
    def send_human_support_notification(
        self, 
        admin_email: str, 
        chatbot_name: str, 
        user_message: str,
        support_request_id: str,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None
    ) -> bool:
        """Send email notification to admin when user requests human support"""
        try:
            subject = f"Human Support Request - {chatbot_name}"
            
            # Create email content
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #739CFC; border-bottom: 2px solid #739CFC; padding-bottom: 10px;">
                            Human Support Request
                        </h2>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #495057;">Request Details</h3>
                            <p><strong>Chatbot:</strong> {chatbot_name}</p>
                            <p><strong>Request ID:</strong> {support_request_id}</p>
                            {f'<p><strong>User Name:</strong> {user_name}</p>' if user_name else ''}
                            {f'<p><strong>User Email:</strong> {user_email}</p>' if user_email else ''}
                            <p><strong>Time:</strong> {self._get_current_time()}</p>
                        </div>
                        
                        <div style="background: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <h3 style="margin-top: 0; color: #495057;">User Message</h3>
                            <p style="background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #739CFC;">
                                {user_message}
                            </p>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{self._get_admin_url(support_request_id)}" 
                               style="background: #739CFC; color: white; padding: 12px 30px; 
                                      text-decoration: none; border-radius: 5px; display: inline-block;">
                                Join Conversation
                            </a>
                        </div>
                        
                        <div style="border-top: 1px solid #dee2e6; padding-top: 20px; margin-top: 30px;">
                            <p style="color: #6c757d; font-size: 14px;">
                                This is an automated notification from your chatbot system. 
                                Please respond to the user as soon as possible.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            text_body = f"""
            Human Support Request - {chatbot_name}
            
            Request Details:
            - Chatbot: {chatbot_name}
            - Request ID: {support_request_id}
            {f'- User Name: {user_name}' if user_name else ''}
            {f'- User Email: {user_email}' if user_email else ''}
            - Time: {self._get_current_time()}
            
            User Message:
            {user_message}
            
            Please visit your admin panel to join the conversation: {self._get_admin_url(support_request_id)}
            """
            
            return self._send_email(admin_email, subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send human support notification: {str(e)}")
            return False
    
    def send_user_confirmation(
        self,
        user_email: str,
        chatbot_name: str,
        support_request_id: str
    ) -> bool:
        """Send confirmation email to user that their support request was received"""
        try:
            subject = f"Support Request Received - {chatbot_name}"
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #739CFC; border-bottom: 2px solid #739CFC; padding-bottom: 10px;">
                            Support Request Received
                        </h2>
                        
                        <p>Thank you for reaching out! We've received your request for human support.</p>
                        
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            <p><strong>Request ID:</strong> {support_request_id}</p>
                            <p><strong>Chatbot:</strong> {chatbot_name}</p>
                            <p><strong>Status:</strong> Pending</p>
                        </div>
                        
                        <p>A human agent will join your conversation shortly. You can continue chatting in the same window where you made this request.</p>
                        
                        <div style="border-top: 1px solid #dee2e6; padding-top: 20px; margin-top: 30px;">
                            <p style="color: #6c757d; font-size: 14px;">
                                This is an automated confirmation. Please do not reply to this email.
                            </p>
                        </div>
                    </div>
                </body>
            </html>
            """
            
            text_body = f"""
            Support Request Received - {chatbot_name}
            
            Thank you for reaching out! We've received your request for human support.
            
            Request ID: {support_request_id}
            Chatbot: {chatbot_name}
            Status: Pending
            
            A human agent will join your conversation shortly. You can continue chatting in the same window where you made this request.
            """
            
            return self._send_email(user_email, subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Failed to send user confirmation: {str(e)}")
            return False
    
    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        """Send email using SMTP"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Attach text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')
            
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    def _get_current_time(self) -> str:
        """Get current time formatted for display"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def _get_admin_url(self, support_request_id: str) -> str:
        """Get admin URL for the support request"""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return f"{base_url}/admin.html#support/{support_request_id}"