from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import streamlit as st
from sqlalchemy.engine import Engine

Base = declarative_base()

def get_engine() -> Engine:
    try:
        db_url = st.secrets["connections"]["database_url"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return create_engine(db_url)
    except:
        return create_engine('sqlite:///verbapost.db')

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    # Default Return Address
    address_name = Column(String, nullable=True)
    address_street = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_zip = Column(String, nullable=True)
    letters = relationship("Letter", back_populates="author")

class Letter(Base):
    __tablename__ = 'letters'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=True) # Allow empty content for Drafts
    status = Column(String, default="Draft") 
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Recipient Info (The Memory)
    recipient_name = Column(String, nullable=True)
    recipient_street = Column(String, nullable=True)
    recipient_city = Column(String, nullable=True)
    recipient_state = Column(String, nullable=True)
    recipient_zip = Column(String, nullable=True)
    
    user_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="letters")

def init_db():
    Base.metadata.create_all(get_engine())

def get_session():
    return sessionmaker(bind=get_engine())()

def create_or_get_user(email):
    session = get_session()
    user = session.query(User).filter_by(email=email).first()
    if not user:
        user = User(username=email, email=email)
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return user

def update_user_address(email, name, street, city, state, zip_code):
    session = get_session()
    user = session.query(User).filter_by(email=email).first()
    if user:
        user.address_name = name
        user.address_street = street
        user.address_city = city
        user.address_state = state
        user.address_zip = zip_code
        session.commit()
    session.close()

# --- NEW FUNCTION: SAVE DRAFT ---
def save_draft(email, r_name, r_street, r_city, r_state, r_zip):
    session = get_session()
    user = session.query(User).filter_by(email=email).first()
    if user:
        draft = Letter(
            author=user,
            status="Pending Payment",
            recipient_name=r_name,
            recipient_street=r_street,
            recipient_city=r_city,
            recipient_state=r_state,
            recipient_zip=r_zip,
            content="" # Empty until recorded
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        draft_id = draft.id
        session.close()
        return draft_id
    session.close()
    return None

def get_letter(letter_id):
    session = get_session()
    letter = session.query(Letter).filter_by(id=letter_id).first()
    session.close()
    return letter

if __name__ == "__main__":
    init_db()