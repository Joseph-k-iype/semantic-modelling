-- database/postgres/schema/09-comments.sql
-- Comments and collaboration tables

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS comment_reactions CASCADE;
DROP TABLE IF EXISTS comment_mentions CASCADE;
DROP TABLE IF EXISTS comments CASCADE;

-- Comments table (threaded comments on any entity)
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type entity_type NOT NULL,
    entity_id UUID NOT NULL,
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT FALSE NOT NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    position JSONB,
    attachments JSONB DEFAULT '[]'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    edited BOOLEAN DEFAULT FALSE NOT NULL,
    deleted_at TIMESTAMP WITH TIME ZONE,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT comments_content_check CHECK (LENGTH(TRIM(content)) >= 1),
    CONSTRAINT comments_resolved_check CHECK (
        (is_resolved = FALSE AND resolved_at IS NULL AND resolved_by IS NULL) OR
        (is_resolved = TRUE AND resolved_at IS NOT NULL)
    )
);

-- Comment mentions table (for @mentions in comments)
CREATE TABLE comment_mentions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    mentioned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_read BOOLEAN DEFAULT FALSE NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Unique constraint: one mention per user per comment
    CONSTRAINT comment_mentions_unique UNIQUE(comment_id, mentioned_user_id)
);

-- Comment reactions table (for emoji reactions)
CREATE TABLE comment_reactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    comment_id UUID NOT NULL REFERENCES comments(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reaction VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT comment_reactions_reaction_check CHECK (LENGTH(reaction) >= 1 AND LENGTH(reaction) <= 50),
    -- Unique constraint: one reaction type per user per comment
    CONSTRAINT comment_reactions_unique UNIQUE(comment_id, user_id, reaction)
);

