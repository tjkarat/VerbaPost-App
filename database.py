from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
import streamlit as st

Base = declarative_base()

# --- CONNECTION ---
def get_engine():
    try:
        db_url = st.secrets["connections"]["database_url"]
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return create_engine(db_url)
    except:
        return create_engine('sqlite:///verbapost.db')

engine = get_engine()

# --- MODELS ---
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False) # This will be the Email
    email = Column(String, unique=True, nullable=False)
    
    # New Columns for Return Address
    address_name = Column(String, nullable=True)
    address_street = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    address_zip = Column(String, nullable=True)
    
    letters = relationship("Letter", back_populates="author")

class Letter(Base):
    __tablename__ = 'letters'
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    status = Column(String, default="Draft") 
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'))
    author = relationship("User", back_populates="letters")

def init_db():
    Base.metadata.create_all(engine)

# --- HELPER FUNCTIONS ---
def get_user_by_email(email):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    session.close()
    return user

def create_or_get_user(email):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    if not user:
        user = User(username=email, email=email)
        session.add(user)
        session.commit()
        # Refresh to get the ID
        session.refresh(user)
    session.close()
    return user

def update_user_address(email, name, street, city, state, zip_code):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(email=email).first()
    if user:
        user.address_name = name
        user.address_street = street
        user.address_city = city
        user.address_state = state
        user.address_zip = zip_code
        session.commit()
    session.close()

def save_letter_to_history(user_email, text_content):
    Session = sessionmaker(bind=engine)
    session = Session()
    user = session.query(User).filter_by(email=user_email).first()
    if user:
        new_letter = Letter(content=text_content, author=user, status="Paid")
        session.add(new_letter)
        session.commit()
    session.close()

if __name__ == "__main__":
    init_db()