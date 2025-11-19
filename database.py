from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import streamlit as st
import os

Base = declarative_base()

# --- INTELLIGENT CONNECTION ---
def get_engine():
    # 1. Try to get Cloud Secret
    try:
        db_url = st.secrets["connections"]["database_url"]
        
        # Compatibility Fix: SQLAlchemy prefers 'postgresql://' over 'postgres://'
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        print("✅ Connecting to Cloud Database...")
        return create_engine(db_url)
    
    # 2. Fallback to Local File (Safety Net)
    except Exception as e:
        print(f"⚠️ Cloud Connection Failed: {e}")
        print("⚠️ Using Local SQLite instead.")
        return create_engine('sqlite:///verbapost.db')

engine = get_engine()

# --- MODELS (The Data Structure) ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    
    # Relationship: A user can have many letters
    letters = relationship("Letter", back_populates="author")

class Letter(Base):
    __tablename__ = 'letters'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    status = Column(String, default="Draft") # Draft, Paid, Sent
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="letters")

# --- FUNCTIONS ---
def init_db():
    """Creates tables in the cloud if they don't exist"""
    Base.metadata.create_all(engine)

def create_letter(text_content, user_name="Guest"):
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Simple User Logic (We will upgrade this on Day 4)
    user = session.query(User).filter_by(username=user_name).first()
    if not user:
        user = User(username=user_name, email=f"{user_name}@example.com")
        session.add(user)
        session.commit()
    
    new_letter = Letter(content=text_content, author=user)
    session.add(new_letter)
    session.commit()
    session.close()

if __name__ == "__main__":
    init_db()
    print("Database Tables Created Successfully!")