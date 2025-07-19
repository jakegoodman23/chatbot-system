-- Migration: Add suggested questions table
-- This migration adds the ability to store pre-loaded questions for each chatbot

CREATE TABLE IF NOT EXISTS suggested_questions (
    id SERIAL PRIMARY KEY,
    chatbot_id INTEGER NOT NULL REFERENCES chatbots(id) ON DELETE CASCADE,
    question_text TEXT NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trigger for updated_at
CREATE TRIGGER update_suggested_questions_updated_at 
    BEFORE UPDATE ON suggested_questions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_suggested_questions_chatbot_id ON suggested_questions(chatbot_id);
CREATE INDEX IF NOT EXISTS idx_suggested_questions_active ON suggested_questions(is_active);
CREATE INDEX IF NOT EXISTS idx_suggested_questions_order ON suggested_questions(chatbot_id, display_order, is_active);

-- Insert some default suggested questions for existing chatbots
INSERT INTO suggested_questions (chatbot_id, question_text, display_order, is_active)
SELECT 
    id as chatbot_id,
    unnest(ARRAY[
        'What can you help me with?',
        'How do I get started?',
        'Can you explain the main features?',
        'What kind of questions can I ask?'
    ]) as question_text,
    unnest(ARRAY[1, 2, 3, 4]) as display_order,
    true as is_active
FROM chatbots 
WHERE is_active = true;