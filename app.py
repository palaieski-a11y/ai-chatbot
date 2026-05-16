import logging
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from chatbot import ChatBot
from config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Load configuration
app.config.from_object(config['development'])

# Initialize chatbot
chatbot = ChatBot()

# Store active conversations in memory (in production, use database/cache)
active_conversations = {}

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "AI Chatbot"}), 200

@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        
        if not username:
            return jsonify({"error": "Username is required"}), 400
        
        user_id = str(uuid.uuid4())
        success = chatbot.create_user(user_id, username, email)
        
        if success:
            return jsonify({
                "user_id": user_id,
                "username": username,
                "email": email
            }), 201
        else:
            return jsonify({"error": "Failed to create user"}), 500
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        title = data.get('title', 'New Conversation')
        
        if not user_id:
            return jsonify({"error": "User ID is required"}), 400
        
        conversation_id = chatbot.create_conversation(user_id, title)
        
        if conversation_id:
            active_conversations[conversation_id] = user_id
            return jsonify({
                "conversation_id": conversation_id,
                "title": title,
                "created_at": str(uuid.uuid4())
            }), 201
        else:
            return jsonify({"error": "Failed to create conversation"}), 500
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>/messages', methods=['POST'])
def send_message(conversation_id):
    """Send a message to the chatbot"""
    try:
        data = request.get_json()
        message = data.get('message')
        temperature = data.get('temperature', 0.7)
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        if conversation_id not in active_conversations:
            return jsonify({"error": "Conversation not found"}), 404
        
        response = chatbot.chat(conversation_id, message, temperature)
        
        if response:
            return jsonify({
                "conversation_id": conversation_id,
                "user_message": message,
                "bot_response": response
            }), 200
        else:
            return jsonify({"error": "Failed to process message"}), 500
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>/history', methods=['GET'])
def get_conversation_history(conversation_id):
    """Get conversation history"""
    try:
        if conversation_id not in active_conversations:
            return jsonify({"error": "Conversation not found"}), 404
        
        history = chatbot.get_conversation_history(conversation_id)
        return jsonify({
            "conversation_id": conversation_id,
            "messages": history
        }), 200
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>/reset', methods=['POST'])
def reset_conversation(conversation_id):
    """Reset a conversation"""
    try:
        if conversation_id not in active_conversations:
            return jsonify({"error": "Conversation not found"}), 404
        
        success = chatbot.reset_conversation(conversation_id)
        
        if success:
            return jsonify({"message": "Conversation reset successfully"}), 200
        else:
            return jsonify({"error": "Failed to reset conversation"}), 500
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/conversations/<conversation_id>/close', methods=['POST'])
def close_conversation(conversation_id):
    """Close a conversation"""
    try:
        if conversation_id in active_conversations:
            del active_conversations[conversation_id]
            return jsonify({"message": "Conversation closed"}), 200
        else:
            return jsonify({"error": "Conversation not found"}), 404
    except Exception as e:
        logger.error(f"Error closing conversation: {e}")
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )
