"""
Main Flask application for the Telegram Notion NDR system.
Provides webhook endpoints and health checks.
"""

import logging
from flask import Flask, request, jsonify
from app.config import config
from app.notion_client import NotionClient
from app.telegram_client import TelegramClient
from app.webhook_handler import WebhookHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Initialize components
webhook_handler = WebhookHandler()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'telegram-notion-ndr',
        'version': '1.0.0'
    })


@app.route('/webhook/notion', methods=['POST'])
def notion_webhook():
    """Handle incoming webhooks from Notion."""
    try:
        logger.info("Received Notion webhook request")
        result = webhook_handler.process_notion_webhook(request)
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', result.get('error')),
            'task_title': result.get('task_title')
        }), result.get('status_code', 200)
        
    except Exception as e:
        logger.error(f"Error in notion webhook handler: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500


@app.route('/test/notion', methods=['GET'])
def test_notion():
    """Test Notion API connection."""
    try:
        notion_client = NotionClient()
        connected = notion_client.test_connection()
        
        if connected:
            # Also get database schema for debugging
            schema = notion_client.get_database_schema()
            return jsonify({
                'success': True,
                'message': 'Notion API connection successful',
                'database_properties': list(schema.keys()) if schema else []
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Notion API connection failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing Notion connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/test/telegram', methods=['GET'])
def test_telegram():
    """Test Telegram bot connection."""
    try:
        telegram_client = TelegramClient()
        connected = telegram_client.test_connection()
        
        if connected:
            # Also get chat info for debugging
            chat_info = telegram_client.get_chat_info()
            return jsonify({
                'success': True,
                'message': 'Telegram bot connection successful',
                'chat_info': chat_info
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Telegram bot connection failed'
            }), 500
            
    except Exception as e:
        logger.error(f"Error testing Telegram connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/test/notification', methods=['POST'])
def test_notification():
    """Send a test notification to verify the complete flow."""
    try:
        result = webhook_handler.test_notification_flow()
        
        return jsonify({
            'success': result['success'],
            'message': result.get('message', result.get('error')),
            'sample_task': result.get('sample_task')
        }), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Error testing notification flow: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/users/notion', methods=['GET'])
def list_notion_users():
    """List all users in the Notion workspace (for configuration setup)."""
    try:
        notion_client = NotionClient()
        users = notion_client.list_users()
        
        return jsonify({
            'success': True,
            'users': users,
            'count': len(users)
        })
        
    except Exception as e:
        logger.error(f"Error listing Notion users: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/config/reload', methods=['POST'])
def reload_config():
    """Reload configuration from file."""
    try:
        config.reload_config()
        return jsonify({
            'success': True,
            'message': 'Configuration reloaded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error reloading configuration: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    try:
        logger.info("Starting Telegram Notion NDR service...")
        logger.info(f"Server will run on port {config.port}")
        
        # Test connections on startup
        logger.info("Testing API connections...")
        
        notion_client = NotionClient()
        if notion_client.test_connection():
            logger.info("✅ Notion API connection successful")
        else:
            logger.warning("❌ Notion API connection failed")
        
        telegram_client = TelegramClient()
        if telegram_client.test_connection():
            logger.info("✅ Telegram bot connection successful")
        else:
            logger.warning("❌ Telegram bot connection failed")
        
        logger.info("Service started successfully!")
        app.run(host='0.0.0.0', port=config.port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        exit(1)