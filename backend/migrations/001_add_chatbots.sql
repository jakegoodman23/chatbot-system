-- Migration: Add Chatbot support
-- This migration adds support for multiple chatbots with separate document bases and system prompts

-- Create the chatbots table
CREATE TABLE IF NOT EXISTS chatbots (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    system_prompt TEXT NOT NULL,
    settings JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_chatbots_updated_at BEFORE UPDATE ON chatbots FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create many-to-many relationship between chatbots and documents
CREATE TABLE IF NOT EXISTS chatbot_documents (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(chatbot_id, document_id)
);

-- Add chatbot_id to chat_sessions to link sessions to specific chatbots
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS chatbot_id INTEGER REFERENCES chatbots(id) ON DELETE CASCADE;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_chatbot_documents_chatbot_id ON chatbot_documents(chatbot_id);
CREATE INDEX IF NOT EXISTS idx_chatbot_documents_document_id ON chatbot_documents(document_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_chatbot_id ON chat_sessions(chatbot_id);
CREATE INDEX IF NOT EXISTS idx_chatbots_active ON chatbots(is_active);