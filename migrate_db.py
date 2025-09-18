#!/usr/bin/env python3
"""
Database Migration Script for Peer-to-Peer Chat
This script handles the migration from old schema to new UUID-based schema
"""

import os
import sqlite3
import shutil
from datetime import datetime

def migrate_database():
    """Migrate database from old schema to new UUID-based schema"""
    
    db_file = 'peer_chat.db'
    backup_file = f'peer_chat_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    if not os.path.exists(db_file):
        print("No existing database found. Migration not needed.")
        return True
    
    try:
        # Create backup
        shutil.copy(db_file, backup_file)
        print(f"Database backed up as: {backup_file}")
        
        # Connect to existing database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if cursor.fetchone():
            # Check if uuid column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'uuid' not in columns:
                print("Old schema detected. Migrating to new UUID-based schema...")
                
                # Drop old tables
                cursor.execute("DROP TABLE IF EXISTS users")
                cursor.execute("DROP TABLE IF EXISTS messages")
                
                conn.commit()
                conn.close()
                
                print("✅ Database migration completed successfully!")
                print("📁 Old database backed up as:", backup_file)
                print("🆕 New database will be created with UUID support")
                return True
            else:
                conn.close()
                print("✅ Database schema is already up to date!")
                return True
        else:
            conn.close()
            print("No users table found. Will create new database.")
            return True
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Starting database migration...")
    success = migrate_database()
    
    if success:
        print("\n🚀 Migration completed! You can now run the application.")
    else:
        print("\n❌ Migration failed. Please check the error messages above.")
