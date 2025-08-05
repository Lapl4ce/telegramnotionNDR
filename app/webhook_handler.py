"""
Webhook handler for processing Notion database updates and triggering notifications.
"""

import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from flask import Request
from app.config import config
from app.notion_client import NotionClient
from app.telegram_client import TelegramClient

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Handles webhook requests from Notion and processes task updates."""
    
    def __init__(self):
        self.notion_client = NotionClient()
        self.telegram_client = TelegramClient()
    
    def verify_webhook_signature(self, request: Request) -> bool:
        """Verify webhook signature for security (if webhook secret is configured)."""
        webhook_secret = config.webhook_secret
        if not webhook_secret:
            # If no secret is configured, skip verification
            logger.warning("No webhook secret configured - skipping signature verification")
            return True
        
        try:
            # Get signature from headers
            signature = request.headers.get('X-Notion-Signature')
            if not signature:
                logger.error("No signature found in webhook headers")
                return False
            
            # Calculate expected signature
            expected_signature = hmac.new(
                webhook_secret.encode('utf-8'),
                request.get_data(),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            if not hmac.compare_digest(signature, expected_signature):
                logger.error("Webhook signature verification failed")
                return False
            
            logger.info("Webhook signature verified successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def process_notion_webhook(self, request: Request) -> Dict[str, Any]:
        """Process incoming webhook from Notion."""
        try:
            # Verify signature if configured
            if not self.verify_webhook_signature(request):
                return {
                    'success': False,
                    'error': 'Signature verification failed',
                    'status_code': 401
                }
            
            # Get JSON payload
            try:
                payload = request.get_json()
                if not payload:
                    return {
                        'success': False,
                        'error': 'No JSON payload received',
                        'status_code': 400
                    }
            except Exception as e:
                logger.error(f"Failed to parse JSON payload: {e}")
                return {
                    'success': False,
                    'error': 'Invalid JSON payload',
                    'status_code': 400
                }
            
            logger.info(f"Received webhook payload: {payload.get('object', 'unknown')}")
            
            # Process the payload
            task_info = self.notion_client.process_webhook_payload(payload)
            
            if not task_info:
                return {
                    'success': True,
                    'message': 'No action required',
                    'status_code': 200
                }
            
            # Send notification to Telegram
            notification_sent = self.telegram_client.send_task_notification(task_info)
            
            if notification_sent:
                logger.info(f"Successfully sent notification for task: {task_info.get('title', 'Unknown')}")
                return {
                    'success': True,
                    'message': 'Notification sent successfully',
                    'task_title': task_info.get('title'),
                    'status_code': 200
                }
            else:
                logger.error(f"Failed to send notification for task: {task_info.get('title', 'Unknown')}")
                return {
                    'success': False,
                    'error': 'Failed to send Telegram notification',
                    'task_title': task_info.get('title'),
                    'status_code': 500
                }
        
        except Exception as e:
            logger.error(f"Error processing Notion webhook: {e}")
            return {
                'success': False,
                'error': f'Internal server error: {str(e)}',
                'status_code': 500
            }
    
    def handle_database_update(self, database_id: str, page_id: str) -> bool:
        """Handle a specific database page update (for manual triggers)."""
        try:
            # Get page content from Notion
            page_data = self.notion_client.get_page_content(page_id)
            if not page_data:
                logger.error(f"Failed to retrieve page data for {page_id}")
                return False
            
            # Extract task information
            task_info = self.notion_client.extract_task_info(page_data['page'])
            if not task_info:
                logger.error(f"Failed to extract task info for {page_id}")
                return False
            
            # Check if there are assigned users
            if not task_info.get('assigned_users'):
                logger.info(f"No assigned users for task {page_id}, skipping notification")
                return True
            
            # Send notification
            return self.telegram_client.send_task_notification(task_info)
            
        except Exception as e:
            logger.error(f"Error handling database update for {page_id}: {e}")
            return False
    
    def test_notification_flow(self) -> Dict[str, Any]:
        """Test the complete notification flow with sample data."""
        try:
            # Create sample task data
            sample_task = {
                'id': 'test-task-id',
                'title': 'Test Task Notification',
                'status': 'In Progress',
                'priority': 'High',
                'due_date': '2024-12-31',
                'assigned_users': list(config.user_mappings.keys())[:1] if config.user_mappings else [],
                'url': 'https://notion.so/test-task'
            }
            
            # Send test notification
            success = self.telegram_client.send_task_notification(sample_task)
            
            return {
                'success': success,
                'message': 'Test notification sent' if success else 'Test notification failed',
                'sample_task': sample_task
            }
            
        except Exception as e:
            logger.error(f"Error testing notification flow: {e}")
            return {
                'success': False,
                'error': str(e)
            }