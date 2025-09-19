#!/usr/bin/env python3
"""
Database Models for Peer-to-Peer Chat Application
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for storing peer information"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True, nullable=False)
    ip_address = Column(String(45), nullable=False)
    username = Column(String(100), nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)
    is_online = Column(Boolean, default=True)
    first_seen = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    """Message model for storing chat history"""
    __tablename__ = 'messages'
    
    id = Column(Integer, primary_key=True)
    sender_uuid = Column(String(36), nullable=False)
    receiver_uuid = Column(String(36), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), default='text')  # text, file, image
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class DatabaseManager:
    """Manages database operations"""
    
    def __init__(self, db_path="peer_chat.db"):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database schema is up to date")
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def handle_migration(self):
        """Handle database schema migrations"""
        try:
            # Check if uuid column exists in users table
            with self.engine.connect() as conn:
                result = conn.execute("PRAGMA table_info(users)")
                columns = [row[1] for row in result]
                
                if 'uuid' not in columns:
                    print("🔄 Migrating database schema...")
                    # Backup existing database
                    import shutil
                    backup_path = f"{self.db_path}.backup"
                    shutil.copy2(self.db_path, backup_path)
                    print(f"📁 Database backed up to {backup_path}")
                    
                    # Drop and recreate tables
                    Base.metadata.drop_all(bind=self.engine)
                    Base.metadata.create_all(bind=self.engine)
                    print("✅ Database migration completed")
                    
        except Exception as e:
            print(f"❌ Migration error: {e}")

