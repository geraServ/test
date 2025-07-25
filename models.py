from sqlalchemy import Column, String
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)  # Telegram user ID
    wallet_address = Column(String, nullable=True)    # TON wallet address