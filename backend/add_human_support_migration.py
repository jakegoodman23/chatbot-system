#!/usr/bin/env python3
"""
Migration script to add human support functionality
This script adds the admin_email field to chatbots table and creates the human support tables
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_url():
    """Get database URL from environment or use default"""
    return os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/chatbot_db")

def run_migration():
    """Run the migration to add human support functionality"""
    
    engine = create_engine(get_database_url())
    
    # SQL statements for migration
    migration_sql = [
        # Add admin_email column to chatbots table
        """
        ALTER TABLE chatbots 
        ADD COLUMN IF NOT EXISTS admin_email VARCHAR(255);
        """,
        
        # Update existing chatbots with a default email (you should update these manually)
        """
        UPDATE chatbots 
        SET admin_email = 'admin@example.com' 
        WHERE admin_email IS NULL;
        """,
        
        # Make admin_email NOT NULL after setting defaults
        """
        ALTER TABLE chatbots 
        ALTER COLUMN admin_email SET NOT NULL;
        """,
        
        # Create human_support_requests table
        """
        CREATE TABLE IF NOT EXISTS human_support_requests (
            id SERIAL PRIMARY KEY,
            request_id VARCHAR(255) UNIQUE NOT NULL,
            chatbot_id INTEGER NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
            session_id VARCHAR(255) NOT NULL REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
            user_name VARCHAR(255),
            user_email VARCHAR(255),
            initial_message TEXT NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            admin_joined_at TIMESTAMP,
            resolved_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create index on request_id for faster lookups
        """
        CREATE INDEX IF NOT EXISTS idx_human_support_requests_request_id 
        ON human_support_requests(request_id);
        """,
        
        # Create index on status for filtering
        """
        CREATE INDEX IF NOT EXISTS idx_human_support_requests_status 
        ON human_support_requests(status);
        """,
        
        # Create index on chatbot_id for filtering by chatbot
        """
        CREATE INDEX IF NOT EXISTS idx_human_support_requests_chatbot_id 
        ON human_support_requests(chatbot_id);
        """,
        
        # Create human_support_messages table
        """
        CREATE TABLE IF NOT EXISTS human_support_messages (
            id SERIAL PRIMARY KEY,
            support_request_id INTEGER NOT NULL REFERENCES human_support_requests(id) ON DELETE CASCADE,
            sender_type VARCHAR(50) NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """,
        
        # Create index on support_request_id for faster message retrieval
        """
        CREATE INDEX IF NOT EXISTS idx_human_support_messages_request_id 
        ON human_support_messages(support_request_id);
        """,
        
        # Create index on created_at for ordering messages
        """
        CREATE INDEX IF NOT EXISTS idx_human_support_messages_created_at 
        ON human_support_messages(created_at);
        """,
        
        # Create trigger to update updated_at timestamp
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """,
        
        # Apply trigger to human_support_requests table
        """
        DROP TRIGGER IF EXISTS update_human_support_requests_updated_at ON human_support_requests;
        CREATE TRIGGER update_human_support_requests_updated_at
            BEFORE UPDATE ON human_support_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """
    ]
    
    try:
        with engine.connect() as connection:
            print("Starting human support migration...")
            
            for i, sql in enumerate(migration_sql, 1):
                print(f"Executing migration step {i}/{len(migration_sql)}...")
                try:
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"✓ Step {i} completed successfully")
                except Exception as e:
                    print(f"✗ Step {i} failed: {e}")
                    # Continue with other steps
                    
            print("\n✅ Human support migration completed!")
            print("\nIMPORTANT: Please update the admin_email for your existing chatbots:")
            print("You can do this through the admin interface or by running:")
            print("UPDATE chatbots SET admin_email = 'your-email@domain.com' WHERE id = <chatbot_id>;")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False
        
    return True

def rollback_migration():
    """Rollback the migration (for development purposes)"""
    
    engine = create_engine(get_database_url())
    
    rollback_sql = [
        "DROP TABLE IF EXISTS human_support_messages CASCADE;",
        "DROP TABLE IF EXISTS human_support_requests CASCADE;",
        "ALTER TABLE chatbots DROP COLUMN IF EXISTS admin_email;",
        "DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;"
    ]
    
    try:
        with engine.connect() as connection:
            print("Rolling back human support migration...")
            
            for i, sql in enumerate(rollback_sql, 1):
                print(f"Executing rollback step {i}/{len(rollback_sql)}...")
                try:
                    connection.execute(text(sql))
                    connection.commit()
                    print(f"✓ Rollback step {i} completed")
                except Exception as e:
                    print(f"✗ Rollback step {i} failed: {e}")
                    
            print("✅ Rollback completed!")
            
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_migration()
    else:
        run_migration()