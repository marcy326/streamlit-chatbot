# database_operations.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=+9), 'JST')

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    caption = Column(Text)
    timestamp = Column(DateTime, default=datetime.now(JST))

engine = create_engine('sqlite:///chat_history.db')
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

def save_message(sender, message, caption):
    """Save a message to the database."""
    session = Session()
    new_message = Message(sender=sender, message=message, caption=caption)
    session.add(new_message)
    session.commit()
    session.close()

def load_messages():
    """Load all messages from the database and return them as a list of dictionaries."""
    session = Session()
    messages = session.query(Message).order_by(Message.timestamp.asc()).all()
    session.close()
    return messages_to_dict_list(messages)

def messages_to_dict_list(messages):
    """Convert a list of Message instances to a list of dictionaries."""
    return [
        {
            "sender": message.sender,
            "message": message.message,
            "timestamp": message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "caption": message.caption,
        }
        for message in messages
    ]