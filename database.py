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
    address_name = Column(String, nullable=True)
    address_street = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_zip = Column(String, nullable=True)
    letters = relationship("Letter", back_populates="author")

class Letter(Base):
    __tablename__ = 'letters'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=True)
    status = Column(String, default="Draft") # Draft, Paid, Sent
    created_at = Column(DateTime, default=datetime.utcnow)
    
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

def get_user_by_email(email):
    session = get_session()
    user = session.query(User).filter_by(email=email).first()
    session.close()
    return user

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
    try:
        user = session.query(User).filter_by(email=email).first()
        if user:
            user.address_name = name
            user.address_street = street
            user.address_city = city
            user.address_state = state
            user.address_zip = zip_code
            session.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        session.close()

def save_draft(email, r_name, r_street, r_city, r_state, r_zip):
    session = get_session()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(username=email, email=email)
            session.add(user)
            session.commit()
            
        draft = Letter(
            author=user,
            status="Pending Payment",
            recipient_name=r_name,
            recipient_street=r_street,
            recipient_city=r_city,
            recipient_state=r_state,
            recipient_zip=r_zip,
            content=""
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
        return draft.id
    except Exception as e:
        print(f"Draft Error: {e}")
        return None
    finally:
        session.close()

def get_letter(letter_id):
    session = get_session()
    letter = session.query(Letter).filter_by(id=letter_id).first()
    session.close()
    return letter

# --- ADMIN FUNCTIONS (NEW) ---
def get_pending_heirloom_letters():
    session = get_session()
    # We assume status='Heirloom_Paid' or just filter by logic in the view
    # For MVP, let's grab ALL letters that aren't 'Draft' or 'Sent'
    # Ideally, we'd have a specific status. Let's grab last 50 for now.
    letters = session.query(Letter).order_by(Letter.created_at.desc()).limit(50).all()
    session.close()
    return letters

def mark_as_sent(letter_id):
    session = get_session()
    letter = session.query(Letter).filter_by(id=letter_id).first()
    if letter:
        letter.status = "Sent"
        session.commit()
    session.close()

if __name__ == "__main__":
    init_db()