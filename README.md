# AI Chatbot

A general-purpose conversational AI chatbot built with Python, Flask, and OpenAI's GPT models.

## Features

✨ **Core Features:**
- Natural language understanding powered by OpenAI GPT-4
- Multi-turn conversation with context memory
- Persistent conversation storage with SQLite/PostgreSQL
- RESTful API for easy integration
- User management system
- Conversation history tracking
- Token usage monitoring
- CORS support for web applications

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/palaieski-a11y/ai-chatbot.git
   cd ai-chatbot
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-...
   ```

## Configuration

Edit `.env` to customize:

```env
# OpenAI Settings
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4  # or gpt-3.5-turbo

# Server Settings
FLASK_PORT=5000
FLASK_DEBUG=True

# Database (SQLite or PostgreSQL)
DATABASE_URL=sqlite:///chatbot.db

# Chatbot Settings
MAX_CONVERSATION_HISTORY=50
CONVERSATION_TIMEOUT=3600
```

## Usage

### Start the Server

```bash
python app.py
```

The API will be available at `http://localhost:5000`

### API Endpoints

#### 1. Health Check
```bash
GET /health
```

#### 2. Create User
```bash
POST /api/users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com"
}
```

**Response:**
```json
{
  "user_id": "uuid",
  "username": "john_doe",
  "email": "john@example.com"
}
```

#### 3. Create Conversation
```bash
POST /api/conversations
Content-Type: application/json

{
  "user_id": "uuid",
  "title": "General Chat"
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "title": "General Chat",
  "created_at": "timestamp"
}
```

#### 4. Send Message
```bash
POST /api/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "message": "Hello, how are you?",
  "temperature": 0.7
}
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "user_message": "Hello, how are you?",
  "bot_response": "I'm doing well, thank you for asking! How can I help you today?"
}
```

#### 5. Get Conversation History
```bash
GET /api/conversations/{conversation_id}/history
```

**Response:**
```json
{
  "conversation_id": "uuid",
  "messages": [
    {"role": "user", "content": "Hello"},
    {"role": "assistant", "content": "Hi there!"}
  ]
}
```

#### 6. Reset Conversation
```bash
POST /api/conversations/{conversation_id}/reset
```

#### 7. Close Conversation
```bash
POST /api/conversations/{conversation_id}/close
```

## Example Usage

### Python Client

```python
import requests
import json

BASE_URL = "http://localhost:5000/api"

# Create user
user_response = requests.post(f"{BASE_URL}/users", json={
    "username": "alice",
    "email": "alice@example.com"
})
user_id = user_response.json()["user_id"]

# Create conversation
conv_response = requests.post(f"{BASE_URL}/conversations", json={
    "user_id": user_id,
    "title": "My Chat"
})
conversation_id = conv_response.json()["conversation_id"]

# Send message
msg_response = requests.post(
    f"{BASE_URL}/conversations/{conversation_id}/messages",
    json={"message": "What is machine learning?"}
)
print(msg_response.json()["bot_response"])
```

### cURL

```bash
# Create user
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "bob", "email": "bob@example.com"}'

# Send message
curl -X POST http://localhost:5000/api/conversations/CONV_ID/messages \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me a joke"}'
```

## Project Structure

```
ai-chatbot/
├── app.py                 # Flask application and routes
├── chatbot.py             # Core chatbot logic
├── database.py            # Database models and setup
├── config.py              # Configuration management
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Database

The chatbot uses SQLite by default (stored in `chatbot.db`). To use PostgreSQL:

1. Install PostgreSQL
2. Create a database: `createdb chatbot_db`
3. Update `.env`:
   ```
   DATABASE_URL=postgresql://user:password@localhost/chatbot_db
   ```
4. Run the app to create tables

## Logging

Logs are printed to console and can be configured in `config.py`. Adjust `LOG_LEVEL` in `.env` (DEBUG, INFO, WARNING, ERROR).

## Performance Considerations

- **Conversation History**: Limited to 50 messages by default (configurable)
- **Temperature**: Controls randomness (0.0 = deterministic, 1.0 = creative)
- **Token Usage**: Monitored and stored for cost tracking
- **Database Indexing**: Add indexes for frequently queried fields in production

## Troubleshooting

### "Invalid API Key" Error
- Check your OpenAI API key in `.env`
- Ensure the key starts with `sk-`
- Verify your API key has sufficient balance

### Database Errors
- Delete `chatbot.db` and restart to reinitialize
- Check database permissions
- Verify DATABASE_URL format

### CORS Issues
- CORS is enabled by default
- Modify `CORS(app)` in `app.py` to restrict origins if needed

## Future Enhancements

- [ ] Advanced memory/context management
- [ ] Multi-language support
- [ ] Custom knowledge base integration
- [ ] Rate limiting
- [ ] User authentication
- [ ] Analytics dashboard
- [ ] Webhook support
- [ ] Docker deployment
- [ ] Unit and integration tests

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Support

For issues, questions, or contributions, please open a GitHub issue or submit a pull request.

## Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://www.sqlalchemy.org/)
- [Python-dotenv](https://github.com/theskumar/python-dotenv)
