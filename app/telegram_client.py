"""
Telegram bot client for sending notifications and managing user interactions.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from telegram import Bot
from telegram.error import TelegramError
from app.config import config

logger = logging.getLogger(__name__)


class TelegramClient:
    """Client for interacting with Telegram Bot API."""
    
    def __init__(self):
        self.bot = Bot(token=config.telegram_bot_token)
        self.chat_id = config.telegram_chat_id
    
    def test_connection(self) -> bool:
        """Test the connection to Telegram Bot API."""
        try:
            # Run async method in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                bot_info = loop.run_until_complete(self.bot.get_me())
                logger.info(f"Telegram bot connection successful: @{bot_info.username}")
                return True
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Telegram bot connection failed: {e}")
            return False
    
    def format_task_message(self, task_info: Dict[str, Any]) -> str:
        """Format task information into a Telegram message."""
        try:
            settings = config.notification_settings
            
            # Build message components
            message_parts = []
            
            # Task title
            title = task_info.get('title', 'Untitled Task')
            message_parts.append(f"📋 *{title}*")
            
            # Task details if enabled
            if settings.get('include_task_details', True):
                if task_info.get('status'):
                    message_parts.append(f"🔄 Status: {task_info['status']}")
                
                if task_info.get('priority'):
                    priority_emoji = {
                        'High': '🔴',
                        'Medium': '🟡', 
                        'Low': '🟢'
                    }.get(task_info['priority'], '⚪')
                    message_parts.append(f"{priority_emoji} Priority: {task_info['priority']}")
            
            # Due date if enabled and available
            if settings.get('include_due_date', True) and task_info.get('due_date'):
                message_parts.append(f"📅 Due: {task_info['due_date']}")
            
            # URL link to task
            if task_info.get('url'):
                message_parts.append(f"🔗 [View Task]({task_info['url']})")
            
            # User mentions if enabled
            if settings.get('mention_users', True):
                assigned_users = task_info.get('assigned_users', [])
                if assigned_users:
                    mentions = []
                    for notion_user_id in assigned_users:
                        telegram_user = config.get_telegram_user(notion_user_id)
                        if telegram_user:
                            username = telegram_user.get('telegram_username')
                            if username:
                                mentions.append(f"@{username}")
                    
                    if mentions:
                        message_parts.append(f"👥 Assigned: {', '.join(mentions)}")
            
            return '\n'.join(message_parts)
            
        except Exception as e:
            logger.error(f"Failed to format task message: {e}")
            return f"📋 Task Update: {task_info.get('title', 'Unknown Task')}"
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to the configured Telegram chat."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self.bot.send_message(
                        chat_id=self.chat_id,
                        text=message,
                        parse_mode=parse_mode,
                        disable_web_page_preview=True
                    )
                )
                logger.info("Message sent successfully to Telegram")
                return True
            finally:
                loop.close()
                
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_task_notification(self, task_info: Dict[str, Any]) -> bool:
        """Send a formatted task notification to Telegram."""
        try:
            message = self.format_task_message(task_info)
            return self.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send task notification: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message to verify bot functionality."""
        test_message = (
            "🤖 *Telegram Notion NDR Test*\n\n"
            "✅ Bot is working correctly!\n"
            "📊 System is ready to send task notifications."
        )
        return self.send_message(test_message)
    
    def get_chat_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the configured chat."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                chat = loop.run_until_complete(self.bot.get_chat(chat_id=self.chat_id))
                return {
                    'id': chat.id,
                    'type': chat.type,
                    'title': getattr(chat, 'title', None),
                    'username': getattr(chat, 'username', None),
                    'description': getattr(chat, 'description', None)
                }
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Failed to get chat info: {e}")
            return None