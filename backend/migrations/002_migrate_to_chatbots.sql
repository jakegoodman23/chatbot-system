-- Migration: Convert existing single-chatbot data to multi-chatbot system
-- This migration creates a default chatbot and associates existing data with it

-- Create a default chatbot from existing system prompt (if any)
DO $$
DECLARE
    default_chatbot_id INTEGER;
    existing_prompt TEXT;
    default_prompt TEXT := 'You are a helpful assistant that answers questions based on the provided context. Use the context information to provide accurate and relevant answers. If the context doesn''t contain enough information to answer the question, say so clearly. Always be truthful and don''t make up information.';
BEGIN
    -- Try to get existing system prompt from admin_settings
    SELECT value INTO existing_prompt 
    FROM admin_settings 
    WHERE key = 'system_prompt' 
    LIMIT 1;
    
    -- Use existing prompt if available, otherwise use default
    IF existing_prompt IS NULL OR existing_prompt = '' THEN
        existing_prompt := default_prompt;
    END IF;
    
    -- Create default chatbot
    INSERT INTO chatbots (name, description, system_prompt, is_active, created_at, updated_at)
    VALUES (
        'Default Assistant',
        'The original chatbot assistant with access to all previously uploaded documents.',
        existing_prompt,
        true,
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ) RETURNING id INTO default_chatbot_id;
    
    -- Associate all existing documents with the default chatbot
    INSERT INTO chatbot_documents (chatbot_id, document_id, created_at)
    SELECT default_chatbot_id, id, CURRENT_TIMESTAMP
    FROM documents;
    
    -- Update all existing chat sessions to reference the default chatbot
    UPDATE chat_sessions 
    SET chatbot_id = default_chatbot_id 
    WHERE chatbot_id IS NULL;
    
    -- Log the migration
    RAISE NOTICE 'Migration completed successfully. Created default chatbot with ID: %', default_chatbot_id;
    RAISE NOTICE 'Associated % documents with default chatbot', (SELECT COUNT(*) FROM documents);
    RAISE NOTICE 'Updated % chat sessions to reference default chatbot', (SELECT COUNT(*) FROM chat_sessions WHERE chatbot_id = default_chatbot_id);
    
END $$;