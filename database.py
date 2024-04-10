# database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=+9), 'JST')
def current_time_jst():
    return datetime.now(JST)

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(String, index=True)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    caption = Column(Text)
    timestamp = Column(DateTime, default=current_time_jst)
    summary = Column(Text, nullable=True)

engine = create_engine('sqlite:///chat_history.db')
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

def save_conversation(conversation_id, messages):
    """特定の会話IDに属するメッセージリストをデータベースに保存する関数"""
    session = Session()
    for message in messages:
        new_message = Message(conversation_id=conversation_id, **message)
        session.add(new_message)
    session.commit()
    session.close()

def get_conversations():
    session = Session()
    conversations = session.query(
        Message.conversation_id,
        func.max(Message.timestamp).label("latest_timestamp")
    ).group_by(Message.conversation_id).order_by(func.max(Message.timestamp).desc()).all()
    session.close()
    return [(c.conversation_id, c.latest_timestamp) for c in conversations]

def save_message(sender, message, caption, conversation_id):
    """Save a message to the database."""
    session = Session()
    new_message = Message(sender=sender, message=message, caption=caption, conversation_id=conversation_id)
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

def load_messages_by_conversation_id(conversation_id):
    """指定された会話IDに基づいてメッセージをロードする"""
    session = Session()
    messages = session.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp.asc()).all()
    session.close()
    return messages_to_dict_list(messages)

def save_summary(summary, conversation_id):
    """指定された会話IDの会話に要約を保存する"""
    session = Session()
    # 会話の最初のメッセージを取得して要約を更新する例
    message = session.query(Message).filter(Message.conversation_id == conversation_id).first()
    if message:
        message.summary = summary
        session.commit()
    session.close()

def get_summary(conversation_id):
    """指定された会話IDの会話の要約を取得する"""
    session = Session()
    message = session.query(Message).filter(Message.conversation_id == conversation_id).first()
    session.close()
    if message and message.summary:
        return message.summary
    return None
