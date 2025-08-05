"""
Notion API client for monitoring database changes and extracting task information.
"""

import logging
from typing import Dict, List, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError
from app.config import config

logger = logging.getLogger(__name__)


class NotionClient:
    """Client for interacting with Notion API."""
    
    def __init__(self):
        self.client = Client(auth=config.notion_token)
        self.database_id = config.notion_database_id
    
    def test_connection(self) -> bool:
        """Test the connection to Notion API."""
        try:
            # Try to retrieve database info
            self.client.databases.retrieve(database_id=self.database_id)
            logger.info("Notion API connection successful")
            return True
        except Exception as e:
            logger.error(f"Notion API connection failed: {e}")
            return False
    
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users in the workspace."""
        try:
            response = self.client.users.list()
            users = []
            for user in response.get('results', []):
                users.append({
                    'id': user['id'],
                    'name': user.get('name', 'Unknown'),
                    'type': user.get('type', 'person'),
                    'email': user.get('person', {}).get('email') if user.get('person') else None
                })
            logger.info(f"Retrieved {len(users)} users from Notion")
            return users
        except Exception as e:
            logger.error(f"Failed to list Notion users: {e}")
            return []
    
    def get_database_schema(self) -> Dict[str, Any]:
        """Get the schema of the monitored database."""
        try:
            response = self.client.databases.retrieve(database_id=self.database_id)
            return response.get('properties', {})
        except Exception as e:
            logger.error(f"Failed to get database schema: {e}")
            return {}
    
    def extract_task_info(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant task information from a Notion page."""
        try:
            properties = page_data.get('properties', {})
            
            # Extract basic task info
            task_info = {
                'id': page_data.get('id'),
                'url': page_data.get('url'),
                'created_time': page_data.get('created_time'),
                'last_edited_time': page_data.get('last_edited_time'),
                'title': '',
                'assigned_users': [],
                'status': '',
                'priority': '',
                'due_date': None,
                'description': ''
            }
            
            # Extract title (usually in a 'Name' or 'Title' property)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_items = prop_data.get('title', [])
                    if title_items:
                        task_info['title'] = ''.join([item.get('plain_text', '') for item in title_items])
                    break
            
            # Extract assigned users (people property)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'people':
                    people = prop_data.get('people', [])
                    task_info['assigned_users'] = [person.get('id') for person in people]
                    break
            
            # Extract status (select property)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'select' and 'status' in prop_name.lower():
                    select_data = prop_data.get('select')
                    if select_data:
                        task_info['status'] = select_data.get('name', '')
                    break
            
            # Extract priority (select property)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'select' and 'priority' in prop_name.lower():
                    select_data = prop_data.get('select')
                    if select_data:
                        task_info['priority'] = select_data.get('name', '')
                    break
            
            # Extract due date (date property)
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'date' and ('due' in prop_name.lower() or 'deadline' in prop_name.lower()):
                    date_data = prop_data.get('date')
                    if date_data:
                        task_info['due_date'] = date_data.get('start')
                    break
            
            logger.info(f"Extracted task info for: {task_info['title']}")
            return task_info
            
        except Exception as e:
            logger.error(f"Failed to extract task info: {e}")
            return {}
    
    def get_page_content(self, page_id: str) -> Dict[str, Any]:
        """Get full page content including blocks."""
        try:
            # Get page properties
            page = self.client.pages.retrieve(page_id=page_id)
            
            # Get page blocks (content)
            blocks_response = self.client.blocks.children.list(block_id=page_id)
            blocks = blocks_response.get('results', [])
            
            # Extract text content from blocks
            content_text = []
            for block in blocks:
                if block.get('type') == 'paragraph':
                    paragraph = block.get('paragraph', {})
                    rich_text = paragraph.get('rich_text', [])
                    text = ''.join([item.get('plain_text', '') for item in rich_text])
                    if text.strip():
                        content_text.append(text.strip())
            
            return {
                'page': page,
                'content': '\n'.join(content_text)
            }
            
        except Exception as e:
            logger.error(f"Failed to get page content for {page_id}: {e}")
            return {}
    
    def process_webhook_payload(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process webhook payload from Notion and extract task information."""
        try:
            # Notion webhook payload structure varies, but typically contains page data
            if payload.get('object') == 'page':
                page_data = payload
            else:
                # Handle other payload structures
                page_data = payload.get('page', {})
            
            if not page_data:
                logger.warning("No page data found in webhook payload")
                return None
            
            # Extract task information
            task_info = self.extract_task_info(page_data)
            
            # Only process if there are assigned users
            if not task_info.get('assigned_users'):
                logger.info("No assigned users found, skipping notification")
                return None
            
            return task_info
            
        except Exception as e:
            logger.error(f"Failed to process webhook payload: {e}")
            return None