"""
Configuration management for the Telegram Notion NDR system.
Handles environment variables, config files, and user mappings.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self._config_data = {}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file and environment variables."""
        # Load from config file if it exists
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self._config_data = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
                self._config_data = {}
        else:
            logger.warning(f"Config file {self.config_file} not found, using defaults")
            self._config_data = {}
    
    @property
    def notion_token(self) -> str:
        """Get Notion API token from environment."""
        token = os.getenv('NOTION_TOKEN')
        if not token:
            raise ValueError("NOTION_TOKEN environment variable is required")
        return token
    
    @property
    def notion_database_id(self) -> str:
        """Get Notion database ID from environment."""
        db_id = os.getenv('NOTION_DATABASE_ID')
        if not db_id:
            raise ValueError("NOTION_DATABASE_ID environment variable is required")
        return db_id
    
    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token from environment."""
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
        return token
    
    @property
    def telegram_chat_id(self) -> str:
        """Get Telegram chat ID from environment."""
        chat_id = os.getenv('TELEGRAM_CHAT_ID')
        if not chat_id:
            raise ValueError("TELEGRAM_CHAT_ID environment variable is required")
        return chat_id
    
    @property
    def webhook_secret(self) -> Optional[str]:
        """Get webhook secret from environment (optional)."""
        return os.getenv('WEBHOOK_SECRET')
    
    @property
    def port(self) -> int:
        """Get server port from environment (default: 5000)."""
        return int(os.getenv('PORT', 5000))
    
    @property
    def user_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Get user mappings from config file."""
        return self._config_data.get('user_mappings', {})
    
    @property
    def notification_settings(self) -> Dict[str, Any]:
        """Get notification settings from config file."""
        default_settings = {
            'include_task_details': True,
            'include_due_date': True,
            'mention_users': True
        }
        return self._config_data.get('notification_settings', default_settings)
    
    def get_telegram_user(self, notion_user_id: str) -> Optional[Dict[str, Any]]:
        """Get Telegram user info for a given Notion user ID."""
        return self.user_mappings.get(notion_user_id)
    
    def reload_config(self):
        """Reload configuration from file."""
        self._load_config()


# Global config instance
config = Config()