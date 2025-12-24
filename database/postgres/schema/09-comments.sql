-- Comments table for collaboration
CREATE TABLE IF NOT EXISTS comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Comment target (can be model, diagram, or specific element)
    model_id UUID REFERENCES models(id) ON DELETE CASCADE,
    diagram_id UUID REFERENCES diagrams(id) ON DELETE CASCADE,
    element_id VARCHAR(255), -- Concept/relationship ID in graph
    
    -- Thread support
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    thread_id UUID, -- Root comment in thread
    
    -- Comment content
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text', -- text, markdown
    
    -- Author
    author_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Status
    is_resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    edited BOOLEAN DEFAULT FALSE,
    deleted BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT valid_content_type CHECK (content_type IN ('text', 'markdown'))
);

-- Comment mentions for @user notifications
CREATE TABLE IF NOT EXISTS comment_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    mentioned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_mention UNIQUE (comment_id, mentioned_user_id)
);

-- Comment reactions (like, helpful, etc.)
CREATE TABLE IF NOT EXISTS comment_reactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reaction VARCHAR(20) NOT NULL, -- like, helpful, confused
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_reaction UNIQUE (comment_id, user_id, reaction),
    CONSTRAINT valid_reaction CHECK (reaction IN ('like', 'helpful', 'confused', 'resolved'))
);

-- Comment attachments
CREATE TABLE IF NOT EXISTS comment_attachments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    file_url VARCHAR(500) NOT NULL,
    file_size INT,
    mime_type VARCHAR(100),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Indexes
CREATE INDEX idx_comments_model_id ON comments(model_id);
CREATE INDEX idx_comments_diagram_id ON comments(diagram_id);
CREATE INDEX idx_comments_element_id ON comments(element_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_thread_id ON comments(thread_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);
CREATE INDEX idx_comments_is_resolved ON comments(is_resolved);
CREATE INDEX idx_comments_deleted ON comments(deleted) WHERE deleted = false;

CREATE INDEX idx_comment_mentions_user_id ON comment_mentions(mentioned_user_id);
CREATE INDEX idx_comment_mentions_is_read ON comment_mentions(is_read);

CREATE INDEX idx_comment_reactions_comment_id ON comment_reactions(comment_id);
CREATE INDEX idx_comment_reactions_user_id ON comment_reactions(user_id);

CREATE INDEX idx_comment_attachments_comment_id ON comment_attachments(comment_id);

-- Trigger
CREATE TRIGGER update_comments_updated_at
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Function to set thread_id for nested comments
CREATE OR REPLACE FUNCTION set_comment_thread_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.parent_id IS NULL THEN
        NEW.thread_id := NEW.id;
    ELSE
        SELECT COALESCE(thread_id, id)
        INTO NEW.thread_id
        FROM comments
        WHERE id = NEW.parent_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_thread_id
    BEFORE INSERT ON comments
    FOR EACH ROW
    EXECUTE FUNCTION set_comment_thread_id();

-- Function to mark comment as edited
CREATE OR REPLACE FUNCTION mark_comment_edited()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.content != NEW.content THEN
        NEW.edited := TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER mark_edited
    BEFORE UPDATE OF content ON comments
    FOR EACH ROW
    EXECUTE FUNCTION mark_comment_edited();

-- Function to extract mentions from comment content
CREATE OR REPLACE FUNCTION extract_mentions()
RETURNS TRIGGER AS $$
DECLARE
    mention_pattern TEXT := '@\[([^\]]+)\]\(([a-f0-9-]+)\)';
    mention RECORD;
BEGIN
    -- Extract all @mentions from content
    FOR mention IN
        SELECT 
            (regexp_matches(NEW.content, mention_pattern, 'g'))[2]::UUID as user_id
    LOOP
        INSERT INTO comment_mentions (comment_id, mentioned_user_id)
        VALUES (NEW.id, mention.user_id)
        ON CONFLICT (comment_id, mentioned_user_id) DO NOTHING;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER extract_user_mentions
    AFTER INSERT OR UPDATE OF content ON comments
    FOR EACH ROW
    EXECUTE FUNCTION extract_mentions();

-- View for comment threads with user details
CREATE OR REPLACE VIEW comment_threads AS
SELECT 
    c.id,
    c.model_id,
    c.diagram_id,
    c.element_id,
    c.parent_id,
    c.thread_id,
    c.content,
    c.created_at,
    c.updated_at,
    c.is_resolved,
    c.edited,
    c.deleted,
    u.full_name as author_name,
    u.email as author_email,
    u.avatar_url as author_avatar,
    (
        SELECT COUNT(*)
        FROM comments replies
        WHERE replies.parent_id = c.id
        AND replies.deleted = false
    ) as reply_count,
    (
        SELECT COUNT(*)
        FROM comment_reactions
        WHERE comment_id = c.id
    ) as reaction_count
FROM comments c
LEFT JOIN users u ON c.author_id = u.id
WHERE c.deleted = false
ORDER BY c.created_at DESC;

COMMENT ON TABLE comments IS 'Threaded comments for collaboration on models and diagrams';
COMMENT ON TABLE comment_mentions IS 'User mentions in comments for notifications';
COMMENT ON TABLE comment_reactions IS 'Emoji reactions to comments';
COMMENT ON COLUMN comments.thread_id IS 'Root comment ID for grouping related comments';