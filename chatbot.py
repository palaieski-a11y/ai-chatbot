import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from config import Config
from database import get_session, Message, Conversation, User, init_db

logger = logging.getLogger(__name__)

class ChatBot:
    """Main chatbot class for handling conversations"""
    
    def __init__(self):
        """Initialize the chatbot with OpenAI client and database"""
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_MODEL
        self.engine = init_db()
        self.max_history = Config.MAX_CONVERSATION_HISTORY
        
        # System prompt that defines chatbot behavior
        self.system_prompt = """You are a helpful, friendly, and intelligent AI assistant. 
You should:
- Provide accurate and helpful information
- Ask clarifying questions when needed
- Be concise but thorough
- Maintain context from previous messages
- Be respectful and professional
- Admit when you don't know something"""
    
    def create_user(self, user_id: str, username: str, email: Optional[str] = None) -> bool:
        """Create a new user"""
        try:
            session = get_session(self.engine)
            user = User(id=user_id, username=username, email=email)
            session.add(user)
            session.commit()
            session.close()
            logger.info(f"User created: {username}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
    
    def create_conversation(self, user_id: str, title: Optional[str] = None) -> str:
        """Create a new conversation"""
        try:
            session = get_session(self.engine)
            conversation_id = str(uuid.uuid4())
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=title or "New Conversation"
            )
            session.add(conversation)
            session.commit()
            session.close()
            logger.info(f"Conversation created: {conversation_id}")
            return conversation_id
        except Exception as e:
            logger.error(f"Error creating conversation: {e}")
            return None
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Retrieve conversation history from database"""
        try:
            session = get_session(self.engine)
            messages = session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).order_by(Message.created_at).all()
            session.close()
            
            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages[-self.max_history:]
            ]
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def save_message(self, conversation_id: str, role: str, content: str, tokens_used: int = 0) -> bool:
        """Save message to database"""
        try:
            session = get_session(self.engine)
            message = Message(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role=role,
                content=content,
                tokens_used=tokens_used
            )
            session.add(message)
            session.commit()
            session.close()
            return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    def chat(self, conversation_id: str, user_message: str, temperature: float = 0.7) -> Optional[str]:
        """Send a message and get a response from the chatbot"""
        try:
            # Save user message
            self.save_message(conversation_id, "user", user_message)
            
            # Get conversation history
            history = self.get_conversation_history(conversation_id)
            
            # Prepare messages for API
            messages = [
                {"role": "system", "content": self.system_prompt},
                *history,
                {"role": "user", "content": user_message}
            ]
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            
            # Extract response
            assistant_message = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            
            # Save assistant response
            self.save_message(conversation_id, "assistant", assistant_message, tokens_used)
            
            logger.info(f"Message processed. Tokens used: {tokens_used}")
            return assistant_message
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return None
    
    def reset_conversation(self, conversation_id: str) -> bool:
        """Reset/clear a conversation"""
        try:
            session = get_session(self.engine)
            session.query(Message).filter(
                Message.conversation_id == conversation_id
            ).delete()
            session.commit()
            session.close()
            logger.info(f"Conversation reset: {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting conversation: {e}")
            return False