-- Indexes for comments table
CREATE INDEX idx_comments_entity ON comments(entity_type, entity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_parent_id ON comments(parent_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_is_resolved ON comments(is_resolved) WHERE deleted_at IS NULL;
CREATE INDEX idx_comments_created_by ON comments(created_by);
CREATE INDEX idx_comments_created_at ON comments(created_at DESC);
CREATE INDEX idx_comments_updated_at ON comments(updated_at DESC);
CREATE INDEX idx_comments_deleted_at ON comments(deleted_at) WHERE deleted_at IS NOT NULL;

-- Full-text search index
CREATE INDEX idx_comments_fulltext ON comments 
    USING gin(to_tsvector('english', content)) 
    WHERE deleted_at IS NULL;

-- Indexes for comment_mentions table
CREATE INDEX idx_comment_mentions_comment_id ON comment_mentions(comment_id);
CREATE INDEX idx_comment_mentions_mentioned_user_id ON comment_mentions(mentioned_user_id);
CREATE INDEX idx_comment_mentions_is_read ON comment_mentions(is_read) WHERE is_read = FALSE;

-- Indexes for comment_reactions table
CREATE INDEX idx_comment_reactions_comment_id ON comment_reactions(comment_id);
CREATE INDEX idx_comment_reactions_user_id ON comment_reactions(user_id);
CREATE INDEX idx_comment_reactions_reaction ON comment_reactions(reaction);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_comments_updated_at
    BEFORE UPDATE ON comments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to mark comment as edited
CREATE OR REPLACE FUNCTION mark_comment_edited()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.content IS DISTINCT FROM NEW.content THEN
        NEW.edited = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER comment_mark_edited
    BEFORE UPDATE OF content ON comments
    FOR EACH ROW
    EXECUTE FUNCTION mark_comment_edited();

-- Trigger to extract and create mentions
CREATE OR REPLACE FUNCTION extract_comment_mentions()
RETURNS TRIGGER AS $$
DECLARE
    v_username TEXT;
    v_user_id UUID;
    v_usernames TEXT[];
BEGIN
    -- Extract @mentions from content using regex
    v_usernames := regexp_matches(NEW.content, '@([A-Za-z0-9_-]+)', 'g');
    
    -- Create mention records
    IF v_usernames IS NOT NULL THEN
        FOREACH v_username IN ARRAY v_usernames
        LOOP
            -- Find user by username
            SELECT id INTO v_user_id
            FROM users
            WHERE username = v_username
            AND deleted_at IS NULL;
            
            -- Create mention if user found
            IF v_user_id IS NOT NULL THEN
                INSERT INTO comment_mentions (comment_id, mentioned_user_id)
                VALUES (NEW.id, v_user_id)
                ON CONFLICT (comment_id, mentioned_user_id) DO NOTHING;
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER comment_extract_mentions
    AFTER INSERT OR UPDATE OF content ON comments
    FOR EACH ROW
    EXECUTE FUNCTION extract_comment_mentions();

-- Function to get comment thread
CREATE OR REPLACE FUNCTION get_comment_thread(p_root_comment_id UUID)
RETURNS TABLE (
    comment_id UUID,
    parent_id UUID,
    content TEXT,
    is_resolved BOOLEAN,
    author_id UUID,
    author_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    reply_count BIGINT,
    reaction_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    WITH RECURSIVE thread AS (
        -- Base case: root comment
        SELECT 
            c.id,
            c.parent_id,
            c.content,
            c.is_resolved,
            c.created_by,
            c.created_at,
            c.updated_at
        FROM comments c
        WHERE c.id = p_root_comment_id
        AND c.deleted_at IS NULL
        
        UNION ALL
        
        -- Recursive case: replies
        SELECT 
            c.id,
            c.parent_id,
            c.content,
            c.is_resolved,
            c.created_by,
            c.created_at,
            c.updated_at
        FROM comments c
        INNER JOIN thread t ON c.parent_id = t.id
        WHERE c.deleted_at IS NULL
    )
    SELECT 
        t.id,
        t.parent_id,
        t.content,
        t.is_resolved,
        t.created_by,
        u.full_name,
        t.created_at,
        t.updated_at,
        COUNT(DISTINCT r.id) as reply_count,
        COUNT(DISTINCT cr.id) as reaction_count
    FROM thread t
    JOIN users u ON u.id = t.created_by
    LEFT JOIN comments r ON r.parent_id = t.id AND r.deleted_at IS NULL
    LEFT JOIN comment_reactions cr ON cr.comment_id = t.id
    GROUP BY t.id, t.parent_id, t.content, t.is_resolved, t.created_by, 
             u.full_name, t.created_at, t.updated_at
    ORDER BY t.created_at;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get comments for entity
CREATE OR REPLACE FUNCTION get_entity_comments(
    p_entity_type entity_type,
    p_entity_id UUID,
    p_include_resolved BOOLEAN DEFAULT FALSE
)
RETURNS TABLE (
    comment_id UUID,
    parent_id UUID,
    content TEXT,
    is_resolved BOOLEAN,
    position JSONB,
    author_id UUID,
    author_name VARCHAR(255),
    author_avatar VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    reply_count BIGINT,
    reaction_count BIGINT,
    reactions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        c.id,
        c.parent_id,
        c.content,
        c.is_resolved,
        c.position,
        c.created_by,
        u.full_name,
        u.avatar_url,
        c.created_at,
        c.updated_at,
        COUNT(DISTINCT r.id) as reply_count,
        COUNT(DISTINCT cr.id) as reaction_count,
        COALESCE(
            jsonb_agg(
                DISTINCT jsonb_build_object(
                    'reaction', cr.reaction,
                    'user_id', cr.user_id,
                    'user_name', ru.full_name
                )
            ) FILTER (WHERE cr.id IS NOT NULL),
            '[]'::jsonb
        ) as reactions
    FROM comments c
    JOIN users u ON u.id = c.created_by
    LEFT JOIN comments r ON r.parent_id = c.id AND r.deleted_at IS NULL
    LEFT JOIN comment_reactions cr ON cr.comment_id = c.id
    LEFT JOIN users ru ON ru.id = cr.user_id
    WHERE c.entity_type = p_entity_type
    AND c.entity_id = p_entity_id
    AND c.parent_id IS NULL
    AND c.deleted_at IS NULL
    AND (p_include_resolved = TRUE OR c.is_resolved = FALSE)
    GROUP BY c.id, c.parent_id, c.content, c.is_resolved, c.position,
             c.created_by, u.full_name, u.avatar_url, c.created_at, c.updated_at
    ORDER BY c.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to resolve comment
CREATE OR REPLACE FUNCTION resolve_comment(
    p_comment_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE comments
    SET 
        is_resolved = TRUE,
        resolved_at = NOW(),
        resolved_by = p_user_id,
        updated_by = p_user_id
    WHERE id = p_comment_id
    AND is_resolved = FALSE;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to unresolve comment
CREATE OR REPLACE FUNCTION unresolve_comment(
    p_comment_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE comments
    SET 
        is_resolved = FALSE,
        resolved_at = NULL,
        resolved_by = NULL,
        updated_by = p_user_id
    WHERE id = p_comment_id
    AND is_resolved = TRUE;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to add reaction
CREATE OR REPLACE FUNCTION add_comment_reaction(
    p_comment_id UUID,
    p_user_id UUID,
    p_reaction VARCHAR(50)
)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO comment_reactions (comment_id, user_id, reaction)
    VALUES (p_comment_id, p_user_id, p_reaction)
    ON CONFLICT (comment_id, user_id, reaction) DO NOTHING;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to remove reaction
CREATE OR REPLACE FUNCTION remove_comment_reaction(
    p_comment_id UUID,
    p_user_id UUID,
    p_reaction VARCHAR(50)
)
RETURNS BOOLEAN AS $$
BEGIN
    DELETE FROM comment_reactions
    WHERE comment_id = p_comment_id
    AND user_id = p_user_id
    AND reaction = p_reaction;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to get unread mentions for user
CREATE OR REPLACE FUNCTION get_unread_mentions(p_user_id UUID)
RETURNS TABLE (
    mention_id UUID,
    comment_id UUID,
    comment_content TEXT,
    entity_type entity_type,
    entity_id UUID,
    author_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        cm.id,
        c.id,
        c.content,
        c.entity_type,
        c.entity_id,
        u.full_name,
        cm.created_at
    FROM comment_mentions cm
    JOIN comments c ON c.id = cm.comment_id
    JOIN users u ON u.id = c.created_by
    WHERE cm.mentioned_user_id = p_user_id
    AND cm.is_read = FALSE
    AND c.deleted_at IS NULL
    ORDER BY cm.created_at DESC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to mark mention as read
CREATE OR REPLACE FUNCTION mark_mention_read(p_mention_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE comment_mentions
    SET 
        is_read = TRUE,
        read_at = NOW()
    WHERE id = p_mention_id
    AND is_read = FALSE;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Comments schema created successfully';
END $$;