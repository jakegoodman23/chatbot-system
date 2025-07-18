#!/usr/bin/env python3
"""
Database migration runner for the chatbot application.
This script applies SQL migrations in order.
"""

import os
import sys
import psycopg2
from psycopg2 import sql
import glob
from pathlib import Path

def get_database_url():
    """Get database URL from environment variables."""
    return os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/chatbot_db')

def connect_to_database():
    """Connect to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(get_database_url())
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

def create_migrations_table(conn):
    """Create the migrations tracking table if it doesn't exist."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_migrations (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
    """)
    cursor.close()

def get_applied_migrations(conn):
    """Get list of already applied migrations."""
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM applied_migrations ORDER BY filename;")
    applied = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return applied

def get_migration_files():
    """Get list of migration files in order."""
    migrations_dir = Path(__file__).parent / 'migrations'
    migration_files = glob.glob(str(migrations_dir / '*.sql'))
    return sorted(migration_files)

def apply_migration(conn, migration_file):
    """Apply a single migration file."""
    filename = os.path.basename(migration_file)
    print(f"Applying migration: {filename}")
    
    try:
        cursor = conn.cursor()
        
        # Read and execute the migration
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        cursor.execute(migration_sql)
        
        # Record that this migration was applied
        cursor.execute(
            "INSERT INTO applied_migrations (filename) VALUES (%s);",
            (filename,)
        )
        
        cursor.close()
        print(f"✅ Successfully applied: {filename}")
        
    except Exception as e:
        print(f"❌ Error applying migration {filename}: {e}")
        sys.exit(1)

def main():
    """Main migration runner."""
    print("🚀 Starting database migrations...")
    
    # Connect to database
    conn = connect_to_database()
    print("✅ Connected to database")
    
    # Create migrations table
    create_migrations_table(conn)
    print("✅ Migrations tracking table ready")
    
    # Get migrations
    applied_migrations = get_applied_migrations(conn)
    migration_files = get_migration_files()
    
    if not migration_files:
        print("ℹ️  No migration files found")
        return
    
    print(f"📋 Found {len(migration_files)} migration files")
    print(f"📋 {len(applied_migrations)} migrations already applied")
    
    # Apply pending migrations
    pending_count = 0
    for migration_file in migration_files:
        filename = os.path.basename(migration_file)
        if filename not in applied_migrations:
            apply_migration(conn, migration_file)
            pending_count += 1
    
    if pending_count == 0:
        print("✅ All migrations already applied - database is up to date!")
    else:
        print(f"✅ Applied {pending_count} new migrations successfully!")
    
    conn.close()
    print("🎉 Migration process completed!")

if __name__ == '__main__':
    main()