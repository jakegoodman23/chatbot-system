-- Migration: Add message feedback table
-- This migration adds the ability to store thumbs up/down feedback for chat messages

CREATE TABLE IF NOT EXISTS message_feedback (
    id SERIAL PRIMARY KEY,
    message_id INTEGER NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    feedback_type VARCHAR(20) NOT NULL CHECK (feedback_type IN ('thumbs_up', 'thumbs_down')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(message_id) -- Only one feedback per message
);

-- Create trigger for updated_at
CREATE TRIGGER update_message_feedback_updated_at 
    BEFORE UPDATE ON message_feedback 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_message_feedback_message_id ON message_feedback(message_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_type ON message_feedback(feedback_type);