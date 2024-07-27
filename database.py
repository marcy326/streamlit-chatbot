# database.py
import bcrypt
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
    user_id = Column(String, index=True)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    caption = Column(Text)
    timestamp = Column(DateTime, default=current_time_jst)
    summary = Column(Text, nullable=True)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

engine = create_engine('sqlite:///chat_history.db')
Session = sessionmaker(bind=engine)

Base.metadata.create_all(engine)

def hash_password(password):
    """パスワードをハッシュ化する"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, plain_password):
    """ハッシュ化されたパスワードと平文のパスワードを比較する"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

def save_user(username, password):
    session = Session()
    hashed_password = hash_password(password)
    new_user = User(username=username, password=hashed_password)
    session.add(new_user)
    session.commit()
    session.close()

def get_user(username):
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def get_user_id(username):
    """指定されたユーザー名に基づいてユーザーIDを取得する"""
    session = Session()
    user = session.query(User).filter(User.username == username).first()
    session.close()
    if user:
        return user.id
    return None

def authenticate_user(username, password):
    user = get_user(username)
    if user and check_password(user.password, password):
        return True
    return False

def save_conversation(conversation_id, messages):
    """特定の会話IDに属するメッセージリストをデータベースに保存する関数"""
    session = Session()
    for message in messages:
        new_message = Message(conversation_id=conversation_id, **message)
        session.add(new_message)
    session.commit()
    session.close()

def get_conversations(user_id):
    session = Session()
    conversations = session.query(
        Message.conversation_id,
        func.max(Message.timestamp).label("latest_timestamp")
    ).filter(
        Message.user_id == user_id,
    ).group_by(Message.conversation_id).order_by(func.max(Message.timestamp).desc()).all()
    session.close()
    return [(c.conversation_id, c.latest_timestamp) for c in conversations]

def save_message(sender, message, caption, conversation_id, user_id):
    """Save a message to the database."""
    session = Session()
    new_message = Message(sender=sender, message=message, caption=caption, conversation_id=conversation_id, user_id=user_id)
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

def delete_conversation(conversation_id):
    """指定された会話IDの会話を削除する。"""
    session = Session()
    messages_to_delete = session.query(Message).filter(Message.conversation_id == conversation_id).all()
    for message in messages_to_delete:
        session.delete(message)
    session.commit()
    session.close()
