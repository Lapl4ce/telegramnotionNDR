# Telegram Notion NDR (Notification Data Router)

An automation system that monitors Notion task databases and sends Telegram notifications when specific users are tagged in tasks.

## Features

- **Notion Integration**: Monitors specified Notion databases for task updates
- **Telegram Notifications**: Sends formatted messages to Telegram channels/groups  
- **User Tagging**: Maps Notion users to Telegram users and tags them in notifications
- **Webhook Support**: Receives real-time updates from Notion via webhooks
- **Configuration Management**: Easy setup via environment variables and config files
- **Error Handling**: Comprehensive logging and error recovery

## Setup

### 1. Prerequisites

- Python 3.8+
- Notion account with API access
- Telegram bot token
- A Notion database set up as a task manager

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/Lapl4ce/telegramnotionNDR.git
cd telegramnotionNDR

# Install dependencies
pip install -r requirements.txt

# Copy example configuration
cp config.example.json config.json
```

### 3. Configuration

#### Environment Variables

Create a `.env` file with the following variables:

```env
# Notion Configuration
NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Telegram Configuration  
TELEGRAM_BOT_TOKEN=xxxxxxxxx:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=-xxxxxxxxx

# Webhook Configuration (optional)
WEBHOOK_SECRET=your_webhook_secret_key
PORT=5000
```

#### Configuration File

Edit `config.json` to map Notion users to Telegram users:

```json
{
  "user_mappings": {
    "notion_user_id_1": {
      "telegram_username": "telegram_user1",
      "telegram_user_id": 123456789
    },
    "notion_user_id_2": {
      "telegram_username": "telegram_user2", 
      "telegram_user_id": 987654321
    }
  },
  "notification_settings": {
    "include_task_details": true,
    "include_due_date": true,
    "mention_users": true
  }
}
```

### 4. Getting Required IDs

#### Notion Database ID
1. Open your Notion database in a browser
2. Copy the database ID from the URL: `https://notion.so/workspace/DATABASE_ID?v=...`

#### Notion User IDs  
1. Use the Notion API to list users in your workspace
2. Run: `python -c "from app.notion_client import NotionClient; client = NotionClient(); print(client.list_users())"`

#### Telegram Chat ID
1. Add your bot to the target channel/group
2. Send a message and visit: `https://api.telegram.org/bot{BOT_TOKEN}/getUpdates`
3. Find the chat ID in the response

### 5. Setting up Notion Webhook (Optional)

For real-time notifications, set up a Notion webhook:

1. Use ngrok or deploy to a public server to expose your webhook endpoint
2. Register webhook with Notion API pointing to `https://your-domain.com/webhook/notion`
3. Set the `WEBHOOK_SECRET` environment variable

## Usage

### Running the Application

```bash
# Development mode
python main.py

# Production mode with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

### Manual Testing

Test the notification system without webhooks:

```bash
# Test Notion connection
python -c "from app.notion_client import NotionClient; client = NotionClient(); print('Notion connected:', client.test_connection())"

# Test Telegram connection  
python -c "from app.telegram_client import TelegramClient; client = TelegramClient(); print('Telegram connected:', client.test_connection())"

# Send test notification
python -c "from app.telegram_client import TelegramClient; client = TelegramClient(); client.send_test_message()"
```

## How It Works

1. **Webhook Reception**: The Flask app receives webhook notifications from Notion when database changes occur
2. **Data Processing**: The system extracts task details and identifies tagged users
3. **User Mapping**: Notion user IDs are mapped to Telegram usernames/IDs using the configuration
4. **Message Formatting**: A formatted message is created with task details and user mentions
5. **Telegram Delivery**: The message is sent to the configured Telegram chat with user tags

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /webhook/notion` - Receives Notion webhook notifications
- `GET /test/notion` - Test Notion API connection
- `GET /test/telegram` - Test Telegram bot connection

## File Structure

```
telegramnotionNDR/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── notion_client.py      # Notion API integration
│   ├── telegram_client.py    # Telegram bot integration
│   └── webhook_handler.py    # Webhook processing logic
├── main.py                   # Flask application entry point
├── requirements.txt          # Python dependencies
├── config.example.json       # Example configuration file
└── README.md                # This file
```

## Error Handling

- All API calls include retry logic and error handling
- Failed notifications are logged with full error details
- The system continues operating even if individual notifications fail
- Health check endpoints help monitor system status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.